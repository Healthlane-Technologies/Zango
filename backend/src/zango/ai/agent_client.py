"""
AgentClient wraps an AppLLMAgent with execution logic:
- Resolves prompts with variables
- Calls the underlying ProviderClient
- Executes tool calls in an agentic loop
- Tracks agent-level usage
"""

import json
import logging
import uuid

from typing import Optional

from zango.ai.exceptions import AgentDisabled
from zango.ai.providers.base import LLMMessage, LLMResponse


logger = logging.getLogger("zango.ai")

# Default safety limit for tool execution rounds
DEFAULT_MAX_TOOL_ROUNDS = 10


class AgentClient:
    """
    Developer-facing agent interface. Obtained via get_agent("name").

    Usage:
        agent = get_agent("assessment-question-generator")
        response = agent.run(
            variables={"question_count": 10, "employee_role": "nurse"},
        )
        print(response.content)
    """

    def __init__(self, agent):
        """
        Args:
            agent: AppLLMAgent model instance
        """
        self._agent = agent

    def _resolve_tools(self):
        """Resolve agent's tool names to LLMToolDef objects from the DB."""
        if not self._agent.tools:
            return None

        from zango.ai.providers.base import LLMToolDef
        from zango.apps.ai.models.tool import AppLLMTool

        tool_records = AppLLMTool.objects.filter(
            name__in=self._agent.tools, is_active=True
        )
        llm_tools = [
            LLMToolDef(
                name=t.name,
                description=t.description,
                input_schema=t.parameters_schema,
            )
            for t in tool_records
        ]
        return llm_tools if llm_tools else None

    def _is_openai_style_provider(self):
        """Check if the provider uses OpenAI-style message format."""
        return self._agent.provider.provider_slug in ("openai", "azure_openai")

    def _build_tool_round_messages(self, response, tool_results):
        """
        Build conversation messages for the assistant's tool calls and their results.
        Format depends on the provider type (Anthropic vs OpenAI-style).

        Args:
            response: LLMResponse from the LLM (contains tool_calls)
            tool_results: list of (LLMToolCall, ToolResult) tuples

        Returns:
            list of LLMMessage objects to append to the conversation
        """
        new_messages = []

        if self._is_openai_style_provider():
            # OpenAI format: assistant message with tool_calls, then one tool message per result
            new_messages.append(
                LLMMessage(
                    role="assistant",
                    content=response.content or None,
                    tool_calls=[
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.input),
                            },
                        }
                        for tc in response.tool_calls
                    ],
                )
            )
            for tc, result in tool_results:
                if result.status == "success":
                    content = (
                        json.dumps(result.output)
                        if not isinstance(result.output, str)
                        else result.output
                    )
                else:
                    content = f"Error: {result.error_message}"
                new_messages.append(
                    LLMMessage(
                        role="tool",
                        content=content,
                        tool_call_id=tc.id,
                    )
                )
        else:
            # Anthropic format: assistant content blocks, then user message with tool_result blocks
            assistant_content = []
            if response.content:
                assistant_content.append({"type": "text", "text": response.content})
            for tc in response.tool_calls:
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.input,
                    }
                )
            new_messages.append(LLMMessage(role="assistant", content=assistant_content))

            tool_result_blocks = []
            for tc, result in tool_results:
                if result.status == "success":
                    content = (
                        json.dumps(result.output)
                        if not isinstance(result.output, str)
                        else result.output
                    )
                else:
                    content = f"Error: {result.error_message}"
                tool_result_blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": content,
                        "is_error": result.status != "success",
                    }
                )
            new_messages.append(LLMMessage(role="user", content=tool_result_blocks))

        return new_messages

    def _log_tool_call(self, tool_call, result, invocation_id, round_number):
        """Log a tool execution to the AppLLMToolCall table."""
        from zango.apps.ai.models.tool import AppLLMTool, AppLLMToolCall

        try:
            tool_record = AppLLMTool.objects.filter(
                name=tool_call.name, is_active=True
            ).first()

            AppLLMToolCall.objects.create(
                invocation_id=invocation_id,
                tool=tool_record,
                tool_name=tool_call.name,
                tool_input=tool_call.input,
                tool_output=result.output,
                round_number=round_number,
                execution_time_ms=result.execution_time_ms,
                status=result.status,
                error_message=result.error_message,
                error_traceback=result.error_traceback,
            )

            # Update tool-level stats atomically to avoid race conditions
            if tool_record:
                from django.db.models import F
                from django.utils import timezone

                update = {
                    "total_calls": F("total_calls") + 1,
                    "last_called_at": timezone.now(),
                }
                if result.status == "error":
                    update["total_errors"] = F("total_errors") + 1
                elif result.status == "timeout":
                    update["total_timeouts"] = F("total_timeouts") + 1
                AppLLMTool.objects.filter(pk=tool_record.pk).update(**update)
        except Exception as e:
            logger.error(f"Failed to log tool call '{tool_call.name}': {e}")

    def run(
        self,
        input: Optional[str] = None,
        variables: Optional[dict] = None,
        messages: Optional[list[LLMMessage]] = None,
        files: Optional[list] = None,
        triggered_by: str = "user",
        max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
        session_id: Optional[str] = None,
        user_ref: str = "",
        **kwargs,
    ) -> LLMResponse:
        """
        Execute the agent with an agentic tool loop.

        Input priority (first non-None wins):
          1. messages — full LLMMessage list, caller owns everything
          2. input    — plain string, simplest case
          3. variables — rendered against the agent's user_prompt template

        Args:
            input: Plain string user message. Simplest way to call the agent.
            variables: Dict of template variables rendered into the agent's
                user_prompt. Used when the agent has a prompt template configured.
            messages: Full list of LLMMessage objects. Low-level escape hatch
                for multi-turn history or tool-result injection.
            files: File/image attachments (LLMFile instances).
            triggered_by: Audit label — "user" | "celery" | "cron" | "system".
            session_id: Memory session key. Auto-generated if memory_enabled and
                not supplied; returned on response.session_id.
            user_ref: Opaque string stored on the session for audit (e.g. user PK).
        """
        from zango.ai.client import ProviderClient
        from zango.ai.tools.executor import ToolExecutor

        if not self._agent.is_enabled:
            raise AgentDisabled(self._agent.name)

        if not self._agent.provider:
            raise ValueError(f"Agent '{self._agent.name}' has no provider configured.")

        # Render system prompt
        system = None
        if self._agent.system_prompt:
            system = self._agent.get_system_prompt_content(**(variables or {}))

        # Build messages — priority: explicit messages > input string > user_prompt template
        if messages is None:
            messages = []

            if input is not None:
                # Plain string — simplest case
                messages.append(
                    LLMMessage(role="user", content=input, files=files or None)
                )
            else:
                user_content = self._agent.get_user_prompt_content(**(variables or {}))
                if user_content:
                    messages.append(
                        LLMMessage(
                            role="user", content=user_content, files=files or None
                        )
                    )
                elif files:
                    # No text but files provided
                    messages.append(LLMMessage(role="user", content="", files=files))
        elif files:
            # Caller provided explicit messages — attach files to the last user message
            for msg in reversed(messages):
                if msg.role == "user":
                    msg.files = (msg.files or []) + list(files)
                    break
            else:
                messages.append(LLMMessage(role="user", content="", files=files))

        if not messages:
            raise ValueError(
                f"Agent '{self._agent.name}' has no input: provide input=, variables=, or messages=."
            )

        # ── Memory: auto-generate session_id if memory is on and none supplied ─
        if self._agent.memory_enabled and not session_id:
            session_id = str(uuid.uuid4())

        # ── Memory: prepend prior session messages ────────────────────────────
        history_messages = []
        if session_id and self._agent.memory_enabled:
            history_messages = self._load_session_messages(session_id)
            if history_messages:
                messages = history_messages + messages

        # Build agent tracking metadata for invocation logging
        agent_tracking = {
            "agent": self._agent,
            "agent_name": self._agent.name,
            "rendered_system_prompt": system,
            "context_snapshot": variables,
            "session_id": session_id,
        }
        if self._agent.system_prompt and self._agent.system_prompt.active_version:
            agent_tracking["system_prompt_name"] = self._agent.system_prompt.name
            agent_tracking["system_prompt_version"] = (
                self._agent.system_prompt.active_version.version_number
            )
        if self._agent.user_prompt and self._agent.user_prompt.active_version:
            agent_tracking["user_prompt_name"] = self._agent.user_prompt.name
            agent_tracking["user_prompt_version"] = (
                self._agent.user_prompt.active_version.version_number
            )

        # Resolve agent tools to LLMToolDef objects for the LLM
        llm_tools = self._resolve_tools()

        # Resolve response_format from agent config
        response_format_kwarg = {}
        if self._agent.output_schema == "JSON":
            if self._agent.output_json_schema:
                response_format_kwarg["response_format"] = (
                    self._agent.output_json_schema
                )
            else:
                response_format_kwarg["response_format"] = "json"

        # Generate a single run_id to group all rounds of this agent.run()
        run_id = uuid.uuid4()

        # Execute via ProviderClient with agentic tool loop
        provider_client = ProviderClient(self._agent.provider)
        raw_provider = provider_client._get_client()
        executor = ToolExecutor()
        total_cost = 0.0

        # Pre-upload files once before the loop, then bake the file blocks
        # permanently into the message content so they survive across all rounds.
        #
        # - OpenAI: uploads file → gets file_id → bakes a lightweight image_url
        #   block (file_id reference) into content. No raw bytes in history.
        # - Anthropic/others: no upload API → bakes raw base64 blocks into
        #   content. Bytes are re-sent every round (unavoidable without Files API).
        #
        # Either way, after this step `msg.files` is cleared and the file
        # representation lives in `msg.content` as a permanent content block.
        if files:
            files = raw_provider.prepare_files(files)
            is_openai_style = self._is_openai_style_provider()
            for msg in messages:
                if msg.role == "user" and msg.files:
                    # Build provider-specific file blocks
                    if is_openai_style:
                        file_blocks = [f.to_openai_block() for f in files]
                    else:
                        file_blocks = [f.to_anthropic_block() for f in files]
                    # Prepend file blocks into content permanently
                    existing = msg.content
                    if isinstance(existing, list):
                        msg.content = file_blocks + existing
                    elif isinstance(existing, str) and existing:
                        msg.content = file_blocks + [{"type": "text", "text": existing}]
                    else:
                        msg.content = file_blocks
                    # Clear files — content now owns the file representation
                    msg.files = None
                    break

        # Capture the new-turn slice (excludes history) for memory persistence
        new_user_messages_for_memory = messages[len(history_messages) :]

        for round_number in range(1, max_tool_rounds + 2):
            # OpenAI-style providers cannot use response_format and tools together —
            # passing both causes the model to loop on tool_use instead of finalising.
            # Only enforce response_format on round 1 (before any tools have been
            # called) or on subsequent rounds where no tools are being sent.
            suppress_response_format = (
                round_number > 1 and llm_tools and response_format_kwarg
            )
            response = provider_client.complete(
                messages=messages,
                model=self._agent.model,
                tools=llm_tools,
                temperature=self._agent.temperature,
                max_tokens=self._agent.max_tokens,
                system=system,
                triggered_by=triggered_by,
                run_id=run_id,
                round_number=round_number,
                **{**agent_tracking},
                **(response_format_kwarg if not suppress_response_format else {}),
                **kwargs,
            )
            total_cost += response.cost_usd

            # If the LLM is done (no tool calls), break
            if response.stop_reason != "tool_use" or not response.tool_calls:
                break

            # Safety: don't exceed max rounds
            if round_number > max_tool_rounds:
                logger.warning(
                    f"Agent '{self._agent.name}' hit max tool rounds ({max_tool_rounds}). "
                    f"Returning last response."
                )
                break

            # Execute each tool call
            tool_results = []
            for tc in response.tool_calls:
                result = executor.execute(tc.name, tc.input)
                tool_results.append((tc, result))

                # Log tool execution to DB
                if response.invocation_id:
                    self._log_tool_call(
                        tc, result, response.invocation_id, round_number
                    )

                logger.info(
                    f"Agent '{self._agent.name}' round {round_number}: "
                    f"tool={tc.name} status={result.status} "
                    f"time={result.execution_time_ms}ms"
                )

            # Build messages for the next LLM call
            round_messages = self._build_tool_round_messages(response, tool_results)
            messages.extend(round_messages)

        # Update agent-level counters with total cost across all rounds
        self._agent.record_usage(total_cost)

        # ── Output schema validation ───────────────────────────────────────────
        if self._agent.output_schema == "JSON" and response.content:
            from zango.ai.exceptions import OutputParseError, OutputValidationError

            try:
                parsed = json.loads(response.content)
            except json.JSONDecodeError as e:
                raise OutputParseError(
                    f"Agent '{self._agent.name}' returned invalid JSON: {e}"
                ) from e

            if self._agent.output_json_schema:
                try:
                    import jsonschema

                    jsonschema.validate(
                        instance=parsed, schema=self._agent.output_json_schema
                    )
                except jsonschema.ValidationError as e:
                    raise OutputValidationError(
                        message=e.message,
                        field=e.json_path,
                        errors=[e.message],
                    ) from e

            response.parsed_content = parsed

        # ── Memory: persist this exchange ─────────────────────────────────────
        if session_id and self._agent.memory_enabled:
            self._save_session_messages(
                session_id=session_id,
                user_ref=user_ref,
                input_messages=new_user_messages_for_memory,
                response=response,
            )
            response.session_id = session_id

        return response

    # ─────────────────────────────── Memory helpers ───────────────────────────

    def _load_session_messages(self, session_id: str) -> list:
        """
        Load prior messages for this session from the DB.
        Returns LLMMessage list ordered oldest-first, capped to
        memory_max_messages pairs (each pair = 1 user + 1 assistant).
        Fail-open: returns [] on any error so the LLM call is never blocked.
        """
        from zango.apps.ai.models.memory import AppLLMMemorySession

        try:
            session = AppLLMMemorySession.objects.filter(
                agent=self._agent,
                session_id=session_id,
                is_active=True,
            ).first()

            if not session:
                return []

            max_rows = (
                self._agent.memory_max_messages * 2
            )  # pairs → individual messages
            db_messages = list(session.messages.order_by("-sequence")[:max_rows])
            db_messages.reverse()  # oldest-first

            result = []
            for m in db_messages:
                result.append(
                    LLMMessage(
                        role=m.role,
                        content=m.content,
                    )
                )
            return result

        except Exception as e:
            logger.warning(
                f"Memory load failed for agent '{self._agent.name}' "
                f"session '{session_id}': {e}"
            )
            return []

    def _save_session_messages(
        self,
        session_id: str,
        user_ref: str,
        input_messages: list,
        response,
    ) -> None:
        """
        Persist the user input(s) and final assistant response to the DB.
        Stores only role=user messages and the final role=assistant message.
        File content blocks are replaced with [file: attachment] placeholders.
        Fail-open: logs error but never re-raises so the caller still gets the response.
        """
        from django.db import transaction
        from django.db.models import Max

        from zango.apps.ai.models.memory import AppLLMMemoryMessage, AppLLMMemorySession

        try:
            with transaction.atomic():
                session, _ = AppLLMMemorySession.objects.get_or_create(
                    agent=self._agent,
                    session_id=session_id,
                    defaults={"user_ref": user_ref},
                )
                # Trigger auto_now update on last_active_at
                session.save(update_fields=["last_active_at"])

                agg = session.messages.aggregate(max_seq=Max("sequence"))
                next_seq = (agg["max_seq"] or 0) + 1

                to_create = []

                for msg in input_messages:
                    if msg.role == "user":
                        content = self._sanitize_content_for_memory(msg.content)
                        to_create.append(
                            AppLLMMemoryMessage(
                                session=session,
                                role="user",
                                content=content,
                                invocation_id=response.invocation_id,
                                sequence=next_seq,
                            )
                        )
                        next_seq += 1

                # Save the final assistant response
                if response.content:
                    to_create.append(
                        AppLLMMemoryMessage(
                            session=session,
                            role="assistant",
                            content=response.content,
                            invocation_id=response.invocation_id,
                            sequence=next_seq,
                        )
                    )

                if to_create:
                    AppLLMMemoryMessage.objects.bulk_create(to_create)

        except Exception as e:
            logger.error(
                f"Memory save failed for agent '{self._agent.name}' "
                f"session '{session_id}': {e}"
            )

    def _sanitize_content_for_memory(self, content):
        """
        Replace file/image content blocks with lightweight text placeholders.
        Prevents large base64 blobs from being stored in the memory table.
        """
        if isinstance(content, str):
            return content

        if not isinstance(content, list):
            return content

        sanitized = []
        for block in content:
            if not isinstance(block, dict):
                sanitized.append(block)
                continue

            block_type = block.get("type", "")

            if block_type in ("image", "document"):
                # Anthropic content block
                source = block.get("source", {})
                if isinstance(source, dict) and source.get("type") == "url":
                    url = source.get("url", "")
                    sanitized.append({"type": "text", "text": f"[file: {url}]"})
                else:
                    sanitized.append({"type": "text", "text": "[file: attachment]"})

            elif block_type == "image_url":
                # OpenAI image block
                url = block.get("image_url", {}).get("url", "")
                if url.startswith("data:"):
                    sanitized.append({"type": "text", "text": "[file: attachment]"})
                else:
                    sanitized.append({"type": "text", "text": f"[file: {url}]"})

            else:
                sanitized.append(block)

        return sanitized

    def clear_session(self, session_id: str) -> bool:
        """
        Deactivate a session and delete all its messages.
        Returns True if found and cleared, False if not found.
        """
        from zango.apps.ai.models.memory import AppLLMMemorySession

        try:
            session = AppLLMMemorySession.objects.filter(
                agent=self._agent,
                session_id=session_id,
            ).first()

            if not session:
                return False

            session.messages.all().delete()
            session.is_active = False
            session.save(update_fields=["is_active"])
            return True

        except Exception as e:
            logger.error(
                f"clear_session failed for agent '{self._agent.name}' "
                f"session '{session_id}': {e}"
            )
            return False

    # ──────────────────────────────────────────────────────────────────────────

    def stream(self, *args, **kwargs):
        raise NotImplementedError(
            "AgentClient.stream() is not yet implemented. "
            "Use AgentClient.run() for synchronous agent execution."
        )
