"""
Every LLM call made through the framework is logged here.
This is the audit trail. It captures everything: what was sent, what came back,
who triggered it, how much it cost, and how long it took.

Log entries are immutable — never updated after creation (append-only).
"""

from django.db import models

from zango.core.model_mixins import FullAuditMixin
from zango.core.storage_utils import ZFileField


class AppLLMInvocation(FullAuditMixin):
    """Immutable log entry for every LLM API call."""

    TRIGGERED_BY_CHOICES = [
        ("user", "User action (request/response)"),
        ("celery", "Background task"),
        ("cron", "Scheduled task"),
        ("system", "System/internal"),
    ]

    STATUS_CHOICES = [
        ("success", "Success"),
        ("error", "Error"),
        ("timeout", "Timeout"),
        ("rate_limited", "Rate Limited"),
        ("budget_exceeded", "Budget Exceeded"),
    ]

    # Which provider configuration was used
    provider = models.ForeignKey(
        "ai.AppLLMProvider",
        on_delete=models.SET_NULL,
        null=True,
        related_name="invocations",
    )
    provider_name = models.CharField(
        max_length=100,
        help_text="Denormalized — preserved even if provider is deleted",
    )
    provider_slug = models.CharField(max_length=50)
    model = models.CharField(
        max_length=100, help_text="The actual model used for this call"
    )

    # Request
    request_messages = models.JSONField(
        help_text="The full messages array sent to the LLM"
    )
    request_system = models.TextField(
        null=True, blank=True, help_text="System prompt, if any"
    )
    request_tools = models.JSONField(
        null=True, blank=True, help_text="Tool definitions sent to the LLM"
    )
    request_params = models.JSONField(
        default=dict, help_text="temperature, max_tokens, etc."
    )
    request_files = models.JSONField(
        null=True,
        blank=True,
        help_text="Metadata of files attached to the request (filename, media_type, size_bytes)",
    )

    # Response
    response_content = models.TextField(
        null=True, blank=True, help_text="Text content of the response"
    )
    response_tool_calls = models.JSONField(
        null=True, blank=True, help_text="Tool calls requested by the LLM"
    )
    stop_reason = models.CharField(max_length=20, null=True, blank=True)

    # Usage & Cost
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_creation_tokens = models.IntegerField(default=0)
    cache_read_tokens = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)

    # Performance
    latency_ms = models.IntegerField(null=True, blank=True)
    time_to_first_token_ms = models.IntegerField(null=True, blank=True)

    # Agent tracking
    agent = models.ForeignKey(
        "ai.AppLLMAgent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invocations",
    )
    agent_name = models.CharField(max_length=150, blank=True, default="")

    # Prompt tracking
    system_prompt_name = models.CharField(max_length=150, blank=True, default="")
    system_prompt_version = models.IntegerField(null=True, blank=True)
    user_prompt_name = models.CharField(max_length=150, blank=True, default="")
    user_prompt_version = models.IntegerField(null=True, blank=True)
    rendered_system_prompt = models.TextField(
        null=True,
        blank=True,
        help_text="Fully rendered system prompt after variable substitution",
    )
    context_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Variables/context passed at runtime",
    )

    # Agent run grouping — all rounds of a single agent.run() share the same run_id
    run_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Groups all LLM call rounds belonging to a single agent.run() invocation",
    )
    round_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Which round within the agent run (1 = first call, 2 = after first tool round, etc.)",
    )
    session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Groups all agent.run() calls belonging to a single memory session. "
        "Null for non-memory agents.",
    )

    # Context — who/what triggered this
    triggered_by = models.CharField(
        max_length=20, choices=TRIGGERED_BY_CHOICES, default="user"
    )
    user_id_ref = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The app user ID who triggered this, if applicable",
    )
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="success")
    error_message = models.TextField(null=True, blank=True)
    error_type = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provider", "-created_at"]),
            models.Index(fields=["agent", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return (
            f"Invocation {self.pk} - {self.provider_name}/{self.model} ({self.status})"
        )


class AppLLMInvocationFile(FullAuditMixin):
    """
    A file attached to an LLM invocation. Mirrors what the model actually saw.

    One row per LLMFile passed to agent.run() / provider.complete(). Only round 1
    of an agent run creates rows — subsequent rounds re-use the same content.

    The `blob` field stores the actual bytes via the tenant's storage backend.
    For URL-only attachments (LLMFile.from_url), blob is null and only
    source_url is recorded. Identity fields (sha256, size_bytes, media_type)
    are kept even if the blob is later purged by a retention policy.
    """

    SOURCE_CHOICES = [
        ("upload", "Upload (django_file / bytes / path)"),
        ("url", "Public URL (not mirrored)"),
    ]

    invocation = models.ForeignKey(
        AppLLMInvocation,
        on_delete=models.CASCADE,
        related_name="files",
    )

    # Identity — preserved forever, even if blob is purged
    sha256 = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 of the file bytes. Empty for URL-only attachments.",
        blank=True,
        default="",
    )
    size_bytes = models.BigIntegerField(
        default=0, help_text="Size of the file bytes. 0 for URL-only attachments."
    )
    media_type = models.CharField(max_length=120, blank=True, default="")
    filename = models.CharField(max_length=512, blank=True, default="")

    source_kind = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_url = models.URLField(
        max_length=2048,
        blank=True,
        default="",
        help_text="Original URL when source_kind='url'.",
    )

    # The mirrored bytes — null for URL-only attachments or after retention purge.
    # validators=[] bypasses ZFileField's hardcoded extension allowlist, since
    # LLM attachments can legitimately be any media type.
    blob = ZFileField(null=True, blank=True, validators=[])

    class Meta:
        ordering = ["invocation_id", "id"]
        indexes = [
            models.Index(fields=["sha256"]),
            models.Index(fields=["invocation", "id"]),
        ]

    def __str__(self):
        return f"InvocationFile {self.pk} ({self.filename or self.sha256[:12] or self.source_url})"
