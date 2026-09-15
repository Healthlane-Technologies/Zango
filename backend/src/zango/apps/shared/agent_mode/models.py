"""Platform-level Agent Mode configuration — public schema, singleton.

Agent Mode is a platform-operator capability, so its Anthropic credentials
live once in the public schema rather than per-tenant. The encrypted-blob
pattern is the same one ``AppLLMProvider`` uses (``zango.ai.encryption``,
backed by Zango's Fernet ``FIELD_ENCRYPTION_KEY``).

The plaintext key is decrypted only in memory, at the moment a run starts,
and is never returned by any API path — see ``masked_config()``.
"""

from __future__ import annotations

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

    default_model = models.CharField(max_length=64, blank=True, default="")
    default_effort = models.CharField(max_length=16, blank=True, default="")
    max_run_seconds = models.PositiveIntegerField(default=1800)
    max_turns = models.PositiveIntegerField(null=True, blank=True)
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
