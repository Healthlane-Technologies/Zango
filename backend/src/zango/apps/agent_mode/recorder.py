"""Batched, fail-open persistence of run events.

Descendant of ``code_execution``'s ``LineLogger``, with two differences:

* a **time-based flush** in addition to the size-based one. An agent can sit
  inside a single tool call for 30s; a purely size-based batch would stall
  the live transcript the panel is polling.
* every message and every string leaf of ``data`` passes through
  ``credentials.redact`` before it is buffered.

Writes are autocommitted (deliberately *not* wrapped in ``atomic()``) so the
tail endpoint sees rows while the run is still going, and every database
error is swallowed — losing an event must never kill a 12-minute run.

Called only from the Celery main thread, which owns the tenant-bound
connection. The SDK pump thread must never call this directly.
"""

from __future__ import annotations

import json
import logging
import time

from .credentials import redact, redact_obj
from .models import AgentRunEvent, EventKind, EventLevel, RunPhase


logger = logging.getLogger("zango.agent_mode")

BATCH_SIZE = 8
FLUSH_INTERVAL_SECONDS = 1.0
MESSAGE_CAP = 8_000
DATA_CAP = 32_000


def _cap(text: str, limit: int) -> str:
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n… [truncated, {len(text)} chars total]"


def _cap_data(data):
    """Bound the JSON payload. A Read of a large file must not bloat the table."""
    if data is None:
        return None
    try:
        encoded = json.dumps(data, default=str)
    except Exception:  # noqa: BLE001
        return {"_unserializable": True}
    if len(encoded) <= DATA_CAP:
        return json.loads(encoded)
    return {"_truncated": True, "_bytes": len(encoded), "preview": encoded[:2_000]}


class EventRecorder:
    """Accumulates AgentRunEvent rows and flushes them in batches."""

    def __init__(self, run, batch_size: int = BATCH_SIZE, start_seq: int | None = None):
        self._run = run
        # Stamped onto every event so the panel can group without re-deriving.
        self.phase = RunPhase.PREPARING
        self._batch_size = batch_size
        self._buffer: list[AgentRunEvent] = []
        self._seq = start_seq if start_seq is not None else 0
        self._last_flush = time.monotonic()
        self.dropped = 0

    # -- writing ---------------------------------------------------------

    def emit(
        self,
        kind: str,
        message: str = "",
        *,
        level: str = EventLevel.INFO,
        tool_name: str = "",
        tool_use_id: str = "",
        parent_tool_use_id: str = "",
        is_error: bool = False,
        data=None,
    ) -> int:
        """Buffer one event. Returns its seq. Never raises."""
        self._seq += 1
        try:
            self._buffer.append(
                AgentRunEvent(
                    run=self._run,
                    seq=self._seq,
                    kind=kind,
                    phase=self.phase,
                    level=level,
                    message=_cap(redact(message or ""), MESSAGE_CAP),
                    tool_name=(tool_name or "")[:64],
                    tool_use_id=(tool_use_id or "")[:64],
                    parent_tool_use_id=(parent_tool_use_id or "")[:64],
                    is_error=bool(is_error),
                    data=_cap_data(redact_obj(data)) if data is not None else None,
                )
            )
        except Exception:  # noqa: BLE001
            self.dropped += 1
            logger.exception("agent_mode: failed to buffer event")
            return self._seq

        if len(self._buffer) >= self._batch_size:
            self.flush()
        return self._seq

    def emit_stderr(self, line: str) -> None:
        """Sink for ClaudeAgentOptions.stderr."""
        text = (line or "").strip()
        if text:
            self.emit(EventKind.STDERR, text, level=EventLevel.WARN)

    # -- flushing --------------------------------------------------------

    def flush(self) -> int:
        """Write buffered rows. Never raises. Returns rows written."""
        if not self._buffer:
            self._last_flush = time.monotonic()
            return 0
        pending, self._buffer = self._buffer, []
        try:
            AgentRunEvent.objects.bulk_create(pending)
            return len(pending)
        except Exception:  # noqa: BLE001 - a logging failure must not kill the run
            self.dropped += len(pending)
            logger.exception("agent_mode: failed to flush %d events", len(pending))
            return 0
        finally:
            self._last_flush = time.monotonic()

    def flush_if_stale(self, max_age: float = FLUSH_INTERVAL_SECONDS) -> int:
        """Flush when the buffer has been sitting too long — keeps the live
        transcript moving during a long-running tool call."""
        if self._buffer and (time.monotonic() - self._last_flush) >= max_age:
            return self.flush()
        return 0

    def set_phase(self, phase: str) -> None:
        """Advance the run phase. Flushes first so the boundary is exact."""
        if phase != self.phase:
            self.flush()
            self.phase = phase

    @property
    def seq(self) -> int:
        return self._seq

    def __enter__(self) -> "EventRecorder":
        return self

    def __exit__(self, *exc) -> None:
        self.flush()
