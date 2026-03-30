"""
Tool confirmation model for pause/resume flow.
"""

from django.db import models
from django.utils import timezone as tz

from zango.core.model_mixins import FullAuditMixin


class AppLLMToolConfirmation(FullAuditMixin):
    """
    Created when a tool with requires_confirmation=True is invoked.
    Stores pipeline state so the agent can resume after the decision.
    """

    STATUS_CHOICES = [
        ("pending", "Awaiting decision"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("auto_approved", "Auto-approved"),
        ("auto_approved_by_policy", "Auto-approved by policy"),
        ("expired", "Expired"),
    ]

    invocation = models.ForeignKey(
        "ai.AppLLMInvocation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="confirmations",
    )
    tool = models.ForeignKey(
        "ai.AppLLMTool", on_delete=models.SET_NULL, null=True
    )
    tool_name = models.CharField(max_length=100)
    tool_input = models.JSONField()
    tool_input_display = models.TextField(blank=True, default="")
    pipeline_state = models.JSONField(default=dict)
    round_number = models.IntegerField(default=1)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    decided_by_user = models.CharField(max_length=255, blank=True, default="")
    decided_by_policy = models.CharField(max_length=200, blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)
    denial_reason = models.TextField(blank=True, default="")

    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self):
        return f"Confirmation for {self.tool_name} ({self.status})"

    @property
    def is_expired(self):
        return self.expires_at < tz.now()

    @property
    def seconds_remaining(self):
        delta = self.expires_at - tz.now()
        return max(0, int(delta.total_seconds()))
