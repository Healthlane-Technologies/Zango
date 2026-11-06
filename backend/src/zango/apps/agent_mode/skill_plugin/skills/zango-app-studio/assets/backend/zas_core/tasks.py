"""
Background work for AI helpers (zas_core.ai). Synced as app tasks like any tasks.py.

    zas_ai_run(run_id)   one queued run (record events, schedule triggers, buttons with run: async)
    zas_ai_tick()        every minute: start the schedule triggers that are due
"""

from celery import shared_task


@shared_task
def zas_ai_run(run_id=None):
    from . import ai
    from .models import ZasAiRun

    r = ZasAiRun.objects.filter(pk=run_id).first()
    if r is None:
        return "missing"
    return ai.execute(r).status


# zas:schedule * * * * *
@shared_task
def zas_ai_tick():
    from . import ai

    if not ai.any_schedule():
        return 0
    return ai.schedule_tick()
