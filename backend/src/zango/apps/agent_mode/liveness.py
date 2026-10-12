"""Closing a stopped run that no worker is going to finish.

Stopping a run is cooperative: the API sets ``abort_requested`` and the worker
that holds the run notices, interrupts the agent and finalises it. When that
worker is gone — restarted or killed mid-run — nobody notices, and the run
would sit "stopping" until the five-minute sweep's much longer cutoff.

So a stop that has gone unanswered for ``STOP_GRACE_SECONDS`` is checked
against the workers themselves, and the run is closed here when none of them
is executing its task.
"""

from __future__ import annotations

import logging

from datetime import timedelta

from django.utils import timezone


logger = logging.getLogger("zango.agent_mode")

# A live worker answers a stop within the stream's own grace period (20 s)
# plus its wrap-up; past this the run is checked against the workers.
STOP_GRACE_SECONDS = 45
# With the broker unreachable there is nothing to ask; wait this long instead.
STOP_BLIND_SECONDS = 300


def task_is_held(task_id: str) -> bool | None:
    """Is a worker executing ``task_id``?  None when the workers can't be asked.

    Asked more than once and the answers pooled: replies are keyed by node
    name, so workers started without a distinct ``-n`` overwrite each other
    and a single poll can miss the one holding the task.
    """
    if not task_id:
        return False
    try:
        from zango.config.celery import app as celery_app
    except Exception:  # noqa: BLE001
        return None
    answered = False
    for timeout in (0.6, 1.0, 1.0):
        try:
            inspect = celery_app.control.inspect(timeout=timeout)
            replies = [inspect.active(), inspect.reserved()]
        except Exception:  # noqa: BLE001
            return None
        for reply in replies:
            if reply is None:
                continue
            answered = True
            for tasks in reply.values():
                if any((t or {}).get("id") == task_id for t in tasks or []):
                    return True
    # Nobody answering at all means no worker is up, so none holds the task —
    # unless the broker itself is down, which raises above.
    return False if answered or _broker_reachable(celery_app) else None


def _broker_reachable(celery_app) -> bool:
    try:
        with celery_app.connection_for_read() as conn:
            conn.ensure_connection(max_retries=1, timeout=1)
        return True
    except Exception:  # noqa: BLE001
        return False


def close_if_abandoned(run, *, now=None) -> bool:
    """Finalise a run whose stop nobody is answering. True when it was closed."""
    from .models import ACTIVE_STATUSES, AgentRun, RunStatus

    if not run.abort_requested or run.status not in ACTIVE_STATUSES:
        return False
    now = now or timezone.now()
    quiet_for = now - run.modified_at
    if quiet_for < timedelta(seconds=STOP_GRACE_SECONDS):
        return False
    held = task_is_held(run.celery_task_id)
    if held or (held is None and quiet_for < timedelta(seconds=STOP_BLIND_SECONDS)):
        return False

    # Re-read under the same condition: a worker may have finished it meanwhile.
    fresh = AgentRun.objects.filter(
        pk=run.pk, abort_requested=True, status__in=list(ACTIVE_STATUSES)
    ).first()
    if fresh is None:
        run.refresh_from_db()
        return False
    fresh.finalize(
        RunStatus.ABORTED,
        error_type="AbortedWorkerLost",
        error_message=(
            "Stopped. The worker that was running this build is no longer "
            "running it (it was restarted or exited), so the build was closed "
            "without its wrap-up steps. Files it had already written remain "
            "in the workspace."
        ),
    )
    _note(fresh, "Stopped — no worker was running this build any more.")
    run.refresh_from_db()
    logger.warning("agent_mode: closed abandoned run %s after an unanswered stop", run.pk)
    return True


def _note(run, message: str) -> None:
    from .models import AgentRunEvent

    try:
        last = (
            AgentRunEvent.objects.filter(run_id=run.id)
            .order_by("-seq")
            .values_list("seq", flat=True)
            .first()
        )
        AgentRunEvent.objects.create(
            run=run, seq=(last or 0) + 1, kind="sys", level="warn", message=message
        )
    except Exception:  # noqa: BLE001
        logger.exception("agent_mode: failed to record the stop note")
