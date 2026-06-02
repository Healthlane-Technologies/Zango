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

    MEMORY_POLICY_CHOICES = [
        ("include", "Include — replay verbatim in session history"),
        ("exclude", "Exclude — drop from loaded history (side-effect tools)"),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    section = models.CharField(max_length=50, default="general")
    parameters_schema = models.JSONField(
        help_text="JSON Schema for the tool's input parameters"
    )
    python_path = models.CharField(max_length=255)
    safety = models.CharField(
        max_length=20, choices=SAFETY_CHOICES, default="read_only"
    )
    timeout_seconds = models.IntegerField(default=30)
    rate_limit_rpm = models.IntegerField(null=True, blank=True)
    return_type = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    schema_hash = models.CharField(max_length=64)
    memory_policy = models.CharField(
        max_length=10,
        choices=MEMORY_POLICY_CHOICES,
        default="include",
        help_text=(
            "include: replay tool call/result verbatim in session history (default). "
            "exclude: drop from loaded history — use for side-effect tools (send_email, etc.)."
        ),
    )

    # Usage stats
    total_calls = models.IntegerField(default=0)
    total_errors = models.IntegerField(default=0)
    total_timeouts = models.IntegerField(default=0)
    avg_execution_ms = models.IntegerField(default=0)
    last_called_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["section", "name"]
        indexes = [
            models.Index(
                fields=["is_active", "section"], name="ai_appllmto_is_acti_ea744c_idx"
            ),
            models.Index(fields=["name"], name="ai_appllmto_name_7e53f7_idx"),
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

    class Meta:
        ordering = ["invocation", "round_number", "created_at"]
        indexes = [
            models.Index(
                fields=["invocation", "round_number"],
                name="ai_appllmto_invocat_a5cba3_idx",
            ),
            models.Index(
                fields=["tool_name", "-created_at"],
                name="ai_appllmto_tool_na_a0236e_idx",
            ),
            models.Index(
                fields=["status", "-created_at"], name="ai_appllmto_status_f21318_idx"
            ),
        ]

    def __str__(self):
        return f"{self.tool_name} (round {self.round_number}, {self.status})"
