"""Mapping SDK messages to events.

Uses lightweight fakes whose CLASS NAMES match the SDK's, because
``mapper`` duck-types on them. Field names mirror
``claude_agent_sdk/types.py`` in the pinned wheel.
"""

import unittest

from zango.apps.agent_mode import mapper
from zango.apps.agent_mode.models import EventKind


# -- fakes named exactly like the SDK types ---------------------------------
class TextBlock:
    def __init__(self, text):
        self.text = text


class ThinkingBlock:
    def __init__(self, thinking):
        self.thinking = thinking


class ToolUseBlock:
    def __init__(self, id, name, input):  # noqa: A002
        self.id, self.name, self.input = id, name, input


class ToolResultBlock:
    def __init__(self, tool_use_id, content, is_error=False):
        self.tool_use_id, self.content, self.is_error = tool_use_id, content, is_error


class SystemMessage:
    def __init__(self, subtype, data):
        self.subtype, self.data = subtype, data


class AssistantMessage:
    def __init__(self, content, parent_tool_use_id=None):
        self.content, self.parent_tool_use_id = content, parent_tool_use_id


class UserMessage:
    def __init__(self, content, parent_tool_use_id=None):
        self.content, self.parent_tool_use_id = content, parent_tool_use_id


class ResultMessage:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class FakeRecorder:
    def __init__(self):
        self.events = []
        self._seq = 0

    def emit(self, kind, message="", **kw):
        self._seq += 1
        self.events.append({"seq": self._seq, "kind": kind, "message": message, **kw})
        return self._seq

    def kinds(self):
        return [e["kind"] for e in self.events]


class MapperTests(unittest.TestCase):
    def setUp(self):
        self.rec = FakeRecorder()
        self.state = {}

    def test_init_captures_session_and_skills(self):
        mapper.record_message(
            SystemMessage(
                "init",
                {
                    "session_id": "sess-1",
                    "model": "claude-x",
                    "skills": ["zango-agent-mode:zango-app-developer-server"],
                },
            ),
            self.rec,
            self.state,
        )
        self.assertEqual(self.state["session_id"], "sess-1")
        self.assertEqual(self.rec.kinds(), [EventKind.INIT])
        self.assertIn("1 skill(s)", self.rec.events[0]["message"])

    def test_system_message_has_subtype_and_data_not_content(self):
        # Regression: an earlier draft assumed SystemMessage.content.
        mapper.record_message(
            SystemMessage("compact_boundary", {"pre_tokens": 9}), self.rec, self.state
        )
        self.assertEqual(self.rec.kinds(), [EventKind.COMPACT])

    def test_assistant_blocks(self):
        mapper.record_message(
            AssistantMessage(
                [
                    TextBlock("hello"),
                    ThinkingBlock("x" * 5000),
                    ToolUseBlock(
                        "tu1",
                        "Write",
                        {"file_path": "patients/models.py", "content": "y" * 9000},
                    ),
                ]
            ),
            self.rec,
            self.state,
        )
        self.assertEqual(
            self.rec.kinds(),
            [EventKind.ASSISTANT, EventKind.THINKING, EventKind.TOOL_USE],
        )
        # thinking is capped
        self.assertLess(len(self.rec.events[1]["message"]), 2200)
        # file body is not stored
        self.assertEqual(
            self.rec.events[2]["data"]["content"], {"_omitted_chars": 9000}
        )
        self.assertEqual(self.rec.events[2]["message"], "Write patients/models.py")
        self.assertEqual(self.state["tool_use_counts"], {"Write": 1})
        self.assertIn("patients/models.py", self.state["touched_files"])

    def test_empty_text_block_is_skipped(self):
        mapper.record_message(
            AssistantMessage([TextBlock("   ")]), self.rec, self.state
        )
        self.assertEqual(self.rec.events, [])

    def test_skill_tool_use_gets_its_own_kind(self):
        mapper.record_message(
            AssistantMessage([ToolUseBlock("t", "Skill", {"name": "zango"})]),
            self.rec,
            self.state,
        )
        self.assertEqual(self.rec.kinds(), [EventKind.SKILL])

    def test_tool_result_error_flag_and_truncation(self):
        mapper.record_message(
            UserMessage([ToolResultBlock("tu1", "e" * 9000, is_error=True)]),
            self.rec,
            self.state,
        )
        ev = self.rec.events[0]
        self.assertEqual(ev["kind"], EventKind.TOOL_RESULT)
        self.assertTrue(ev["is_error"])
        self.assertLess(len(ev["message"]), 2200)
        self.assertEqual(ev["data"]["len"], 9000)

    def test_tool_result_list_content(self):
        mapper.record_message(
            UserMessage([ToolResultBlock("t", [{"type": "text", "text": "ok"}])]),
            self.rec,
            self.state,
        )
        self.assertEqual(self.rec.events[0]["message"], "ok")

    def test_result_tokens_come_from_model_usage_camelcase(self):
        # Regression: ResultMessage has no total_input_tokens/total_output_tokens.
        mapper.record_message(
            ResultMessage(
                subtype="success",
                terminal_reason="completed",
                result="done",
                num_turns=7,
                duration_api_ms=1234,
                total_cost_usd=0.4123,
                is_error=False,
                session_id="sess-9",
                api_error_status=None,
                permission_denials=[],
                model_usage={
                    "claude-a": {
                        "inputTokens": 100,
                        "outputTokens": 20,
                        "cacheReadInputTokens": 5,
                        "cacheCreationInputTokens": 3,
                    },
                    "claude-b": {
                        "inputTokens": 50,
                        "outputTokens": 10,
                        "cacheReadInputTokens": 1,
                        "cacheCreationInputTokens": 0,
                    },
                },
            ),
            self.rec,
            self.state,
        )
        self.assertEqual(self.state["input_tokens"], 150)
        self.assertEqual(self.state["output_tokens"], 30)
        self.assertEqual(self.state["cache_read_tokens"], 6)
        self.assertEqual(self.state["cache_creation_tokens"], 3)
        self.assertEqual(self.state["num_turns"], 7)
        self.assertEqual(self.state["session_id"], "sess-9")
        self.assertEqual(self.rec.kinds(), [EventKind.RESULT])

    def test_result_missing_model_usage_is_safe(self):
        mapper.record_message(
            ResultMessage(
                subtype="error_max_turns",
                is_error=True,
                model_usage=None,
                total_cost_usd=None,
                num_turns=None,
            ),
            self.rec,
            self.state,
        )
        self.assertEqual(self.state["input_tokens"], 0)
        self.assertTrue(self.rec.events[0]["is_error"])

    def test_summarize_tool_use(self):
        self.assertEqual(
            mapper.summarize_tool_use("Bash", {"command": "ls -la"}), "Bash: ls -la"
        )
        self.assertEqual(
            mapper.summarize_tool_use("Grep", {"pattern": "foo"}), "Grep 'foo'"
        )
        self.assertEqual(
            mapper.summarize_tool_use("Read", {"file_path": "a.py"}), "Read a.py"
        )

    def test_unknown_message_type_does_not_crash(self):
        class WeirdMessage:
            pass

        mapper.record_message(WeirdMessage(), self.rec, self.state)
        self.assertEqual(self.rec.kinds(), [EventKind.SYS])


if __name__ == "__main__":
    unittest.main()
