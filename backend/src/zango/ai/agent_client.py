"""
AgentClient wraps an AppLLMAgent with execution logic:
- Resolves prompts with variables
- Calls the underlying ProviderClient
- Executes tool calls in an agentic loop
- Tracks agent-level usage
"""

import json
import logging
import time
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

    def _persist_invocation_files(self, invocation_id, audit_payloads):
        """
        Create AppLLMInvocationFile rows for an invocation.

        Bytes-bearing entries are saved through ZFileField (tenant-scoped
        storage). URL-only entries are recorded as identity rows with blob=None.
        Fail-open: errors are logged but never re-raised — audit failures must
        not break the agent run.
        """
        from django.core.files.base import ContentFile

        from zango.apps.ai.models.invocation import AppLLMInvocationFile

        for payload in audit_payloads:
            try:
                obj = AppLLMInvocationFile(
                    invocation_id=invocation_id,
                    sha256=payload.get("sha256", ""),
                    size_bytes=payload.get("size_bytes", 0),
                    media_type=payload.get("media_type", ""),
                    filename=payload.get("filename", ""),
                    source_kind=payload.get("source_kind", "upload"),
                    source_url=payload.get("source_url", ""),
                )
                data = payload.get("data")
                if data:
                    name = payload.get("filename") or "upload.bin"
                    obj.blob.save(name, ContentFile(data), save=False)
                obj.save()
            except Exception as e:
                logger.error(
                    f"Failed to persist invocation file "
                    f"(invocation_id={invocation_id}, filename={payload.get('filename')}): {e}"
                )

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
        system_variables: Optional[dict] = None,
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
            system_variables: Dict of template variables rendered into the agent's
                system_prompt. Separate from variables (user prompt). If omitted,
                the system prompt is used as-is (no variable substitution).
            messages: Full list of LLMMessage objects. Low-level escape hatch
                for multi-turn history or tool-result injection.
            files: File/image attachments (LLMFile instances).
            triggered_by: Audit label — "user" | "celery" | "cron" | "system".
            session_id: Memory session key. Auto-generated if short_term_memory and
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
            system = self._agent.get_system_prompt_content(**(system_variables or {}))

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
        if self._agent.short_term_memory and not session_id:
            session_id = str(uuid.uuid4())

        # ── Memory: prepend prior session messages ────────────────────────────
        history_messages = []
        if session_id and self._agent.short_term_memory:
            history_messages = self._load_session_messages(session_id)
            if history_messages:
                messages = history_messages + messages

        # Build agent tracking metadata for invocation logging
        agent_tracking = {
            "agent": self._agent,
            "agent_name": self._agent.name,
            "rendered_system_prompt": system,
            "context_snapshot": {
                "variables": variables,
                "system_variables": system_variables,
            },
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
        run_start_ms = time.monotonic() * 1000

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
        # Hash + capture file payloads BEFORE prepare_files() mutates them.
        # files_meta is the lightweight summary written to the invocation's
        # request_files JSON; audit_payloads carries the raw bytes used to
        # create AppLLMInvocationFile rows after round 1's invocation exists.
        files_meta = None
        audit_payloads = None
        if files:
            import hashlib

            files_meta = []
            audit_payloads = []
            for f in files:
                source_kind = "url" if (f.url and not f.data) else "upload"
                size_bytes = len(f.data) if f.data else 0
                sha256 = hashlib.sha256(f.data).hexdigest() if f.data else ""
                files_meta.append(
                    {
                        "filename": f.filename or None,
                        "media_type": f.media_type or None,
                        "size_bytes": size_bytes or None,
                        "sha256": sha256 or None,
                        "source": source_kind,
                        **({"url": f.url} if f.url else {}),
                    }
                )
                audit_payloads.append(
                    {
                        "data": f.data,
                        "sha256": sha256,
                        "size_bytes": size_bytes,
                        "media_type": f.media_type or "",
                        "filename": f.filename or "",
                        "source_kind": source_kind,
                        "source_url": f.url or "",
                    }
                )
            files_meta = files_meta or None
            audit_payloads = audit_payloads or None

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

        for round_number in range(1, max_tool_rounds + 2):
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
                request_files_meta=files_meta if round_number == 1 else None,
                **{**agent_tracking},
                **response_format_kwarg,
                **kwargs,
            )
            total_cost += response.cost_usd

            # Persist mirrored file blobs once, after round 1's invocation row exists.
            if round_number == 1 and audit_payloads and response.invocation_id:
                self._persist_invocation_files(response.invocation_id, audit_payloads)

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

        # Overwrite latency_ms with total wall-clock time across all rounds
        response.latency_ms = int(time.monotonic() * 1000 - run_start_ms)

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
        if session_id and self._agent.short_term_memory:
            new_messages_for_memory = messages[len(history_messages) :]
            self._save_session_messages(
                session_id=session_id,
                user_ref=user_ref,
                new_messages=new_messages_for_memory,
                response=response,
            )
            response.session_id = session_id

        return response

    # ─────────────────────────────── Memory helpers ───────────────────────────

    def _get_excluded_tool_names(self) -> set:
        """
        Return the set of tool names whose memory_policy is "exclude".
        These tools' call/result messages are dropped from loaded history.
        """
        from zango.apps.ai.models.tool import AppLLMTool

        if not self._agent.tools:
            return set()

        return set(
            AppLLMTool.objects.filter(
                name__in=self._agent.tools,
                memory_policy="exclude",
            ).values_list("name", flat=True)
        )

    def _load_session_messages(self, session_id: str) -> list:
        """
        Load prior messages for this session from the DB.
        Returns LLMMessage list ordered oldest-first, capped to
        short_term_memory_max_messages rows. Tool call/result message pairs whose
        tool has memory_policy="exclude" are dropped from the loaded history.
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

            max_rows = self._agent.short_term_memory_max_messages * 2
            db_messages = list(session.messages.order_by("-sequence")[:max_rows])
            db_messages.reverse()  # oldest-first

            excluded_tools = self._get_excluded_tool_names()

            # Identify sequences belonging to excluded tool rounds.
            # Strategy: walk messages in order; when an assistant message contains
            # a tool_use block for an excluded tool, mark it excluded and mark the
            # immediately following tool-result message (role="tool" for OpenAI or
            # role="user" with tool_result blocks for Anthropic) as excluded too.
            excluded_sequences = set()
            if excluded_tools:
                prev_assistant_excluded = False
                for m in db_messages:
                    if m.role == "assistant" and isinstance(m.content, list):
                        tool_use_names = {
                            b.get("name")
                            for b in m.content
                            if isinstance(b, dict) and b.get("type") == "tool_use"
                        }
                        if tool_use_names & excluded_tools:
                            excluded_sequences.add(m.sequence)
                            prev_assistant_excluded = True
                        else:
                            prev_assistant_excluded = False

                    elif m.role == "tool":
                        # OpenAI-style tool result follows the preceding assistant
                        if prev_assistant_excluded:
                            excluded_sequences.add(m.sequence)
                        prev_assistant_excluded = False

                    elif m.role == "user" and isinstance(m.content, list):
                        if any(
                            isinstance(b, dict) and b.get("type") == "tool_result"
                            for b in m.content
                        ):
                            # Anthropic-style tool result follows the preceding assistant
                            if prev_assistant_excluded:
                                excluded_sequences.add(m.sequence)
                        prev_assistant_excluded = False

                    else:
                        prev_assistant_excluded = False

            is_openai = self._is_openai_style_provider()

            result = []
            for m in db_messages:
                if m.sequence in excluded_sequences:
                    continue

                kwargs = {"role": m.role, "content": m.content}

                if m.role == "tool" and isinstance(m.content, dict):
                    # OpenAI-style tool result stored as {content, tool_call_id}
                    kwargs["content"] = m.content.get("content", m.content)
                    kwargs["tool_call_id"] = m.content.get("tool_call_id")

                elif (
                    is_openai
                    and m.role == "assistant"
                    and isinstance(m.content, list)
                    and any(
                        isinstance(b, dict) and b.get("type") == "tool_use"
                        for b in m.content
                    )
                ):
                    # Assistant tool-use round was stored in Anthropic-style content blocks.
                    # Convert back to OpenAI tool_calls format so the SDK doesn't reject it.
                    tool_calls = [
                        {
                            "id": b.get("id"),
                            "type": "function",
                            "function": {
                                "name": b.get("name"),
                                "arguments": (
                                    b.get("input")
                                    if isinstance(b.get("input"), str)
                                    else json.dumps(b.get("input") or {})
                                ),
                            },
                        }
                        for b in m.content
                        if isinstance(b, dict) and b.get("type") == "tool_use"
                    ]
                    text_blocks = [
                        b.get("text", "")
                        for b in m.content
                        if isinstance(b, dict) and b.get("type") == "text"
                    ]
                    kwargs["content"] = " ".join(text_blocks) if text_blocks else None
                    kwargs["tool_calls"] = tool_calls

                result.append(LLMMessage(**kwargs))
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
        new_messages: list,
        response,
    ) -> None:
        """
        Persist all messages from the current turn to the DB, including
        intermediate tool call/result rounds. File content blocks are replaced
        with lightweight placeholders. The final assistant text response is
        always persisted last.
        Fail-open: logs error but never re-raises so the caller gets the response.
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
                session.save(update_fields=["last_active_at"])

                agg = session.messages.aggregate(max_seq=Max("sequence"))
                next_seq = (agg["max_seq"] or 0) + 1

                to_create = []

                for msg in new_messages:
                    is_anthropic_tool_result = (
                        msg.role == "user"
                        and isinstance(msg.content, list)
                        and any(
                            isinstance(b, dict) and b.get("type") == "tool_result"
                            for b in msg.content
                        )
                    )
                    is_assistant_tool_use = msg.role == "assistant" and (
                        msg.tool_calls
                        or (
                            isinstance(msg.content, list)
                            and any(
                                isinstance(b, dict) and b.get("type") == "tool_use"
                                for b in msg.content
                            )
                        )
                    )

                    if is_anthropic_tool_result:
                        # Anthropic-style tool result block (role=user with tool_result)
                        to_create.append(
                            AppLLMMemoryMessage(
                                session=session,
                                role="user",
                                content=msg.content,
                                invocation_id=response.invocation_id,
                                sequence=next_seq,
                            )
                        )
                        next_seq += 1

                    elif msg.role == "user":
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

                    elif is_assistant_tool_use:
                        # Intermediate assistant message with tool calls — persist verbatim.
                        # OpenAI-style: content may be None when tool calls live in msg.tool_calls.
                        # Reconstruct content list so the JSONField is never null.
                        if msg.content is not None:
                            content = self._sanitize_content_for_memory(msg.content)
                        elif msg.tool_calls:
                            content = [
                                {
                                    "type": "tool_use",
                                    "id": tc.get("id"),
                                    "name": tc.get("function", {}).get("name"),
                                    "input": tc.get("function", {}).get("arguments"),
                                }
                                for tc in msg.tool_calls
                            ]
                        else:
                            content = []
                        to_create.append(
                            AppLLMMemoryMessage(
                                session=session,
                                role="assistant",
                                content=content,
                                invocation_id=response.invocation_id,
                                sequence=next_seq,
                            )
                        )
                        next_seq += 1

                    elif msg.role == "tool":
                        # OpenAI-style tool result — store content + tool_call_id together
                        stored_content = {
                            "content": msg.content,
                            "tool_call_id": msg.tool_call_id,
                        }
                        to_create.append(
                            AppLLMMemoryMessage(
                                session=session,
                                role="tool",
                                content=stored_content,
                                invocation_id=response.invocation_id,
                                sequence=next_seq,
                            )
                        )
                        next_seq += 1

                # Final assistant text response
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
