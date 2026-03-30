"""
AgentClient wraps an AppLLMAgent with execution logic:
- Resolves prompts with variables
- Calls the underlying ProviderClient
- Executes tool calls in an agentic loop
- Tracks agent-level usage
"""

import json
import logging
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
            new_messages.append(LLMMessage(
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
            ))
            for tc, result in tool_results:
                if result.status == "success":
                    content = json.dumps(result.output) if not isinstance(result.output, str) else result.output
                else:
                    content = f"Error: {result.error_message}"
                new_messages.append(LLMMessage(
                    role="tool",
                    content=content,
                    tool_call_id=tc.id,
                ))
        else:
            # Anthropic format: assistant content blocks, then user message with tool_result blocks
            assistant_content = []
            if response.content:
                assistant_content.append({"type": "text", "text": response.content})
            for tc in response.tool_calls:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.input,
                })
            new_messages.append(LLMMessage(role="assistant", content=assistant_content))

            tool_result_blocks = []
            for tc, result in tool_results:
                if result.status == "success":
                    content = json.dumps(result.output) if not isinstance(result.output, str) else result.output
                else:
                    content = f"Error: {result.error_message}"
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": content,
                    "is_error": result.status != "success",
                })
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

            # Update tool-level stats
            if tool_record:
                tool_record.total_calls += 1
                if result.status == "error":
                    tool_record.total_errors += 1
                elif result.status == "timeout":
                    tool_record.total_timeouts += 1
                from django.utils import timezone
                tool_record.last_called_at = timezone.now()
                tool_record.save(update_fields=[
                    "total_calls", "total_errors", "total_timeouts", "last_called_at",
                ])
        except Exception as e:
            logger.error(f"Failed to log tool call '{tool_call.name}': {e}")

    def run(
        self,
        variables: Optional[dict] = None,
        messages: Optional[list[LLMMessage]] = None,
        triggered_by: str = "user",
        max_tool_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
        **kwargs,
    ) -> LLMResponse:
        """
        Execute the agent with an agentic tool loop:
        1. Check agent is enabled
        2. Render system_prompt with variables
        3. Build messages: if provided use them, else render user_prompt
        4. Call provider_client.complete() with agent's params
        5. If the LLM requests tool calls, execute them and loop
        6. Repeat until the LLM produces a final response or max rounds reached
        7. Update agent usage counters
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

        # Build messages
        if messages is None:
            messages = []
            user_content = self._agent.get_user_prompt_content(**(variables or {}))
            if user_content:
                messages.append(LLMMessage(role="user", content=user_content))

        if not messages:
            raise ValueError(
                f"Agent '{self._agent.name}' has no user prompt and no messages provided."
            )

        # Build agent tracking metadata for invocation logging
        agent_tracking = {
            "agent": self._agent,
            "agent_name": self._agent.name,
            "rendered_system_prompt": system,
            "context_snapshot": variables,
        }
        if self._agent.system_prompt and self._agent.system_prompt.active_version:
            agent_tracking["system_prompt_name"] = self._agent.system_prompt.name
            agent_tracking["system_prompt_version"] = self._agent.system_prompt.active_version.version_number
        if self._agent.user_prompt and self._agent.user_prompt.active_version:
            agent_tracking["user_prompt_name"] = self._agent.user_prompt.name
            agent_tracking["user_prompt_version"] = self._agent.user_prompt.active_version.version_number

        # Resolve agent tools to LLMToolDef objects for the LLM
        llm_tools = self._resolve_tools()

        # Resolve response_format from agent config
        response_format_kwarg = {}
        if self._agent.output_schema == "JSON":
            if self._agent.output_json_schema:
                response_format_kwarg["response_format"] = self._agent.output_json_schema
            else:
                response_format_kwarg["response_format"] = "json"

        # Execute via ProviderClient with agentic tool loop
        provider_client = ProviderClient(self._agent.provider)
        executor = ToolExecutor()
        total_cost = 0.0

        for round_number in range(1, max_tool_rounds + 2):
            response = provider_client.complete(
                messages=messages,
                model=self._agent.model,
                tools=llm_tools,
                temperature=self._agent.temperature,
                max_tokens=self._agent.max_tokens,
                system=system,
                triggered_by=triggered_by,
                **{**agent_tracking},
                **response_format_kwarg,
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
                    self._log_tool_call(tc, result, response.invocation_id, round_number)

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

        return response

    def stream(
        self,
        variables: Optional[dict] = None,
        messages: Optional[list[LLMMessage]] = None,
        triggered_by: str = "user",
        **kwargs,
    ):
        """
        Streaming version of run(). Yields LLMStreamChunks.
        """
        from zango.ai.client import ProviderClient

        if not self._agent.is_enabled:
            raise AgentDisabled(self._agent.name)

        if not self._agent.provider:
            raise ValueError(f"Agent '{self._agent.name}' has no provider configured.")

        system = None
        if self._agent.system_prompt:
            system = self._agent.get_system_prompt_content(**(variables or {}))

        if messages is None:
            messages = []
            user_content = self._agent.get_user_prompt_content(**(variables or {}))
            if user_content:
                messages.append(LLMMessage(role="user", content=user_content))

        if not messages:
            raise ValueError(
                f"Agent '{self._agent.name}' has no user prompt and no messages provided."
            )

        # Resolve agent tools
        llm_tools = self._resolve_tools()

        provider_client = ProviderClient(self._agent.provider)
        return provider_client.stream(
            messages=messages,
            model=self._agent.model,
            tools=llm_tools,
            temperature=self._agent.temperature,
            max_tokens=self._agent.max_tokens,
            system=system,
            triggered_by=triggered_by,
            **kwargs,
        )
