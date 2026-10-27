"""Bridge the SDK's async iterator to a synchronous Celery task.

This is the single most important correctness detail in Agent Mode.

The SDK's ``ClaudeSDKClient`` is async; Django's ORM raises
``SynchronousOnlyOperation`` when called from an async context. The obvious
fix — wrapping ORM writes in ``sync_to_async`` — is *wrong here*: it hops to
an asgiref executor thread holding a **different** database connection, which
is still pointed at the **public** schema. Events would be written into the
wrong tenant's schema, silently.

So the async iteration runs on a dedicated daemon thread that touches nothing
but a ``queue.Queue``. The Celery main thread — which owns the tenant-bound
connection — drains that queue and performs every ORM write.

The hooks passed in ``ClaudeAgentOptions`` also execute on this pump's loop,
so they too must stay ORM-free; they push onto the same thread-safe queue.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import queue
import threading

from dataclasses import dataclass
from typing import Any, Iterator


logger = logging.getLogger("zango.agent_mode")


def _log_auth_source(message) -> None:
    """Log which credential the CLI authenticated with, once per session.

    ``apiKeySource`` is "none" when no API key is in play, i.e. the CLI is on
    the subscription login (AGENT_MODE_AUTH=subscription); anything else
    names where the billed key came from.
    """
    if type(message).__name__ != "SystemMessage":
        return
    if getattr(message, "subtype", "") != "init":
        return
    data = getattr(message, "data", None) or {}
    logger.info(
        "agent_mode: CLI session %s auth apiKeySource=%s model=%s",
        data.get("session_id") or "?",
        data.get("apiKeySource") or "?",
        data.get("model") or "?",
    )


# Bounded so a chatty agent cannot balloon worker memory. The consumer
# batches its inserts, so blocking here is rare.
DEFAULT_QUEUE_MAX = 2_000
DEFAULT_POLL_TIMEOUT = 0.25
# How often the pump looks at the stop flag, and how long it gives an
# interrupted agent to wind down before closing the client under it.
STOP_POLL_SECONDS = 0.25
STOP_GRACE_SECONDS = 20.0
# Subagents run in the background: the parent's turn can end (a ResultMessage)
# while they still work, and closing the client then kills them. The pump holds
# the session open until they finish; if the CLI does not start a turn on their
# results by itself within NUDGE_SECONDS, it asks the agent to collect them.
# BACKGROUND_IDLE_SECONDS bounds a wait in which nothing arrives at all.
NUDGE_SECONDS = 30.0
BACKGROUND_IDLE_SECONDS = 30 * 60.0
NUDGE_PROMPT = (
    "Your background agents have finished. Collect their results, finish "
    "whatever is still left, and end only when the work is complete; do not "
    "end your turn while an agent you started is still running."
)
_TERMINAL_TASK = {"completed", "failed", "stopped", "killed"}


def _track_task(message, active: set) -> None:
    """Keep ``active`` = the ids of background tasks still running."""
    name = type(message).__name__
    task_id = getattr(message, "task_id", None)
    if not task_id:
        return
    if name == "TaskStartedMessage":
        # Subagents only ("local_agent"): a background shell such as a dev
        # server never finishes, and must not hold the run open.
        task_type = getattr(message, "task_type", None)
        if task_type is None or "agent" in task_type:
            active.add(task_id)
    elif name == "TaskNotificationMessage":
        active.discard(task_id)
    elif name == "TaskUpdatedMessage":
        status = getattr(message, "status", None) or (
            getattr(message, "patch", None) or {}
        ).get("status")
        if status in _TERMINAL_TASK:
            active.discard(task_id)


@dataclass
class StreamItem:
    """One item from the pump.

    kind:
      "message" -> payload is an SDK message object
      "hook"    -> payload is a dict describing a hook denial
      "spec"    -> payload is an accepted spec-tool edit {yaml, changed_paths, issues}
      "idle"    -> nothing arrived within the poll window (lets the consumer
                   run its periodic work, e.g. abort checks and stale flushes)
      "done"    -> the stream finished normally
      "error"   -> payload is the exception that ended the stream
    """

    kind: str
    payload: Any = None


class AgentStream:
    """Iterate SDK messages synchronously, on the caller's thread."""

    def __init__(
        self,
        options,
        prompt: str,
        *,
        cancel: threading.Event | None = None,
        queue_max: int = DEFAULT_QUEUE_MAX,
        poll_timeout: float = DEFAULT_POLL_TIMEOUT,
    ):
        self.options = options
        self.prompt = prompt
        self.cancel = cancel or threading.Event()
        self.poll_timeout = poll_timeout
        self._q: queue.Queue[StreamItem] = queue.Queue(maxsize=queue_max)
        self._thread: threading.Thread | None = None
        self._finished = False

    # -- the hook sink ---------------------------------------------------

    def hook_sink(self, tool_name: str, reason: str, tool_input: dict) -> None:
        """Thread-safe, ORM-free sink handed to the PreToolUse guard."""
        with contextlib.suppress(Exception):
            self._q.put_nowait(
                StreamItem(
                    "hook",
                    {
                        "tool_name": tool_name,
                        "reason": reason,
                        "tool_input": tool_input,
                    },
                )
            )

    def push(self, kind: str, payload: Any) -> None:
        """Thread-safe, ORM-free: hand an item to the consumer (spec tools use it)."""
        self._q.put(StreamItem(kind, payload))

    # -- iteration -------------------------------------------------------

    def __iter__(self) -> Iterator[StreamItem]:
        self._thread = threading.Thread(
            target=self._pump, name="agent-mode-pump", daemon=True
        )
        self._thread.start()

        while True:
            try:
                item = self._q.get(timeout=self.poll_timeout)
            except queue.Empty:
                # Surface an idle tick so the consumer can check the abort
                # flag and flush stale events during a long tool call.
                if self._finished:
                    return
                yield StreamItem("idle")
                continue

            if item.kind in ("done", "error"):
                self._finished = True
                yield item
                return
            yield item

    def request_stop(self) -> None:
        self.cancel.set()

    def join(self, timeout: float = 10.0) -> None:
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    # -- the pump (async, no ORM) ----------------------------------------

    def _pump(self) -> None:
        async def main() -> None:
            # Imported here so the module stays importable (and the app
            # loadable) on installs without the SDK.
            from claude_agent_sdk import ClaudeSDKClient

            async with ClaudeSDKClient(options=self.options) as client:
                await client.query(self.prompt)
                # The stop flag is watched alongside the stream, not only when
                # a message arrives: during a long tool call or a subagent the
                # SDK may send nothing for minutes, and a stop has to land then.
                # receive_messages, not receive_response: the latter stops at the
                # first ResultMessage, even while background subagents still run.
                messages = client.receive_messages().__aiter__()
                pending = asyncio.ensure_future(messages.__anext__())
                loop = asyncio.get_running_loop()
                give_up_at = None
                active: set = set()
                waiting = False  # the turn ended while subagents still ran
                nudge_at = None
                nudge = NUDGE_PROMPT
                answered = False  # the agent has said or done anything
                reprompted = False
                last_message_at = loop.time()
                try:
                    while True:
                        done, _ = await asyncio.wait(
                            {pending}, timeout=STOP_POLL_SECONDS
                        )
                        if done:
                            try:
                                message = pending.result()
                            except StopAsyncIteration:
                                break
                            _log_auth_source(message)
                            self._q.put(StreamItem("message", message))
                            pending = asyncio.ensure_future(messages.__anext__())
                            last_message_at = loop.time()
                            name = type(message).__name__
                            _track_task(message, active)
                            if name == "ResultMessage":
                                if (
                                    not answered
                                    and not reprompted
                                    and not getattr(message, "is_error", False)
                                ):
                                    # A resumed session can close a turn on its
                                    # queued task notifications (num_turns 0)
                                    # before reading the prompt: send it again.
                                    reprompted, nudge = True, self.prompt
                                    waiting, nudge_at = True, None
                                elif not active:
                                    break
                                else:
                                    waiting, nudge_at = True, None
                                    nudge = NUDGE_PROMPT
                            elif (
                                name == "AssistantMessage"
                                and getattr(message, "parent_tool_use_id", None) is None
                            ):
                                # The parent took a turn (a subagent's messages
                                # carry its Agent call's id): its result decides.
                                answered = True
                                waiting, nudge_at = False, None
                            if waiting and not active and nudge_at is None:
                                nudge_at = loop.time() + NUDGE_SECONDS
                        if (
                            waiting
                            and nudge_at is not None
                            and loop.time() >= nudge_at
                            and not self.cancel.is_set()
                        ):
                            waiting, nudge_at = False, None
                            await client.query(nudge)
                        if (
                            waiting
                            and loop.time() - last_message_at >= BACKGROUND_IDLE_SECONDS
                        ):
                            logger.warning(
                                "agent_mode: background tasks %s silent for %ss; closing",
                                sorted(active),
                                BACKGROUND_IDLE_SECONDS,
                            )
                            break
                        if not self.cancel.is_set():
                            continue
                        if give_up_at is None:
                            give_up_at = loop.time() + STOP_GRACE_SECONDS
                            with contextlib.suppress(Exception):
                                await client.interrupt()
                        elif loop.time() >= give_up_at:
                            # The agent did not wind down after the interrupt:
                            # leave it; closing the client ends its process.
                            break
                finally:
                    if not pending.done():
                        pending.cancel()
                    with contextlib.suppress(BaseException):
                        await pending

        try:
            # A fresh event loop per run, closed on exit. Correct under a
            # prefork Celery child; never reuse a module-level loop.
            asyncio.run(main())
            self._q.put(StreamItem("done"))
        except BaseException as exc:  # noqa: BLE001 - reported, not raised
            logger.exception("agent_mode: SDK stream failed")
            with contextlib.suppress(Exception):
                self._q.put(StreamItem("error", exc))
