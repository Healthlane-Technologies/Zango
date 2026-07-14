"""Celery task that materialises an ExportJob into a CSV in tenant storage."""

from __future__ import annotations

import logging
import os
import tempfile

from celery import shared_task

from django.core.files import File
from django.db import connection
from django.utils import timezone

from zango.apps.exports.builders import get_builder
from zango.apps.exports.models import ExportJob, ExportStatus
from zango.apps.shared.tenancy.models import TenantModel


log = logging.getLogger(__name__)


@shared_task(bind=True, name="zango.exports.run_export")
def run_export(self, tenant_name: str, job_uuid: str) -> dict:
    """Build the CSV for a single ExportJob row and attach it to `file`.

    The pre-count and rate-limit checks live in the API view; this task
    trusts them and just does the write. Any exception is captured on the
    row as `error_message` with `status=failed`.
    """
    tenant = TenantModel.objects.get(name=tenant_name)
    connection.set_tenant(tenant)

    try:
        job = ExportJob.objects.get(object_uuid=job_uuid)
    except ExportJob.DoesNotExist:
        log.error("exports: job %s not found on tenant %s", job_uuid, tenant_name)
        return {"status": "error", "reason": "job_not_found"}

    job.status = ExportStatus.RUNNING
    job.started_at = timezone.now()
    job.celery_task_id = (self.request.id or "")[:64]
    job.save(update_fields=["status", "started_at", "celery_task_id", "modified_at"])

    tmp_path = None
    try:
        builder = get_builder(job.kind)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
        ) as tmp:
            tmp_path = tmp.name
            row_count = builder.write_csv(job.filters or {}, tenant, tmp)

        filename = f"{job.kind}-{timezone.now():%Y%m%d-%H%M%S}.csv"
        with open(tmp_path, "rb") as fp:
            job.file.save(filename, File(fp), save=False)

        job.filename = filename
        job.row_count = row_count
        try:
            job.size_bytes = job.file.size
        except Exception:  # noqa: BLE001
            job.size_bytes = os.path.getsize(tmp_path)
        job.status = ExportStatus.SUCCESS
    except Exception as exc:  # noqa: BLE001
        log.exception("exports: job %s failed", job_uuid)
        job.status = ExportStatus.FAILED
        job.error_message = str(exc)[:2000]
    finally:
        job.completed_at = timezone.now()
        job.save()
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return {"status": job.status, "row_count": job.row_count or 0}
