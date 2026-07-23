"""Models for the Exports feature.

A single `ExportJob` row per user-requested CSV export. Four discriminator
values on `kind` cover App Users, Access Logs, Application Audit Logs, and
Framework Audit Logs — each with a dedicated builder in `builders.py`.
"""

from __future__ import annotations

import uuid

from django.db import models

from zango.core.model_mixins import FullAuditMixin
from zango.core.storage_utils import ZFileField


# Hard cap enforced pre-dispatch. Locked in the plan.
MAX_EXPORT_ROWS = 30_000


class ExportKind(models.TextChoices):
    APP_USERS = "app_users", "App Users"
    ACCESS_LOGS = "access_logs", "Access Logs"
    AUDIT_LOGS_APP = "audit_logs_app", "Application Audit Logs"
    AUDIT_LOGS_FRAMEWORK = "audit_logs_framework", "Framework Audit Logs"


class ExportStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


ACTIVE_STATUSES = frozenset({ExportStatus.QUEUED, ExportStatus.RUNNING})
TERMINAL_STATUSES = frozenset({ExportStatus.SUCCESS, ExportStatus.FAILED})


class ExportJob(FullAuditMixin):
    """A user-requested CSV export of one of the platform list surfaces."""

    object_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False
    )
    kind = models.CharField(max_length=32, choices=ExportKind.choices)
    status = models.CharField(
        max_length=16,
        choices=ExportStatus.choices,
        default=ExportStatus.QUEUED,
        db_index=True,
    )

    # Full filter payload captured at request time. Used by the celery builder
    # to reconstruct the queryset AND rendered on My Downloads.
    filters = models.JSONField(default=dict, blank=True)
    # Server-built one-line summary of `filters` for the UI.
    filters_summary = models.CharField(max_length=512, blank=True, default="")

    row_count = models.PositiveIntegerField(null=True, blank=True)
    file = ZFileField(null=True, blank=True)
    filename = models.CharField(max_length=256, blank=True, default="")
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True)

    error_message = models.TextField(blank=True, default="")
    celery_task_id = models.CharField(max_length=64, blank=True, default="")

    requested_by = models.ForeignKey(
        "platformauth.PlatformUserModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "exports_job"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["requested_by", "-created_at"]),
            models.Index(fields=["kind", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind}/{self.object_uuid}"
