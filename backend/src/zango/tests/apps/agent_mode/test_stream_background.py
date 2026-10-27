"""A turn that ends while background subagents still run does not end the run.

Regression (run 6): the build agent dispatched five subagents, which run in the
background, and ended its turn to wait for them. The pump stopped at that
ResultMessage and closed the client, which killed the subagents: one backend
module was left as a bare __init__.py and the bring-up failed on every policy.
"""

import asyncio
import sys
import types
import unittest

from unittest import mock

from zango.apps.agent_mode import stream


def _msg(name, **fields):
    return type(name, (), fields)()


class _BackgroundClient:
    """Starts a task, ends the turn, finishes the task; then answers a nudge."""

    instances = []

    def __init__(self, options=None):
        self.queries = []
        self.nudged = asyncio.Event()
        _BackgroundClient.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def query(self, prompt):
        self.queries.append(prompt)
        if len(self.queries) > 1:
            self.nudged.set()

    async def interrupt(self):
        pass

    async def receive_messages(self):
        yield _msg("TaskStartedMessage", task_id="t1")
        yield _msg("ResultMessage", task_id=None)  # the turn ends; t1 still runs
        yield _msg("TaskNotificationMessage", task_id="t1")
        await self.nudged.wait()
        yield _msg("AssistantMessage", task_id=None)
        yield _msg("ResultMessage", task_id=None)
        await asyncio.sleep(3600)  # a live session never ends by itself


class BackgroundTasksKeepTheRunOpenTests(unittest.TestCase):
    def test_the_run_waits_for_its_subagents_then_asks_for_their_results(self):
        _BackgroundClient.instances.clear()
        sdk = types.SimpleNamespace(ClaudeSDKClient=_BackgroundClient)
        with mock.patch.dict(sys.modules, {"claude_agent_sdk": sdk}), mock.patch.object(
            stream, "NUDGE_SECONDS", 0.2
        ):
            items = [i for i in stream.AgentStream(None, "build") if i.kind != "idle"]
        names = [type(i.payload).__name__ for i in items if i.kind == "message"]
        self.assertEqual(
            names,
            [
                "TaskStartedMessage",
                "ResultMessage",
                "TaskNotificationMessage",
                "AssistantMessage",
                "ResultMessage",
            ],
        )
        self.assertEqual(items[-1].kind, "done")
        self.assertEqual(
            _BackgroundClient.instances[0].queries, ["build", stream.NUDGE_PROMPT]
        )

    def test_a_turn_with_no_background_work_ends_the_run(self):
        class _Plain(_BackgroundClient):
            async def receive_messages(self):
                yield _msg("AssistantMessage", task_id=None)
                yield _msg("ResultMessage", task_id=None)
                await asyncio.sleep(3600)

        sdk = types.SimpleNamespace(ClaudeSDKClient=_Plain)
        with mock.patch.dict(sys.modules, {"claude_agent_sdk": sdk}):
            items = [i for i in stream.AgentStream(None, "q") if i.kind != "idle"]
        self.assertEqual(items[-1].kind, "done")
        self.assertEqual(len([i for i in items if i.kind == "message"]), 2)
