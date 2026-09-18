"""Platform-level Agent Mode configuration — public schema, singleton.

Agent Mode is a platform-operator capability, so its Anthropic credentials
live once in the public schema rather than per-tenant. The encrypted-blob
pattern is the same one ``AppLLMProvider`` uses (``zango.ai.encryption``,
backed by Zango's Fernet ``FIELD_ENCRYPTION_KEY``).

The plaintext key is decrypted only in memory, at the moment a run starts,
and is never returned by any API path — see ``masked_config()``.
"""

from __future__ import annotations

import uuid

from django.db import models

from zango.core.model_mixins import FullAuditMixin


class AgentModeSettings(FullAuditMixin):
    """Singleton (singleton_id=1) platform configuration for Agent Mode."""

    SECRET_FIELDS = ["api_key", "auth_token", "aws_secret_access_key"]

    singleton_id = models.PositiveSmallIntegerField(
        default=1, unique=True, editable=False
    )
    is_enabled = models.BooleanField(default=False)
    provider = models.CharField(max_length=16, default="anthropic")
    config_encrypted = models.BinaryField(null=True, blank=True)

    # --- build agent (phase 2: implements the approved spec) --------------
    default_model = models.CharField(max_length=64, blank=True, default="")
    default_effort = models.CharField(max_length=16, blank=True, default="")
    max_run_seconds = models.PositiveIntegerField(default=1800)
    max_turns = models.PositiveIntegerField(null=True, blank=True)

    # --- analyst agent (phase 1: gathers the requirement) -----------------
    # Configured separately because the two do very different work: the
    # analyst reads and asks questions in short turns, so it rarely needs the
    # same model or budget as a build that writes dozens of files.
    analyst_model = models.CharField(max_length=64, blank=True, default="")
    analyst_effort = models.CharField(max_length=16, blank=True, default="")
    analyst_budget_usd = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    analyst_max_turns = models.PositiveIntegerField(null=True, blank=True)

    # --- behaviour --------------------------------------------------------
    allow_frontend_build = models.BooleanField(default=False)
    ensure_packages = models.BooleanField(default=True)
    max_budget_usd = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    monthly_budget_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    is_validated = models.BooleanField(default=False)
    last_validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "agent_mode_platform_settings"
        verbose_name = "Agent Mode settings"
        verbose_name_plural = "Agent Mode settings"

    @classmethod
    def load(cls) -> "AgentModeSettings | None":
        return cls.objects.filter(singleton_id=1).first()

    def get_config(self) -> dict:
        """Decrypt the stored config. In-memory only — never serialize this."""
        if not self.config_encrypted:
            return {}
        from zango.ai.encryption import decrypt_config

        return decrypt_config(self.config_encrypted)

    def set_config(self, config: dict) -> None:
        from zango.ai.encryption import encrypt_config

        self.config_encrypted = encrypt_config(config)

    def masked_config(self) -> dict:
        """Config with every secret masked. The only API-safe accessor."""
        from zango.ai.encryption import mask_config

        return mask_config(self.get_config(), self.SECRET_FIELDS)

    def __str__(self) -> str:
        state = "enabled" if self.is_enabled else "disabled"
        return f"Agent Mode settings ({self.provider}, {state})"


class ScaffoldStatus(models.TextChoices):
    """Lifecycle of a "Build with Agent" hand-off.

    Short-lived: it exists only to carry a one-line ask from the platform
    landing page to a requirement conversation inside a brand-new app.
    """

    NAMING = "naming", "Choosing a name"
    CREATING = "creating", "Creating the app"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


SCAFFOLD_TERMINAL_STATUSES = frozenset({ScaffoldStatus.READY, ScaffoldStatus.FAILED})


class AgentAppScaffold(FullAuditMixin):
    """One "describe it and the agent builds it" hand-off.

    Lives in the public schema because it is created *before* the app exists —
    there is no tenant schema to write to yet. Once the app is deployed the
    conversation moves into that app's own ``AgentRequirement``, and this row
    is only a breadcrumb linking the two (so a page reload mid-creation can
    pick the thread back up).
    """

    object_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False
    )
    prompt = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=ScaffoldStatus.choices,
        default=ScaffoldStatus.NAMING,
        db_index=True,
    )

    # Chosen by the agent, validated against the tenant-name rules.
    app_name = models.CharField(max_length=30, blank=True, default="")
    app_label = models.CharField(max_length=120, blank=True, default="")
    app_description = models.TextField(blank=True, default="")
    name_source = models.CharField(max_length=16, blank=True, default="")

    # The app this became, and the workspace-init task to watch.
    app_uuid = models.UUIDField(null=True, blank=True, db_index=True)
    init_task_id = models.CharField(max_length=64, blank=True, default="")

    # The requirement conversation the user is handed off to.
    requirement_uuid = models.UUIDField(null=True, blank=True)

    celery_task_id = models.CharField(max_length=64, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    created_by_label = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "agent_mode_app_scaffold"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self) -> str:
        return f"Scaffold {self.object_uuid} ({self.status})"

    @property
    def is_terminal(self) -> bool:
        return self.status in SCAFFOLD_TERMINAL_STATUSES

    def fail(self, message: str) -> None:
        self.status = ScaffoldStatus.FAILED
        self.error_message = (message or "")[:2000]
        self.save(update_fields=["status", "error_message", "modified_at"])
