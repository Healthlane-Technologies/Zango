"""Stopping a build.

Regression: Stop only took effect when the agent next sent a message, so a
build in a long tool call or subagent kept going; and a build whose worker
had been restarted stayed "stopping" with nobody left to finish it.
"""

import asyncio
import sys
import threading
import time
import types
import unittest

from datetime import timedelta
from unittest import mock

from django.utils import timezone

from zango.apps.agent_mode import liveness, stream
from zango.apps.agent_mode.models import AgentRun, RunStatus


class _SilentClient:
    """An SDK client that sends one message, then nothing until interrupted."""

    instances = []

    def __init__(self, options=None):
        self.interrupted = asyncio.Event()
        self.interrupts = 0
        self.ends_on_interrupt = True
        _SilentClient.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def query(self, prompt):
        pass

    async def interrupt(self):
        self.interrupts += 1
        self.interrupted.set()

    async def receive_response(self):
        yield "first"
        await self.interrupted.wait()
        if not self.ends_on_interrupt:
            await asyncio.sleep(3600)
        yield "result"


class _DeafClient(_SilentClient):
    def __init__(self, options=None):
        super().__init__(options)
        self.ends_on_interrupt = False


def _collect(agent_stream, stop_after: float):
    """Iterate the stream on this thread, asking it to stop after a delay."""
    threading.Timer(stop_after, agent_stream.request_stop).start()
    started = time.monotonic()
    items = [item for item in agent_stream if item.kind != "idle"]
    return items, time.monotonic() - started


class StopInterruptsASilentAgentTests(unittest.TestCase):
    def _sdk(self, client):
        _SilentClient.instances.clear()
        return mock.patch.dict(
            sys.modules, {"claude_agent_sdk": types.SimpleNamespace(ClaudeSDKClient=client)}
        )

    def test_stop_lands_while_no_message_is_arriving(self):
        with self._sdk(_SilentClient):
            items, took = _collect(stream.AgentStream(None, "build"), stop_after=0.3)
        self.assertEqual([i.payload for i in items if i.kind == "message"], ["first", "result"])
        self.assertEqual(items[-1].kind, "done")
        self.assertEqual(_SilentClient.instances[0].interrupts, 1)
        self.assertLess(took, 3)

    def test_an_agent_that_ignores_the_interrupt_is_left_after_the_grace(self):
        with self._sdk(_DeafClient), mock.patch.object(stream, "STOP_GRACE_SECONDS", 0.5):
            items, took = _collect(stream.AgentStream(None, "build"), stop_after=0.2)
        self.assertEqual(items[-1].kind, "done")
        self.assertEqual(_SilentClient.instances[0].interrupts, 1)
        self.assertLess(took, 5)

    def test_a_stream_nobody_stops_runs_to_its_end(self):
        class Finishing(_SilentClient):
            async def receive_response(self):
                yield "first"
                yield "result"

        with self._sdk(Finishing):
            items = [i for i in stream.AgentStream(None, "build") if i.kind != "idle"]
        self.assertEqual([i.kind for i in items], ["message", "message", "done"])
        self.assertEqual(_SilentClient.instances[0].interrupts, 0)


def _run(**over):
    run = mock.Mock(spec=["pk", "id", "status", "abort_requested", "modified_at",
                          "celery_task_id", "refresh_from_db", "finalize"])
    run.pk = run.id = 7
    run.status = RunStatus.RUNNING
    run.abort_requested = True
    run.modified_at = timezone.now() - timedelta(minutes=2)
    run.celery_task_id = "task-1"
    for key, value in over.items():
        setattr(run, key, value)
    return run


class AbandonedStopTests(unittest.TestCase):
    def _close(self, run, held):
        manager = mock.Mock()
        manager.filter.return_value.first.return_value = run
        with mock.patch.object(liveness, "task_is_held", return_value=held) as asked, \
                mock.patch.object(AgentRun, "objects", manager), \
                mock.patch.object(liveness, "_note"):
            return liveness.close_if_abandoned(run), asked

    def test_a_stopped_run_with_no_worker_is_closed(self):
        run = _run()
        closed, _ = self._close(run, held=False)
        self.assertTrue(closed)
        status, = run.finalize.call_args.args
        self.assertEqual(status, RunStatus.ABORTED)
        self.assertEqual(run.finalize.call_args.kwargs["error_type"], "AbortedWorkerLost")

    def test_a_run_a_worker_still_holds_is_left_to_it(self):
        run = _run()
        closed, _ = self._close(run, held=True)
        self.assertFalse(closed)
        run.finalize.assert_not_called()

    def test_a_fresh_stop_is_given_time_before_anyone_is_asked(self):
        run = _run(modified_at=timezone.now() - timedelta(seconds=5))
        closed, asked = self._close(run, held=False)
        self.assertFalse(closed)
        asked.assert_not_called()

    def test_a_run_nobody_stopped_is_never_closed(self):
        for run in (_run(abort_requested=False), _run(status=RunStatus.WAITING),
                    _run(status=RunStatus.SUCCESS)):
            closed, asked = self._close(run, held=False)
            self.assertFalse(closed)
            asked.assert_not_called()

    def test_an_unreachable_broker_waits_longer_then_closes(self):
        closed, _ = self._close(_run(), held=None)
        self.assertFalse(closed)
        late = _run(modified_at=timezone.now() - timedelta(minutes=10))
        closed, _ = self._close(late, held=None)
        self.assertTrue(closed)


class TaskIsHeldTests(unittest.TestCase):
    def _ask(self, active, reserved=None):
        inspect = mock.Mock()
        inspect.active.return_value = active
        inspect.reserved.return_value = reserved
        app = mock.Mock()
        app.control.inspect.return_value = inspect
        module = types.SimpleNamespace(app=app)
        with mock.patch.dict(sys.modules, {"zango.config.celery": module}), \
                mock.patch.object(liveness, "_broker_reachable", return_value=True):
            return liveness.task_is_held("task-1")

    def test_a_worker_executing_the_task_holds_it(self):
        self.assertTrue(self._ask({"celery@host": [{"id": "task-1"}]}))

    def test_workers_busy_with_other_tasks_do_not(self):
        self.assertFalse(self._ask({"celery@host": [{"id": "other"}]}, {"celery@host": []}))

    def test_no_worker_answering_means_nobody_holds_it(self):
        self.assertFalse(self._ask(None))

    def test_a_run_that_never_reached_a_worker_is_not_held(self):
        self.assertFalse(liveness.task_is_held(""))


if __name__ == "__main__":
    unittest.main()
