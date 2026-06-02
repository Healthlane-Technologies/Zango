"""Thread-aware stdout / stderr proxy that forwards writes to a logger
when a `bind()` is active for the current execution context.

Motivation: workspace devs use `print()` liberally in views and Celery
tasks. Direct stdout writes bypass Python's logging system entirely —
no formatter runs, no `tenant_filter` decorates, and CloudWatch only
ever sees the raw text without the `[<schema>:<domain>]` prefix the
Platform Logs connector relies on to scope per-tenant.

This module installs `sys.stdout` / `sys.stderr` proxies **once** at
app startup. Each proxy reads its OWN `ContextVar` on every `write()`.
When a request handler (gunicorn middleware) or celery task hook calls
`bind_stdout(logger_name)` / `bind_stderr(logger_name)` at scope entry
and `reset_stdout(token)` / `reset_stderr(token)` at exit, every write
inside that scope is forwarded as a `logger.log()` call — and naturally
inherits the verbose formatter + tenant filter configured on the
console handler.

ContextVar is per-execution-context (per-thread AND per-async task)
so the swap is safe under thread-based and async gunicorn workers.
Threads with no binding (boot, mgmt commands, background workers
without our hook) fall through to the real stream untouched.

Keeping a separate ContextVar per stream matters: if both proxies
shared one ContextVar, the second `bind()` call in a request would
clobber the first, and every print to stdout would be logged under
whatever logger name was bound for stderr.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Optional


# One ContextVar per stream. None = no active scope; writes pass
# through to the real underlying stream.
_active_stdout: ContextVar[Optional[str]] = ContextVar(
    "platform_logs_stdout_target", default=None
)
_active_stderr: ContextVar[Optional[str]] = ContextVar(
    "platform_logs_stderr_target", default=None
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

    Each instance reads its own `active_var` so stdout and stderr can
    be bound to different loggers without one overwriting the other.
    """

    def __init__(
        self,
        fallback,
        default_level: int,
        active_var: ContextVar,
    ):
        self._fallback = fallback
        self._default_level = default_level
        self._active_var = active_var
        self._buf: list[str] = []

    def write(self, s):
        # If we're already inside a forwarded emission (the bound logger's
        # console handler is writing the formatted record back to us),
        # pass through to the real stream and stop. Without this guard
        # every emit re-feeds itself.
        if _emitting.get():
            try:
                return self._fallback.write(s)
            except Exception:
                return len(s)

        target = self._active_var.get()
        # No binding → straight passthrough.
        if target is None or not isinstance(s, str) or not s:
            try:
                return self._fallback.write(s)
            except Exception:
                return len(s)

        # Binding active. Buffer until we have a complete line, then
        # forward each line as a log record. We do NOT also `fallback.write`
        # here — the forwarded record reaches the stream via the bound
        # logger's handler (with timestamp + tenant prefix), and a raw
        # write would produce a duplicate, unformatted line.
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
        return len(s)

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
        sys.stdout = _Proxy(sys.stdout, logging.INFO, _active_stdout)
    if not isinstance(sys.stderr, _Proxy):
        sys.stderr = _Proxy(sys.stderr, logging.ERROR, _active_stderr)


def bind_stdout(logger_name: str):
    """Start capturing stdout writes in the current execution context."""
    return _active_stdout.set(logger_name)


def bind_stderr(logger_name: str):
    """Start capturing stderr writes in the current execution context."""
    return _active_stderr.set(logger_name)


def reset_stdout(token) -> None:
    """Drop the stdout binding established by a previous `bind_stdout()`."""
    try:
        _active_stdout.reset(token)
    except (LookupError, ValueError):
        # Token was already consumed or belongs to a different context;
        # safe to ignore — the binding wouldn't apply anyway.
        pass


def reset_stderr(token) -> None:
    """Drop the stderr binding established by a previous `bind_stderr()`."""
    try:
        _active_stderr.reset(token)
    except (LookupError, ValueError):
        pass


def is_active() -> bool:
    """Whether any scope is currently capturing in this execution context."""
    return _active_stdout.get() is not None or _active_stderr.get() is not None
