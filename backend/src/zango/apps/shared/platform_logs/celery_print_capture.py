"""Bind the stdout/stderr proxy for the duration of every Celery task.

A `task_prerun` signal calls `stdout_proxy.bind(...)` so subsequent
`print()` writes from workspace task code travel through a logger
(picking up the verbose formatter + tenant_filter on the console
handler). A `task_postrun` signal calls `stdout_proxy.reset(token)` to
end the scope.

Why this isn't the codexec executor's job:
- The codexec executor already swaps stdout/stderr with its own
  CapturingStream that fans every line into a per-execution log table.
  Doubling that with our proxy would be a no-op at best (since codexec
  saves the real stdout before swapping) but is conceptually noisy.
- We skip tasks whose names start with `zango.code_execution.` so the
  executor stays the single owner of its stdout swap.
"""

from __future__ import annotations

import logging

from celery.signals import task_postrun, task_prerun

from zango.apps.shared.platform_logs import stdout_proxy


logger = logging.getLogger(__name__)

# Task name prefixes that own their own stdout handling.
_SKIP_PREFIXES = ("zango.code_execution.",)

# task_id → (stdout_token, stderr_token)
_tokens: dict = {}


def _should_skip(task_name: str) -> bool:
    return bool(task_name) and any(task_name.startswith(p) for p in _SKIP_PREFIXES)


@task_prerun.connect
def _capture(task_id=None, task=None, **kwargs):
    name = getattr(task, "name", "") or ""
    if _should_skip(name):
        return
    # Without a task_id we have no way to look the tokens back up at
    # task_postrun — and using a falsy sentinel as a dict key would let
    # multiple concurrent anonymous tasks collide on the same slot,
    # leaking ContextVar bindings. Skip the install in that case;
    # callers without an id can't be reliably cleaned up.
    if not task_id:
        return
    # Bind each stream to its own ContextVar via the stream-specific
    # helpers — a shared bind() would let the second call clobber the
    # first. Stage the partial state in `_tokens` between the two
    # bind() calls so a failure in the second still leaves the first
    # token recoverable in _restore.
    stdout_token = None
    stderr_token = None
    try:
        stdout_token = stdout_proxy.bind_stdout("celery.task.stdout")
        _tokens[task_id] = (stdout_token, None)
        stderr_token = stdout_proxy.bind_stderr("celery.task.stderr")
        _tokens[task_id] = (stdout_token, stderr_token)
    except Exception:
        logger.exception(
            "platform_logs: failed to install stdout proxy for celery task"
        )


@task_postrun.connect
def _restore(task_id=None, **kwargs):
    if not task_id:
        return
    pair = _tokens.pop(task_id, None)
    if pair is None:
        return
    stdout_token, stderr_token = pair
    # Reset each in its own try/finally so a failure on stderr still
    # clears stdout (or vice versa) — neither binding gets stuck.
    try:
        if stderr_token is not None:
            try:
                stdout_proxy.reset_stderr(stderr_token)
            except Exception:
                logger.exception(
                    "platform_logs: failed to reset stderr proxy after celery task"
                )
    finally:
        if stdout_token is not None:
            try:
                stdout_proxy.reset_stdout(stdout_token)
            except Exception:
                logger.exception(
                    "platform_logs: failed to reset stdout proxy after celery task"
                )
