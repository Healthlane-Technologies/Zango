"""
Database models for tool management.
AppLLMTool: DB mirror of registered @tool functions (synced from code).
AppLLMToolCall: Log entry for each tool execution within an agent invocation.
"""

from django.db import models

from zango.core.model_mixins import FullAuditMixin


class AppLLMTool(FullAuditMixin):
    """
    DB representation of a registered @tool function.
    Source of truth is CODE — DB records exist for panel visibility and tracking.
    """

    SAFETY_CHOICES = [
        ("read_only", "Read Only"),
        ("write", "Write"),
        ("external", "External"),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    section = models.CharField(max_length=50, default="general")
    parameters_schema = models.JSONField(
        help_text="JSON Schema for the tool's input parameters"
    )
    python_path = models.CharField(max_length=255)
    safety = models.CharField(max_length=20, choices=SAFETY_CHOICES, default="read_only")
    requires_confirmation = models.BooleanField(default=False)
    timeout_seconds = models.IntegerField(default=30)
    rate_limit_rpm = models.IntegerField(null=True, blank=True)
    return_type = models.CharField(max_length=100, null=True, blank=True)
    has_display_func = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    schema_hash = models.CharField(max_length=64)

    # Usage stats
    total_calls = models.IntegerField(default=0)
    total_errors = models.IntegerField(default=0)
    total_timeouts = models.IntegerField(default=0)
    avg_execution_ms = models.IntegerField(default=0)
    last_called_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["section", "name"]
        indexes = [
            models.Index(fields=["is_active", "section"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.section})"


class AppLLMToolCall(FullAuditMixin):
    """Log entry for each tool call within an agent invocation."""

    STATUS_CHOICES = [
        ("success", "Success"),
        ("error", "Error"),
        ("timeout", "Timeout"),
        ("validation_error", "Validation Error"),
        ("denied", "Denied"),
        ("pending", "Pending"),
    ]

    CONFIRMATION_CHOICES = [
        ("auto_approved", "Auto-approved"),
        ("auto_approved_by_policy", "Auto-approved by policy"),
        ("approved", "Approved by human"),
        ("denied", "Denied by human"),
        ("denied_by_policy", "Denied by policy"),
        ("expired", "Expired"),
    ]

    invocation = models.ForeignKey(
        "ai.AppLLMInvocation",
        on_delete=models.CASCADE,
        related_name="tool_calls",
    )
    tool = models.ForeignKey(
        AppLLMTool, on_delete=models.SET_NULL, null=True, related_name="calls"
    )
    tool_name = models.CharField(max_length=100)
    tool_input = models.JSONField()
    tool_output = models.JSONField(null=True, blank=True)
    round_number = models.IntegerField(default=1)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(null=True, blank=True)
    error_traceback = models.TextField(null=True, blank=True)

    # Confirmation tracking
    confirmation = models.ForeignKey(
        "ai.AppLLMToolConfirmation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tool_call",
    )
    confirmation_decision = models.CharField(
        max_length=30, null=True, blank=True, choices=CONFIRMATION_CHOICES
    )
    confirmation_decided_by = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["invocation", "round_number", "created_at"]
        indexes = [
            models.Index(fields=["invocation", "round_number"]),
            models.Index(fields=["tool_name", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.tool_name} (round {self.round_number}, {self.status})"
