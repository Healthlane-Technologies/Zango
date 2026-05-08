"""
Memory models — session-scoped conversation history for LLM agents.
"""

from django.db import models

from zango.core.model_mixins import FullAuditMixin


class AppLLMMemorySession(FullAuditMixin):
    """
    A named conversation session tied to a specific agent.
    Groups a sequence of messages exchanged in a single user session
    (e.g., a chat thread, a workflow run).
    """

    agent = models.ForeignKey(
        "ai.AppLLMAgent",
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    session_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Caller-supplied opaque identifier (e.g. 'user-42-chat')",
    )
    user_ref = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Optional opaque reference to the app user (for audit)",
    )
    last_active_at = models.DateTimeField(
        auto_now=True,
        help_text="Updated on every agent.run() call that touches this session",
    )
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(
        default=dict,
        help_text="Arbitrary caller-supplied metadata (e.g. page context, tenant info)",
    )

    class Meta:
        unique_together = [("agent", "session_id")]
        ordering = ["-last_active_at"]

    def __str__(self):
        return f"{self.agent.name} / {self.session_id}"


class AppLLMMemoryMessage(FullAuditMixin):
    """
    A single stored message within a memory session.
    Only user input and final assistant responses are stored — not
    intermediate tool-call rounds (they are ephemeral scaffolding).
    """

    session = models.ForeignKey(
        AppLLMMemorySession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(
        max_length=20,
        help_text="'user' or 'assistant'",
    )
    content = models.JSONField(
        help_text="Message content — str or list of content blocks",
    )
    invocation = models.ForeignKey(
        "ai.AppLLMInvocation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="memory_messages",
        help_text="The invocation that produced this message (for audit trail)",
    )
    sequence = models.PositiveIntegerField(
        help_text="Monotonically increasing counter within the session (1-based)",
    )

    class Meta:
        ordering = ["sequence"]
        indexes = [
            models.Index(
                fields=["session", "sequence"],
                name="ai_mem_msg_seq_idx",
            ),
        ]

    def __str__(self):
        return f"{self.session} [{self.sequence}] {self.role}"
