from django.db import models

from zango.apps.auditlogs.registry import auditlog
from zango.core.model_mixins import FullAuditMixin


class AppRelease(FullAuditMixin):
    STATUS_CHOICES = [
        ("initiated", "Initiated"),
        ("in_progress", "In Progress"),
        ("released", "Released"),
        ("failed", "Failed"),
        ("archived", "Archived"),
    ]

    version = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="initiated"
    )
    last_git_hash = models.CharField(max_length=40, null=True, blank=True)
    release_result = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Release {self.version}"


auditlog.register(AppRelease)
