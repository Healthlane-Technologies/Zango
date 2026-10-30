"""A turn that ends while background subagents still run does not end the run.

Regression (run 6): the build agent dispatched five subagents, which run in the
background, and ended its turn to wait for them. The pump stopped at that
ResultMessage and closed the client, which killed the subagents: one backend
module was left as a bare __init__.py and the bring-up failed on every policy.
The resumed fix round then closed on a 0-turn result before reading its prompt.
"""

import asyncio
import sys
import types
import unittest

from unittest import mock

from zango.apps.agent_mode import stream


def _msg(name, **fields):
    fields.setdefault("task_id", None)
    return type(name, (), fields)()


class _Client:
    """Plays ``script``: messages, or the string "nudged" to wait for a query."""

    instances = []
    script: list = []

    def __init__(self, options=None):
        self.queries = []
        self.asked = asyncio.Event()
        _Client.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def query(self, prompt):
        self.queries.append(prompt)
        if len(self.queries) > 1:
            self.asked.set()

    async def interrupt(self):
        pass

    async def receive_messages(self):
        for step in self.script:
            if step == "nudged":
                await self.asked.wait()
                self.asked.clear()
            else:
                yield step
        await asyncio.sleep(3600)  # a live session never ends by itself


def _run(script, prompt="build", end_check=None):
    _Client.instances.clear()
    client = type("C", (_Client,), {"script": script})
    sdk = types.SimpleNamespace(ClaudeSDKClient=client)
    with mock.patch.dict(sys.modules, {"claude_agent_sdk": sdk}), mock.patch.object(
        stream, "NUDGE_SECONDS", 0.2
    ):
        items = [i for i in stream.AgentStream(None, prompt, end_check=end_check) if i.kind != "idle"]
    names = [type(i.payload).__name__ for i in items if i.kind == "message"]
    return items, names, _Client.instances[0].queries


class BackgroundTasksKeepTheRunOpenTests(unittest.TestCase):
    def test_the_run_waits_for_its_subagents_then_asks_for_their_results(self):
        items, names, queries = _run(
            [
                _msg("AssistantMessage", parent_tool_use_id=None),
                _msg("TaskStartedMessage", task_id="t1", task_type="local_agent"),
                _msg("ResultMessage"),  # the turn ends; t1 still runs
                _msg("AssistantMessage", parent_tool_use_id="call-1"),  # t1 itself
                _msg("TaskNotificationMessage", task_id="t1"),
                "nudged",
                _msg("AssistantMessage", parent_tool_use_id=None),
                _msg("ResultMessage"),
            ]
        )
        self.assertEqual(names[-1], "ResultMessage")
        self.assertEqual(len(names), 7)
        self.assertEqual(items[-1].kind, "done")
        self.assertEqual(queries, ["build", stream.NUDGE_PROMPT])

    def test_no_nudge_when_the_cli_takes_the_turn_itself(self):
        _, names, queries = _run(
            [
                _msg("AssistantMessage", parent_tool_use_id=None),
                _msg("TaskStartedMessage", task_id="t1", task_type="local_agent"),
                _msg("ResultMessage"),
                _msg("TaskNotificationMessage", task_id="t1"),
                _msg("AssistantMessage", parent_tool_use_id=None),
                _msg("ResultMessage"),
            ]
        )
        self.assertEqual(len(names), 6)
        self.assertEqual(queries, ["build"])

    def test_a_background_shell_does_not_hold_the_run(self):
        _, names, queries = _run(
            [
                _msg("AssistantMessage", parent_tool_use_id=None),
                _msg("TaskStartedMessage", task_id="s1", task_type="local_bash"),
                _msg("ResultMessage"),
            ]
        )
        self.assertEqual(len(names), 3)
        self.assertEqual(queries, ["build"])

    def test_a_result_before_any_reply_resends_the_prompt_once(self):
        _, names, queries = _run(
            [
                _msg("TaskNotificationMessage", task_id="old"),
                _msg("ResultMessage", num_turns=0),
                "nudged",
                _msg("AssistantMessage", parent_tool_use_id=None),
                _msg("ResultMessage"),
            ],
            prompt="fix these",
        )
        self.assertEqual(len(names), 4)
        self.assertEqual(queries, ["fix these", "fix these"])

    def test_a_turn_with_no_background_work_ends_the_run(self):
        items, names, queries = _run(
            [_msg("AssistantMessage", parent_tool_use_id=None), _msg("ResultMessage")]
        )
        self.assertEqual(items[-1].kind, "done")
        self.assertEqual(len(names), 2)
        self.assertEqual(queries, ["build"])


class EndOfTurnCheckTests(unittest.TestCase):
    TURN = [_msg("AssistantMessage", parent_tool_use_id=None), _msg("ResultMessage")]

    def test_an_owed_message_is_sent_back_instead_of_ending_the_turn(self):
        owed = ["apply the reference", None]
        _, names, queries = _run(
            self.TURN + ["nudged"] + self.TURN, end_check=lambda: owed.pop(0)
        )
        self.assertEqual(queries, ["build", "apply the reference"])
        self.assertEqual(len(names), 4)

    def test_the_check_is_asked_at_most_twice(self):
        _, names, queries = _run(
            self.TURN + ["nudged"] + self.TURN + ["nudged"] + self.TURN,
            end_check=lambda: "still owed",
        )
        self.assertEqual(queries, ["build", "still owed", "still owed"])
        self.assertEqual(len(names), 6)

    def test_a_check_that_raises_does_not_hold_the_turn(self):
        def boom():
            raise RuntimeError("x")

        items, _, queries = _run(self.TURN, end_check=boom)
        self.assertEqual(items[-1].kind, "done")
        self.assertEqual(queries, ["build"])
