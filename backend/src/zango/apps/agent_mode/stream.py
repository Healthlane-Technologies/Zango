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

# Bounded so a chatty agent cannot balloon worker memory. The consumer
# batches its inserts, so blocking here is rare.
DEFAULT_QUEUE_MAX = 2_000
DEFAULT_POLL_TIMEOUT = 0.25


@dataclass
class StreamItem:
    """One item from the pump.

    kind:
      "message" -> payload is an SDK message object
      "hook"    -> payload is a dict describing a hook denial
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
                async for message in client.receive_response():
                    self._q.put(StreamItem("message", message))
                    if self.cancel.is_set():
                        with contextlib.suppress(Exception):
                            await client.interrupt()
                        break

        try:
            # A fresh event loop per run, closed on exit. Correct under a
            # prefork Celery child; never reuse a module-level loop.
            asyncio.run(main())
            self._q.put(StreamItem("done"))
        except BaseException as exc:  # noqa: BLE001 - reported, not raised
            logger.exception("agent_mode: SDK stream failed")
            with contextlib.suppress(Exception):
                self._q.put(StreamItem("error", exc))
