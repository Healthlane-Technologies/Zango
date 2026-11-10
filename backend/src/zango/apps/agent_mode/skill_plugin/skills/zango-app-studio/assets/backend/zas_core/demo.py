"""
Helpers for backend/demo_data.py (open mode: the prototype's sample records, loaded by the platform
outside any request).

A plain save() there loses what the loader sets: zango's pre_save signal writes created_by from the
request user (none here) and created_at is auto_now_add. And the workflow engine reads exactly one
WorkflowState per record; a second one breaks every list and 360 that shows the record's status.

    from .zas_core import demo

    rx = Prescription(...); rx.save()
    demo.stamp(rx, created_by=users["Intake Associate"], days_ago=3)   # after the last save()
    demo.set_status(case, "pending_approval")
    demo.set_status(case, "approved", actor=sup, name="approve", data={"form_data": {"decision_note": "OK"}})
"""
import datetime

from django.utils import timezone


def _wf():
    from ...packages.workflow.base.models import WorkflowState, WorkflowTransaction
    return WorkflowState, WorkflowTransaction


def set_status(obj, status, actor=None, name=None, data=None, from_state=None):
    """Move `obj` to `status`: one history row per call, and the record's single current-state row
    points at it (made on the first call, updated after). Call it once per step of the history."""
    WorkflowState, WorkflowTransaction = _wf()
    cur = WorkflowState.objects.filter(obj_uuid=obj.object_uuid).order_by("id")
    prev = cur.first()
    tx = WorkflowTransaction.objects.create(
        obj_uuid=obj.object_uuid, transition_name=name or status, transition_type="status",
        from_state=from_state if from_state is not None else (prev.current_state if prev else ""),
        to_state=status, actor=actor, data=data)
    if prev is None:
        WorkflowState.objects.create(obj_uuid=obj.object_uuid, transaction=tx, current_state=status)
    else:
        cur.exclude(pk=prev.pk).delete()
        WorkflowState.objects.filter(pk=prev.pk).update(transaction=tx, current_state=status)
    return tx


def stamp(obj, created_by=None, days_ago=None):
    """Set the owner and the age a save() would overwrite. Call after the record's last save()."""
    vals = {}
    if created_by is not None:
        vals["created_by"] = created_by
    if days_ago is not None:
        vals["created_at"] = timezone.now() - datetime.timedelta(days=days_ago)
    if vals:
        type(obj).objects.filter(pk=obj.pk).update(**vals)
        for k, v in vals.items():
            setattr(obj, k, v)
    return obj


def check():
    """Problems the loader left: records with more than one current-state row. [] when clean."""
    from django.db.models import Count

    WorkflowState, _ = _wf()
    dupes = (WorkflowState.objects.values("obj_uuid").annotate(n=Count("id")).filter(n__gt=1)
             .values_list("obj_uuid", "n"))
    return [f"record {u} has {n} workflow states (one per record: use zas_core.demo.set_status)" for u, n in dupes]
