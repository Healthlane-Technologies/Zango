"""Per-model usage capture.

`AgentRun.model_usage` existed as a column from the start but nothing ever
wrote to it: `record_message` summed `ResultMessage.model_usage` into four
token totals and dropped the dict. Since `AgentRun.model` holds the
*configured* model — blank whenever the platform default is used, which is
every run so far — the panel had no way to report which models actually ran.

These tests cover the capture path and the fallback used when a run dies
before producing a ResultMessage.
"""

import unittest

from zango.apps.agent_mode.mapper import sum_model_usage


class _Recorder:
    """Minimal stand-in; these tests only care about accumulated state."""

    def __init__(self):
        self.emitted = []
        self.seq = 0

    def emit(self, kind, message, **kwargs):
        self.seq += 1
        self.emitted.append((kind, message, kwargs))


class ResultMessage:
    """Shape of claude_agent_sdk ResultMessage, fields read by the mapper.

    The class name matters: `record_message` dispatches on
    `type(obj).__name__`, so a differently-named double is silently ignored.
    """

    def __init__(self, model_usage):
        self.subtype = "success"
        self.terminal_reason = "completed"
        self.result = "done"
        self.num_turns = 12
        self.duration_api_ms = 1000
        self.total_cost_usd = 1.5
        self.api_error_status = None
        self.is_error = False
        self.permission_denials = None
        self.session_id = "sess-1"
        self.model_usage = model_usage


class AssistantMessage:
    def __init__(self, model):
        self.model = model
        self.content = []
        self.parent_tool_use_id = None


TWO_MODELS = {
    "claude-opus-4-5-20251101": {
        "inputTokens": 150,
        "outputTokens": 80000,
        "cacheReadInputTokens": 20000000,
        "cacheCreationInputTokens": 300000,
        "costUSD": 14.9,
    },
    "claude-haiku-4-5-20251001": {
        "inputTokens": 48,
        "outputTokens": 10516,
        "cacheReadInputTokens": 2669311,
        "cacheCreationInputTokens": 14554,
        "costUSD": 0.66,
    },
}


class SumModelUsageTests(unittest.TestCase):
    def test_totals_across_models(self):
        totals = sum_model_usage(TWO_MODELS)
        self.assertEqual(totals["input_tokens"], 198)
        self.assertEqual(totals["output_tokens"], 90516)
        self.assertEqual(totals["cache_read_tokens"], 22669311)
        self.assertEqual(totals["cache_creation_tokens"], 314554)

    def test_non_dict_is_survivable(self):
        self.assertEqual(sum_model_usage(None)["input_tokens"], 0)
        self.assertEqual(sum_model_usage("nope")["output_tokens"], 0)


class RecordModelUsageTests(unittest.TestCase):
    def test_result_message_keeps_the_raw_breakdown(self):
        """The regression: totals were kept, the per-model dict was dropped."""
        from zango.apps.agent_mode.mapper import record_message

        state = {}
        record_message(ResultMessage(TWO_MODELS), _Recorder(), state)
        self.assertEqual(state.get("model_usage"), TWO_MODELS)
        # And the totals must still be derived, as before.
        self.assertEqual(state["input_tokens"], 198)
        self.assertEqual(state["cache_read_tokens"], 22669311)

    def test_absent_usage_sets_no_key(self):
        from zango.apps.agent_mode.mapper import record_message

        state = {}
        record_message(ResultMessage(None), _Recorder(), state)
        self.assertNotIn("model_usage", state)

    def test_assistant_messages_track_models_as_a_fallback(self):
        """A run that dies before the result has no model_usage at all."""
        from zango.apps.agent_mode.mapper import record_message

        state = {}
        rec = _Recorder()
        record_message(AssistantMessage("claude-opus-4-5-20251101"), rec, state)
        record_message(AssistantMessage("claude-opus-4-5-20251101"), rec, state)
        record_message(AssistantMessage("claude-haiku-4-5-20251001"), rec, state)
        self.assertEqual(
            state["models_seen"],
            {"claude-opus-4-5-20251101": 2, "claude-haiku-4-5-20251001": 1},
        )

    def test_missing_model_attribute_is_ignored(self):
        from zango.apps.agent_mode.mapper import record_message

        state = {}
        record_message(AssistantMessage(""), _Recorder(), state)
        self.assertNotIn("models_seen", state)


class ApplyStatePersistenceTests(unittest.TestCase):
    """`_apply_state` saves with an explicit update_fields — a field set but
    not listed there is silently discarded, which is how the first real run
    lost its cost and tokens."""

    def test_model_usage_is_in_update_fields(self):
        import inspect

        from zango.apps.agent_mode import tasks

        source = inspect.getsource(tasks._apply_state)
        self.assertIn('run.model_usage = usage', source)
        self.assertIn('"model_usage",', source)

    def test_serializer_exposes_model_usage(self):
        from zango.api.platform.agent_mode.v1.serializers import (
            AgentRunDetailSerializer,
        )

        self.assertIn("model_usage", AgentRunDetailSerializer.Meta.fields)
