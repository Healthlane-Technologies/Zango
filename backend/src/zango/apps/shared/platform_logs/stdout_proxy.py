"""Thread-aware stdout / stderr proxy that forwards writes to a logger
when a `bind()` is active for the current execution context.

Motivation: workspace devs use `print()` liberally in views and Celery
tasks. Direct stdout writes bypass Python's logging system entirely —
no formatter runs, no `tenant_filter` decorates, and CloudWatch only
ever sees the raw text without the `[<schema>:<domain>]` prefix the
Platform Logs connector relies on to scope per-tenant.

This module installs `sys.stdout` / `sys.stderr` proxies **once** at
app startup. Each proxy reads a `ContextVar` on every `write()`. When
a request handler (gunicorn middleware) or celery task hook calls
`bind(logger_name)` at the entry of its scope and `reset(token)` at
exit, every write inside that scope is forwarded as a `logger.log()`
call — and naturally inherits the verbose formatter + tenant filter
configured on the console handler.

ContextVar is per-execution-context (per-thread AND per-async task)
so the swap is safe under thread-based and async gunicorn workers.
Threads with no binding (boot, mgmt commands, background workers
without our hook) fall through to the real stream untouched.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Optional


# Set by middleware (RequestPrintCaptureMiddleware) and the celery
# print-capture hooks. None = no active scope; writes pass through.
_active: ContextVar[Optional[str]] = ContextVar(
    "platform_logs_stdout_target", default=None
)

# Reentrancy guard: when the proxy's own `log.log(...)` call triggers a
# console handler that writes back to sys.stdout/stderr (i.e. this proxy),
# we must NOT re-forward. Otherwise every emitted line feeds itself an
# infinite chain of records. ContextVar so the guard is per-thread / per-task.
_emitting: ContextVar[bool] = ContextVar(
    "platform_logs_stdout_emitting", default=False
)


class _Proxy:
    """File-like that forwards line-buffered writes to a logger if a
    target is bound in this execution context, otherwise to the real
    underlying stream.
    """

    def __init__(self, fallback, default_level: int):
        self._fallback = fallback
        self._default_level = default_level
        self._buf: list[str] = []

    def write(self, s):
        target = _active.get()
        # Always preserve the raw write so terminals, tail -f on
        # container fds, and any tooling watching real stdout still
        # see the output.
        try:
            n = self._fallback.write(s)
        except Exception:
            n = len(s)

        # If we're already inside a forwarded emission (the proxy's own
        # log.log() call is being handled by a console handler that writes
        # back to us), pass through without re-forwarding. Without this
        # guard every emit feeds itself.
        if _emitting.get():
            return n

        if target is not None and isinstance(s, str) and s:
            self._buf.append(s)
            if "\n" in s:
                full = "".join(self._buf)
                self._buf.clear()
                log = logging.getLogger(target)
                token = _emitting.set(True)
                try:
                    for line in full.splitlines():
                        if line:
                            log.log(self._default_level, line)
                finally:
                    _emitting.reset(token)
        return n

    def flush(self):
        try:
            return self._fallback.flush()
        except Exception:
            return None

    def isatty(self):
        try:
            return self._fallback.isatty()
        except Exception:
            return False

    def __getattr__(self, item):
        # Pass through any attribute we don't override (e.g. .encoding,
        # .fileno, .buffer, ...) so libraries probing the stream see
        # the real underlying handle.
        return getattr(self._fallback, item)


def install() -> None:
    """Wrap `sys.stdout` and `sys.stderr` with proxies, once. Idempotent —
    safe to call multiple times from different ready() paths."""
    if not isinstance(sys.stdout, _Proxy):
        sys.stdout = _Proxy(sys.stdout, logging.INFO)
    if not isinstance(sys.stderr, _Proxy):
        sys.stderr = _Proxy(sys.stderr, logging.ERROR)


def bind(logger_name: str):
    """Start capturing prints in the current execution context.

    Returns a Token suitable for `reset(token)` once the scope ends.
    Always call reset in a `finally` block to avoid leaking bindings
    across requests / tasks.
    """
    return _active.set(logger_name)


def reset(token) -> None:
    """Drop the capture binding established by a previous `bind()`."""
    try:
        _active.reset(token)
    except (LookupError, ValueError):
        # Token was already consumed or belongs to a different context;
        # safe to ignore — the binding wouldn't apply anyway.
        pass


def is_active() -> bool:
    """Whether a scope is currently capturing in this execution context."""
    return _active.get() is not None
