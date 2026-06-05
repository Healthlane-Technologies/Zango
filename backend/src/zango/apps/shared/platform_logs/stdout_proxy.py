"""Thread-aware stdout / stderr proxy that forwards writes to loguru
when a `bind()` is active for the current execution context.

Motivation: workspace devs use `print()` liberally in views and Celery
tasks. Direct stdout writes bypass the logging system entirely — no
formatter runs, no tenant context attaches, and CloudWatch only sees
the raw text without the `[<schema>:<domain>]` prefix the Platform
Logs connector relies on to scope per-tenant.

Loguru is the project's standard logging library (workspace code is
told to use `from loguru import logger; logger.info(...)`). Routing
captured prints through loguru rather than stdlib `logging` keeps a
stray `print()` shape-identical in CloudWatch to a deliberate
`logger.info()` — same format, same tenant prefix.

This module installs `sys.stdout` / `sys.stderr` proxies **once** at
app startup. Each proxy reads its OWN `ContextVar` on every `write()`.
When a request handler (gunicorn middleware) or celery task hook calls
`bind_stdout(source)` / `bind_stderr(source)` at scope entry and
`reset_stdout(token)` / `reset_stderr(token)` at exit, every write
inside that scope is forwarded as `loguru.logger.bind(source=…)
.opt(depth=1).log(level, line)` — picking up loguru's configured
format (with the tenant prefix from `get_loguru_format`) and the real
caller's file/function/line via the depth shift.

ContextVar is per-execution-context (per-thread AND per-async task)
so the swap is safe under thread-based and async gunicorn workers.
Threads with no binding (boot, mgmt commands, background workers
without our hook) fall through to the real stream untouched.

Keeping a separate ContextVar per stream matters: if both proxies
shared one ContextVar, the second `bind()` call in a request would
clobber the first, and every print to stdout would be logged under
whatever source was bound for stderr.
"""

from __future__ import annotations

import sys
from contextvars import ContextVar
from typing import Optional

from loguru import logger as _loguru_logger


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


_LOGGING_PACKAGES = ("loguru", "logging")
_LOGGING_PACKAGE_PREFIXES = tuple(f"{p}." for p in _LOGGING_PACKAGES)


def _called_from_logging() -> bool:
    """True if any of the closest call frames live inside a logging package.

    Used by `_Proxy.write` to detect the case where a logging library's
    own sink is writing a formatted record back to sys.stderr. Two paths
    we need to catch:

    * **loguru** — workspace code that does `logger.error("msg")` directly.
      Loguru formats the record and its sink writes the result to stderr.
      Without this guard the proxy would re-forward that formatted text
      into loguru and trip loguru's reentrancy lock ("Could not acquire
      internal lock because it was already in use").

    * **stdlib `logging`** — workspace code (or Celery, or Django, or
      any third-party lib) that uses `logging.getLogger(...).info(...)`.
      Stdlib's StreamHandler writes the formatted line to stderr. Without
      this guard the proxy would forward it into loguru, producing a
      double-wrapped line where the caller column reads `logging:emit`
      and the original INFO record is upgraded to ERROR because it
      arrived via the stderr proxy.

    The ContextVar-based `_emitting` guard only covers the path where
    the proxy itself initiated the emit; this covers every other path
    where a logging library ends up writing to a proxied stream.

    Match is exact-or-dotted-child so we don't accidentally swallow
    writes from unrelated modules like `loggers` or `loggingconfig`.
    """
    frame = sys._getframe(2)  # skip _called_from_logging and _Proxy.write
    for _ in range(8):  # bounded — sink-to-write stack depth is short
        if frame is None:
            return False
        mod = frame.f_globals.get("__name__", "")
        if mod in _LOGGING_PACKAGES or mod.startswith(_LOGGING_PACKAGE_PREFIXES):
            return True
        frame = frame.f_back
    return False


class _Proxy:
    """File-like that forwards line-buffered writes to loguru if a target
    is bound in this execution context, otherwise to the real underlying
    stream.

    Each instance reads its own `active_var` so stdout and stderr can
    be bound to different sources without one overwriting the other.

    Loguru — not stdlib `logging` — is the project's standard logging
    library. Forwarding through loguru keeps a workspace dev's
    accidental `print("...")` shape-identical in CloudWatch to their
    deliberate `logger.info("...")`: same tenant prefix, same format,
    same caller frame columns.
    """

    def __init__(
        self,
        fallback,
        default_level_name: str,
        active_var: ContextVar,
    ):
        self._fallback = fallback
        self._default_level_name = default_level_name  # "INFO" / "ERROR"
        self._active_var = active_var
        self._buf: list[str] = []

    def write(self, s):
        # If we're already inside a forwarded emission (loguru's sink
        # writing the formatted record back to sys.stderr — which is
        # this proxy), pass through to the real stream and stop.
        # Without this guard every emit re-feeds itself.
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

        # Binding is active, but this write came from inside a logging
        # library — loguru's sink or stdlib `logging`'s StreamHandler is
        # writing a formatted record back to the proxied stream.
        # Forwarding would either trip loguru's reentrancy lock OR
        # produce a double-wrapped line whose caller column reads
        # `logging:emit`. Pass through to the real stream untouched.
        if _called_from_logging():
            try:
                return self._fallback.write(s)
            except Exception:
                return len(s)

        # Binding active and the write originated from non-logging code
        # (i.e. a real print). Buffer until we have a complete line, then
        # forward each line as a loguru record. We do NOT also call
        # `fallback.write` here — the forwarded record reaches the
        # stream via loguru's sink (with timestamp + tenant prefix),
        # and a raw write would produce a duplicate, unformatted line.
        self._buf.append(s)
        if "\n" in s:
            full = "".join(self._buf)
            self._buf.clear()
            token = _emitting.set(True)
            try:
                # opt(depth=1) shifts loguru's reported caller frame
                # past this method so file/function/line columns point
                # at the print() site instead of `_Proxy.write`.
                # bind(source=target) stashes the stream label
                # ("zango.request.stdout" / "celery.task.stdout" / …)
                # in `record["extra"]["source"]` so format strings can
                # surface it if needed.
                emit = _loguru_logger.bind(source=target).opt(depth=1)
                for line in full.splitlines():
                    if line:
                        emit.log(self._default_level_name, line)
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
        sys.stdout = _Proxy(sys.stdout, "INFO", _active_stdout)
    if not isinstance(sys.stderr, _Proxy):
        sys.stderr = _Proxy(sys.stderr, "ERROR", _active_stderr)


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
