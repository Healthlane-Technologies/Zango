"""
Unit tests for AgentClient (zango.ai.agent_client).

ProviderClient and ToolExecutor are patched. Only AgentClient's own
orchestration logic runs: guard checks, input resolution, system/output
config, agentic loop, message format routing, memory sanitization,
and memory load/save flow.
"""

import uuid
from unittest.mock import MagicMock, call, patch

from django.test import SimpleTestCase

from zango.ai.agent_client import AgentClient
from zango.ai.exceptions import AgentDisabled
from zango.ai.providers.base import LLMMessage, LLMResponse, LLMToolCall, LLMUsage

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_response(content="Done", tool_calls=None, stop_reason="end_turn", cost=0.001):
    return LLMResponse(
        content=content,
        tool_calls=tool_calls or [],
        stop_reason=stop_reason,
        usage=LLMUsage(input_tokens=100, output_tokens=50),
        model="claude-sonnet-4-20250514",
        raw_response=None,
        latency_ms=100,
        cost_usd=cost,
        invocation_id=1,
    )


def _make_tool_call(name="get_scores", input_data=None, call_id="tc_001"):
    return LLMToolCall(id=call_id, name=name, input=input_data or {"employee_id": 42})


def _make_tool_result(status="success", output=None, error_message=None):
    r = MagicMock()
    r.status = status
    r.output = output if output is not None else {"score": 88}
    r.error_message = error_message
    r.error_traceback = None
    r.execution_time_ms = 10
    return r


def _make_agent(
    tools=None,
    provider_slug="anthropic",
    memory_enabled=False,
    output_schema=None,
    output_json_schema=None,
):
    agent = MagicMock()
    agent.name = "test-agent"
    agent.is_enabled = True
    agent.provider = MagicMock()
    agent.provider.provider_slug = provider_slug
    agent.provider.name = "test-provider"
    agent.model = "claude-sonnet-4-20250514"
    agent.temperature = 0.7
    agent.max_tokens = 1024
    agent.tools = tools or []
    agent.system_prompt = None
    agent.user_prompt = None
    agent.memory_enabled = memory_enabled
    agent.memory_max_messages = 10
    agent.output_schema = output_schema
    agent.output_json_schema = output_json_schema
    agent.get_user_prompt_content.return_value = "Template rendered content"
    agent.get_system_prompt_content.return_value = "System prompt content"
    return agent


# All four are lazy-imported inside run() — patch at canonical paths.
_PC = "zango.ai.client.ProviderClient"
_EXEC = "zango.ai.tools.executor.ToolExecutor"
_TOOL_MODEL = "zango.apps.ai.models.tool.AppLLMTool"
_TOOL_CALL_MODEL = "zango.apps.ai.models.tool.AppLLMToolCall"


# ─── 6a. Guard checks ─────────────────────────────────────────────────────────

class GuardCheckTest(SimpleTestCase):

    def test_disabled_agent_raises_agent_disabled(self):
        agent = _make_agent()
        agent.is_enabled = False
        with self.assertRaises(AgentDisabled):
            AgentClient(agent).run(input="hello")

    def test_no_provider_raises_value_error(self):
        agent = _make_agent()
        agent.provider = None
        with self.assertRaises(ValueError):
            AgentClient(agent).run(input="hello")

    @patch(_PC)
    def test_no_input_no_prompt_raises_value_error(self, mock_pc_cls):
        agent = _make_agent()
        agent.get_user_prompt_content.return_value = ""
        mock_pc_cls.return_value._get_client.return_value = MagicMock()
        with self.assertRaises(ValueError):
            AgentClient(agent).run()


# ─── 6b. Input resolution ─────────────────────────────────────────────────────

class InputResolutionTest(SimpleTestCase):

    def _run_and_capture_messages(self, agent, **kwargs):
        with patch(_PC) as mock_pc_cls:
            mock_pc = MagicMock()
            mock_pc.complete.return_value = _make_response()
            mock_pc._get_client.return_value = MagicMock()
            mock_pc_cls.return_value = mock_pc
            AgentClient(agent).run(**kwargs)
            return mock_pc.complete.call_args.kwargs["messages"]

    def test_input_string_used_directly(self):
        agent = _make_agent()
        messages = self._run_and_capture_messages(agent, input="hello")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "hello")

    def test_input_wins_over_variables(self):
        agent = _make_agent()
        messages = self._run_and_capture_messages(
            agent, input="explicit", variables={"x": 1}
        )
        self.assertEqual(messages[0].content, "explicit")
        agent.get_user_prompt_content.assert_not_called()

    def test_variables_renders_template(self):
        agent = _make_agent()
        agent.get_user_prompt_content.return_value = "rendered with x=1"
        messages = self._run_and_capture_messages(agent, variables={"x": 1})
        agent.get_user_prompt_content.assert_called_once_with(x=1)
        self.assertEqual(messages[0].content, "rendered with x=1")

    def test_explicit_messages_passed_directly(self):
        agent = _make_agent()
        explicit = [LLMMessage(role="user", content="custom")]
        messages = self._run_and_capture_messages(agent, messages=explicit)
        self.assertEqual(messages[0].content, "custom")
        agent.get_user_prompt_content.assert_not_called()

    def test_files_only_no_text_creates_empty_content_message(self):
        agent = _make_agent()
        agent.get_user_prompt_content.return_value = ""
        file_mock = MagicMock()
        file_mock.to_anthropic_block.return_value = {"type": "image", "source": {}}

        with patch(_PC) as mock_pc_cls:
            mock_pc = MagicMock()
            mock_pc.complete.return_value = _make_response()
            raw = MagicMock()
            raw.prepare_files.return_value = [file_mock]
            mock_pc._get_client.return_value = raw
            mock_pc_cls.return_value = mock_pc
            AgentClient(agent).run(files=[file_mock])

        messages = mock_pc.complete.call_args.kwargs["messages"]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "user")

    def test_files_appended_to_last_user_message_in_explicit_messages(self):
        agent = _make_agent()
        existing = [
            LLMMessage(role="user", content="first"),
            LLMMessage(role="assistant", content="reply"),
            LLMMessage(role="user", content="second"),
        ]
        file_mock = MagicMock()
        file_mock.to_anthropic_block.return_value = {"type": "image", "source": {}}
        with patch(_PC) as mock_pc_cls:
            mock_pc = MagicMock()
            mock_pc.complete.return_value = _make_response()
            raw = MagicMock()
            raw.prepare_files.return_value = [file_mock]
            mock_pc._get_client.return_value = raw
            mock_pc_cls.return_value = mock_pc
            AgentClient(agent).run(messages=existing, files=[file_mock])
        # After prepare_files the file block is baked into message content;
        # the last user message (index 2) should have a list content with the block.
        last_user_msg = existing[2]
        self.assertIsInstance(last_user_msg.content, list)

    def test_files_creates_new_user_message_when_no_user_message_in_explicit(self):
        agent = _make_agent()
        explicit = [LLMMessage(role="assistant", content="reply")]
        file_mock = MagicMock()
        with patch(_PC) as mock_pc_cls:
            mock_pc = MagicMock()
            mock_pc.complete.return_value = _make_response()
            mock_pc._get_client.return_value = MagicMock()
            mock_pc_cls.return_value = mock_pc
            AgentClient(agent).run(messages=explicit, files=[file_mock])
        messages = mock_pc.complete.call_args.kwargs["messages"]
        # A new user message must have been appended
        roles = [m.role for m in messages]
        self.assertIn("user", roles)


# ─── 6c. System prompt rendering ─────────────────────────────────────────────

class SystemPromptTest(SimpleTestCase):

    def _run_and_capture_system(self, agent, **kwargs):
        with patch(_PC) as mock_pc_cls:
            mock_pc = MagicMock()
            mock_pc.complete.return_value = _make_response()
            mock_pc._get_client.return_value = MagicMock()
            mock_pc_cls.return_value = mock_pc
            AgentClient(agent).run(**kwargs)
            return mock_pc.complete.call_args.kwargs.get("system")

    def test_no_system_prompt_passes_none(self):
        agent = _make_agent()
        agent.system_prompt = None
        system = self._run_and_capture_system(agent, input="hi")
        self.assertIsNone(system)

    def test_system_prompt_rendered_and_forwarded(self):
        agent = _make_agent()
        agent.system_prompt = MagicMock()
        agent.get_system_prompt_content.return_value = "You are helpful"
        system = self._run_and_capture_system(agent, input="hi")
        self.assertEqual(system, "You are helpful")


# ─── 6d. Output format ────────────────────────────────────────────────────────

class OutputFormatTest(SimpleTestCase):

    def _run_and_get_complete_kwargs(self, agent):
        with patch(_PC) as mock_pc_cls:
            mock_pc = MagicMock()
            mock_pc.complete.return_value = _make_response()
            mock_pc._get_client.return_value = MagicMock()
            mock_pc_cls.return_value = mock_pc
            AgentClient(agent).run(input="hi")
            return mock_pc.complete.call_args.kwargs

    def test_no_output_schema_no_response_format_kwarg(self):
        agent = _make_agent(output_schema=None)
        kwargs = self._run_and_get_complete_kwargs(agent)
        self.assertNotIn("response_format", kwargs)

    def test_json_output_schema_no_json_schema_passes_json_string(self):
        agent = _make_agent(output_schema="JSON", output_json_schema=None)
        kwargs = self._run_and_get_complete_kwargs(agent)
        self.assertEqual(kwargs.get("response_format"), "json")

    def test_json_output_schema_with_json_schema_passes_dict(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        agent = _make_agent(output_schema="JSON", output_json_schema=schema)
        kwargs = self._run_and_get_complete_kwargs(agent)
        self.assertEqual(kwargs.get("response_format"), schema)


# ─── 6e. Agentic loop ─────────────────────────────────────────────────────────

class AgenticLoopTest(SimpleTestCase):

    def _patched_run(self, agent, mock_pc, tool_results=None, **run_kwargs):
        """Run with ProviderClient and ToolExecutor patched."""
        with patch(_PC) as mock_pc_cls:
            mock_pc_cls.return_value = mock_pc
            with patch(_EXEC) as mock_exec_cls:
                mock_exec = MagicMock()
                if tool_results:
                    mock_exec.execute.side_effect = tool_results
                else:
                    mock_exec.execute.return_value = _make_tool_result()
                mock_exec_cls.return_value = mock_exec
                with patch(_TOOL_MODEL):
                    with patch(_TOOL_CALL_MODEL):
                        return AgentClient(agent).run(**run_kwargs), mock_pc, mock_exec

    def _make_pc(self, responses):
        mock_pc = MagicMock()
        mock_pc.complete.side_effect = responses if len(responses) > 1 else None
        if len(responses) == 1:
            mock_pc.complete.return_value = responses[0]
        mock_pc._get_client.return_value = MagicMock()
        return mock_pc

    def test_no_tools_single_llm_call(self):
        agent = _make_agent()
        mock_pc = self._make_pc([_make_response("Final")])
        response, pc, _ = self._patched_run(agent, mock_pc, input="hi")
        self.assertEqual(response.content, "Final")
        pc.complete.assert_called_once()

    def test_one_tool_call_then_done(self):
        agent = _make_agent(tools=["get_scores"])
        tc = _make_tool_call()
        round1 = _make_response("", tool_calls=[tc], stop_reason="tool_use")
        round2 = _make_response("Final after tool")
        mock_pc = self._make_pc([round1, round2])
        response, pc, executor = self._patched_run(agent, mock_pc, input="hi")
        self.assertEqual(response.content, "Final after tool")
        self.assertEqual(pc.complete.call_count, 2)
        executor.execute.assert_called_once_with("get_scores", {"employee_id": 42})

    def test_two_tool_calls_in_one_round(self):
        agent = _make_agent(tools=["get_scores", "get_name"])
        tc1 = _make_tool_call("get_scores", call_id="tc1")
        tc2 = _make_tool_call("get_name", input_data={"id": 1}, call_id="tc2")
        round1 = _make_response("", tool_calls=[tc1, tc2], stop_reason="tool_use")
        round2 = _make_response("Done")
        mock_pc = self._make_pc([round1, round2])
        _, _, executor = self._patched_run(agent, mock_pc, input="hi")
        self.assertEqual(executor.execute.call_count, 2)

    def test_max_rounds_safety_limits_loop(self):
        agent = _make_agent(tools=["get_scores"])
        tc = _make_tool_call()
        infinite = _make_response("", tool_calls=[tc], stop_reason="tool_use")
        mock_pc = MagicMock()
        mock_pc.complete.return_value = infinite
        mock_pc._get_client.return_value = MagicMock()
        _, pc, _ = self._patched_run(agent, mock_pc, input="hi", max_tool_rounds=3)
        self.assertLessEqual(pc.complete.call_count, 5)

    def test_total_cost_summed_across_rounds(self):
        agent = _make_agent(tools=["get_scores"])
        tc = _make_tool_call()
        round1 = _make_response("", tool_calls=[tc], stop_reason="tool_use", cost=0.002)
        round2 = _make_response("Done", cost=0.003)
        mock_pc = self._make_pc([round1, round2])
        self._patched_run(agent, mock_pc, input="hi")
        agent.record_usage.assert_called_once_with(pytest.approx(0.005, abs=1e-6)
                                                    if False else 0.005)
        # Verify via call_args
        actual_cost = agent.record_usage.call_args[0][0]
        self.assertAlmostEqual(actual_cost, 0.005, places=6)

    def test_run_id_same_across_all_rounds(self):
        agent = _make_agent(tools=["get_scores"])
        tc = _make_tool_call()
        round1 = _make_response("", tool_calls=[tc], stop_reason="tool_use")
        round2 = _make_response("Done")
        mock_pc = self._make_pc([round1, round2])
        self._patched_run(agent, mock_pc, input="hi")
        calls = mock_pc.complete.call_args_list
        run_ids = [c.kwargs["run_id"] for c in calls]
        self.assertEqual(run_ids[0], run_ids[1])

    def test_round_number_increments(self):
        agent = _make_agent(tools=["get_scores"])
        tc = _make_tool_call()
        round1 = _make_response("", tool_calls=[tc], stop_reason="tool_use")
        round2 = _make_response("Done")
        mock_pc = self._make_pc([round1, round2])
        self._patched_run(agent, mock_pc, input="hi")
        calls = mock_pc.complete.call_args_list
        self.assertEqual(calls[0].kwargs["round_number"], 1)
        self.assertEqual(calls[1].kwargs["round_number"], 2)

    def test_no_tools_configured_passes_none_to_complete(self):
        agent = _make_agent(tools=[])
        mock_pc = self._make_pc([_make_response()])
        self._patched_run(agent, mock_pc, input="hi")
        self.assertIsNone(mock_pc.complete.call_args.kwargs["tools"])

    def test_tool_error_result_fed_back_and_loop_continues(self):
        agent = _make_agent(tools=["get_scores"])
        tc = _make_tool_call()
        round1 = _make_response("", tool_calls=[tc], stop_reason="tool_use")
        round2 = _make_response("Recovered")
        mock_pc = self._make_pc([round1, round2])
        error_result = _make_tool_result(status="error", output=None,
                                         error_message="DB error")
        with patch(_PC) as mock_pc_cls:
            mock_pc_cls.return_value = mock_pc
            with patch(_EXEC) as mock_exec_cls:
                mock_exec_cls.return_value.execute.return_value = error_result
                with patch(_TOOL_MODEL):
                    with patch(_TOOL_CALL_MODEL):
                        response = AgentClient(agent).run(input="hi")
        self.assertEqual(response.content, "Recovered")
        self.assertEqual(mock_pc.complete.call_count, 2)


# ─── 6f. Message format routing ───────────────────────────────────────────────

class MessageFormatTest(SimpleTestCase):
    """_build_tool_round_messages — pure logic, no I/O."""

    def _build(self, provider_slug, tc_list, result_list):
        agent = _make_agent(provider_slug=provider_slug)
        client = AgentClient(agent)
        response = _make_response("", tool_calls=tc_list, stop_reason="tool_use")
        return client._build_tool_round_messages(response, list(zip(tc_list, result_list)))

    def test_anthropic_success_structure(self):
        tc = _make_tool_call()
        messages = self._build("anthropic", [tc], [_make_tool_result()])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "assistant")
        self.assertEqual(messages[1].role, "user")
        self.assertEqual(messages[1].content[0]["type"], "tool_result")

    def test_anthropic_error_result_sets_is_error_flag(self):
        tc = _make_tool_call()
        result = _make_tool_result(status="error", output=None, error_message="DB failed")
        messages = self._build("anthropic", [tc], [result])
        self.assertTrue(messages[1].content[0]["is_error"])
        self.assertIn("Error:", messages[1].content[0]["content"])

    def test_anthropic_text_plus_tool_call_in_same_response(self):
        tc = _make_tool_call()
        agent = _make_agent(provider_slug="anthropic")
        client = AgentClient(agent)
        response = _make_response("Thinking...", tool_calls=[tc], stop_reason="tool_use")
        messages = client._build_tool_round_messages(response, [(tc, _make_tool_result())])
        # assistant content must have text block AND tool_use block
        assistant_content = messages[0].content
        types = [b["type"] for b in assistant_content]
        self.assertIn("text", types)
        self.assertIn("tool_use", types)

    def test_openai_success_structure(self):
        tc = _make_tool_call()
        messages = self._build("openai", [tc], [_make_tool_result()])
        self.assertEqual(messages[0].role, "assistant")
        self.assertIsNotNone(messages[0].tool_calls)
        self.assertEqual(messages[1].role, "tool")
        self.assertEqual(messages[1].tool_call_id, "tc_001")

    def test_openai_error_result_content_is_error_string(self):
        tc = _make_tool_call()
        result = _make_tool_result(status="error", output=None, error_message="DB failed")
        messages = self._build("openai", [tc], [result])
        self.assertIn("Error:", messages[1].content)

    def test_azure_openai_same_as_openai(self):
        tc = _make_tool_call()
        messages = self._build("azure_openai", [tc], [_make_tool_result()])
        self.assertEqual(messages[1].role, "tool")

    def test_anthropic_multiple_tool_calls_single_user_message(self):
        tc1 = _make_tool_call("t1", call_id="c1")
        tc2 = _make_tool_call("t2", call_id="c2")
        messages = self._build("anthropic", [tc1, tc2],
                               [_make_tool_result(), _make_tool_result()])
        # One assistant message + one user message with two tool_result blocks
        self.assertEqual(len(messages), 2)
        self.assertEqual(len(messages[1].content), 2)

    def test_openai_multiple_tool_calls_multiple_tool_messages(self):
        tc1 = _make_tool_call("t1", call_id="c1")
        tc2 = _make_tool_call("t2", call_id="c2")
        messages = self._build("openai", [tc1, tc2],
                               [_make_tool_result(), _make_tool_result()])
        # One assistant + two role=tool messages
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[1].role, "tool")
        self.assertEqual(messages[2].role, "tool")


# ─── 6g. Memory sanitization ──────────────────────────────────────────────────

class MemorySanitizationTest(SimpleTestCase):

    def _sanitize(self, content):
        return AgentClient(MagicMock())._sanitize_content_for_memory(content)

    def test_plain_string_unchanged(self):
        self.assertEqual(self._sanitize("hello"), "hello")

    def test_non_list_dict_unchanged(self):
        d = {"type": "text"}
        self.assertEqual(self._sanitize(d), d)

    def test_anthropic_base64_image_replaced(self):
        content = [{"type": "image", "source": {"type": "base64", "data": "ABCD"}}]
        result = self._sanitize(content)
        self.assertEqual(result[0], {"type": "text", "text": "[file: attachment]"})

    def test_anthropic_base64_document_replaced(self):
        content = [{"type": "document", "source": {"type": "base64", "data": "ABCD"}}]
        result = self._sanitize(content)
        self.assertEqual(result[0]["text"], "[file: attachment]")

    def test_anthropic_url_block_keeps_url(self):
        content = [{"type": "image", "source": {"type": "url", "url": "https://cdn.example.com/img.png"}}]
        result = self._sanitize(content)
        self.assertIn("https://cdn.example.com/img.png", result[0]["text"])

    def test_openai_data_url_replaced(self):
        content = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,ABC"}}]
        result = self._sanitize(content)
        self.assertEqual(result[0], {"type": "text", "text": "[file: attachment]"})

    def test_openai_public_url_keeps_url(self):
        content = [{"type": "image_url", "image_url": {"url": "https://cdn.example.com/img.png"}}]
        result = self._sanitize(content)
        self.assertIn("https://cdn.example.com/img.png", result[0]["text"])

    def test_text_block_preserved(self):
        content = [{"type": "text", "text": "hello"}]
        result = self._sanitize(content)
        self.assertEqual(result[0], {"type": "text", "text": "hello"})

    def test_mixed_list_file_sanitized_text_preserved(self):
        content = [
            {"type": "image", "source": {"type": "base64", "data": "ABCD"}},
            {"type": "text", "text": "What is this?"},
        ]
        result = self._sanitize(content)
        self.assertEqual(result[0]["text"], "[file: attachment]")
        self.assertEqual(result[1]["text"], "What is this?")

    def test_empty_list_returns_empty_list(self):
        self.assertEqual(self._sanitize([]), [])


# ─── 6h. Memory flow ──────────────────────────────────────────────────────────

class MemoryFlowTest(SimpleTestCase):

    def _run_with_memory(self, agent, load_return=None, **run_kwargs):
        with patch(_PC) as mock_pc_cls:
            mock_pc = MagicMock()
            mock_pc.complete.return_value = _make_response("Answer")
            mock_pc._get_client.return_value = MagicMock()
            mock_pc_cls.return_value = mock_pc

            _MEM_SESSION = "zango.apps.ai.models.memory.AppLLMMemorySession"
            _MEM_MSG = "zango.apps.ai.models.memory.AppLLMMemoryMessage"

            with patch(_MEM_SESSION) as mock_session_model:
                with patch(_MEM_MSG) as mock_msg_model:
                    # Setup load
                    mock_session = MagicMock()
                    mock_session.messages.order_by.return_value.__getitem__ = \
                        MagicMock(return_value=load_return or [])
                    mock_session_model.objects.filter.return_value.first.return_value = (
                        mock_session if load_return is not None else None
                    )
                    # Setup save
                    mock_session_model.objects.get_or_create.return_value = (
                        MagicMock(), True
                    )
                    mock_session_model.objects.filter.return_value.first.return_value = None
                    mock_msg_model.objects.bulk_create = MagicMock()

                    response = AgentClient(agent).run(**run_kwargs)
                    return response, mock_pc, mock_session_model, mock_msg_model

    def test_memory_disabled_no_session_id_on_response(self):
        agent = _make_agent(memory_enabled=False)
        response, _, _, _ = self._run_with_memory(agent, input="hi")
        self.assertIsNone(response.session_id)

    def test_memory_enabled_auto_generates_session_id(self):
        agent = _make_agent(memory_enabled=True)
        response, _, _, _ = self._run_with_memory(agent, input="hi")
        self.assertIsNotNone(response.session_id)
        # Must be a valid UUID
        uuid.UUID(str(response.session_id))

    def test_memory_enabled_explicit_session_id_preserved(self):
        agent = _make_agent(memory_enabled=True)
        response, _, _, _ = self._run_with_memory(
            agent, input="hi", session_id="sess-abc"
        )
        self.assertEqual(response.session_id, "sess-abc")

    def test_memory_load_failure_does_not_block_llm_call(self):
        agent = _make_agent(memory_enabled=True)
        with patch(_PC) as mock_pc_cls:
            mock_pc = MagicMock()
            mock_pc.complete.return_value = _make_response("Answer")
            mock_pc._get_client.return_value = MagicMock()
            mock_pc_cls.return_value = mock_pc

            _MEM_SESSION = "zango.apps.ai.models.memory.AppLLMMemorySession"
            with patch(_MEM_SESSION) as mock_session_model:
                # Load raises
                mock_session_model.objects.filter.side_effect = Exception("DB down")
                mock_session_model.objects.get_or_create.return_value = (MagicMock(), True)
                response = AgentClient(agent).run(input="hi")

        # LLM was still called despite memory load failure
        mock_pc.complete.assert_called_once()
        self.assertEqual(response.content, "Answer")

    def test_memory_save_failure_does_not_crash_caller(self):
        agent = _make_agent(memory_enabled=True)
        with patch(_PC) as mock_pc_cls:
            mock_pc = MagicMock()
            mock_pc.complete.return_value = _make_response("Answer")
            mock_pc._get_client.return_value = MagicMock()
            mock_pc_cls.return_value = mock_pc

            _MEM_SESSION = "zango.apps.ai.models.memory.AppLLMMemorySession"
            with patch(_MEM_SESSION) as mock_session_model:
                mock_session_model.objects.filter.return_value.first.return_value = None
                # Save raises
                mock_session_model.objects.get_or_create.side_effect = Exception("DB down")
                response = AgentClient(agent).run(input="hi")

        # Response still returned despite save failure
        self.assertEqual(response.content, "Answer")
