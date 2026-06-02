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
    try:
        name = getattr(task, "name", "") or ""
        if _should_skip(name):
            return
        # The proxy uses the level (INFO / ERROR) configured on the
        # underlying _Proxy instances at install() time. Logger names
        # below are what shows up under `name` in the verbose format.
        stdout_token = stdout_proxy.bind("celery.task.stdout")
        stderr_token = stdout_proxy.bind("celery.task.stderr")
        _tokens[task_id] = (stdout_token, stderr_token)
    except Exception:
        logger.exception(
            "platform_logs: failed to install stdout proxy for celery task"
        )


@task_postrun.connect
def _restore(task_id=None, **kwargs):
    pair = _tokens.pop(task_id, None)
    if pair is None:
        return
    try:
        for token in pair:
            stdout_proxy.reset(token)
    except Exception:
        logger.exception(
            "platform_logs: failed to reset stdout proxy after celery task"
        )
