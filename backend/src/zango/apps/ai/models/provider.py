"""
Tenant-scoped database models for app-level LLM provider configuration.
These models live in each app's schema (not the shared/public schema).
They store the app admin's configuration of available providers.
"""

from django.db import models
from django.db.models import F
from django.utils import timezone

from zango.ai.encryption import decrypt_config
from zango.ai.exceptions import BudgetExceeded, ProviderDisabled
from zango.core.model_mixins import FullAuditMixin


class AppLLMProvider(FullAuditMixin):
    """
    An app's configured connection to an LLM provider.
    One app can have multiple configurations (e.g., different API keys, models).
    """

    # Identity
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Admin-friendly name, e.g., 'claude-primary', 'gpt4-fallback'",
    )
    description = models.TextField(blank=True, default="")

    # Links to the platform-level provider registry
    provider_slug = models.CharField(
        max_length=50,
        help_text="References the registered provider class, e.g., 'anthropic', 'openai'",
    )

    # Configuration (encrypted JSON blob containing all config including API keys)
    config_encrypted = models.BinaryField(
        help_text="Encrypted JSON containing all config including API keys"
    )

    # The default model to use when agents don't specify one
    default_model = models.CharField(
        max_length=100,
        help_text="Default model ID from the provider's supported_models list",
    )

    # Rate limiting
    rate_limit_rpm = models.IntegerField(
        null=True, blank=True, help_text="Max requests per minute. Null = no limit."
    )
    rate_limit_tpm = models.IntegerField(
        null=True, blank=True, help_text="Max tokens per minute. Null = no limit."
    )

    # Budget controls
    monthly_budget_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly spending cap in USD. Null = no limit.",
    )
    budget_alert_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=80.00,
        help_text="Alert when this percentage of monthly budget is consumed",
    )
    current_month_spend_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Running total of spend for current month. Reset on budget_reset_day.",
    )
    budget_reset_day = models.IntegerField(
        default=1, help_text="Day of month to reset the budget counter"
    )
    last_budget_reset = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last budget reset",
    )

    # Status
    is_enabled = models.BooleanField(default=True)
    is_validated = models.BooleanField(
        default=False,
        help_text="True if validate_config() succeeded at least once",
    )
    last_validated_at = models.DateTimeField(null=True, blank=True)
    validation_error = models.TextField(
        null=True, blank=True, help_text="Last validation error message, if any"
    )

    # Usage stats (updated atomically, not real-time)
    total_invocations = models.IntegerField(default=0)
    total_input_tokens = models.BigIntegerField(default=0)
    total_output_tokens = models.BigIntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=12, decimal_places=6, default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.provider_slug})"

    def get_provider_class(self):
        """Returns the registered provider class for this config's provider_slug."""
        from zango.ai.providers.registry import get_provider_class

        return get_provider_class(self.provider_slug)

    def get_client(self):
        """
        Instantiates and returns a configured provider client.
        Decrypts config, creates provider instance.
        Raises ProviderDisabled if is_enabled is False.
        Raises BudgetExceeded if monthly budget is exceeded.
        """
        if not self.is_enabled:
            raise ProviderDisabled(self.name)

        self.check_and_reset_budget()

        if (
            self.monthly_budget_usd
            and self.current_month_spend_usd >= self.monthly_budget_usd
        ):
            raise BudgetExceeded(self.name, self.monthly_budget_usd)

        config = self._decrypt_config()
        provider_cls = self.get_provider_class()
        return provider_cls(config)

    def _decrypt_config(self) -> dict:
        """Decrypt config_encrypted and return as dict."""
        return decrypt_config(self.config_encrypted)

    def record_usage(self, usage, cost: float):
        """
        Atomically update usage counters.
        Uses F() expressions to avoid race conditions.
        """
        AppLLMProvider.objects.filter(pk=self.pk).update(
            total_invocations=F("total_invocations") + 1,
            total_input_tokens=F("total_input_tokens") + usage.input_tokens,
            total_output_tokens=F("total_output_tokens") + usage.output_tokens,
            total_cost_usd=F("total_cost_usd") + cost,
            current_month_spend_usd=F("current_month_spend_usd") + cost,
        )

    def check_budget(self) -> dict:
        """
        Returns budget status with JSON-serializable values.
        """
        if not self.monthly_budget_usd:
            return {
                "within_budget": True,
                "used": str(self.current_month_spend_usd),
                "limit": None,
                "pct": 0,
            }
        pct = float(self.current_month_spend_usd / self.monthly_budget_usd) * 100
        return {
            "within_budget": self.current_month_spend_usd < self.monthly_budget_usd,
            "used": str(self.current_month_spend_usd),
            "limit": str(self.monthly_budget_usd),
            "pct": round(pct, 2),
        }

    def check_and_reset_budget(self):
        """
        Check if it's time to reset the monthly budget counter.
        Resets if the current day >= budget_reset_day and the last
        reset was before the current month's reset day.
        """
        now = timezone.now()
        reset_day = min(self.budget_reset_day, 28)  # Clamp to 28 for safety

        if self.last_budget_reset:
            # Calculate when the next reset should happen
            last_reset = self.last_budget_reset
            if last_reset.month == now.month and last_reset.year == now.year:
                # Already reset this month
                return

        if now.day >= reset_day:
            AppLLMProvider.objects.filter(pk=self.pk).update(
                current_month_spend_usd=0,
                last_budget_reset=now,
            )
            self.current_month_spend_usd = 0
            self.last_budget_reset = now


class AppLLMProviderModel(FullAuditMixin):
    """
    Tracks which models are enabled for a given provider configuration.
    Allows admins to restrict which models are available to agents.
    Also allows overriding cost rates (e.g., for enterprise agreements).
    """

    provider = models.ForeignKey(
        AppLLMProvider, on_delete=models.CASCADE, related_name="enabled_models"
    )
    model_id = models.CharField(
        max_length=100,
        help_text="The model identifier, e.g., 'claude-sonnet-4-20250514'",
    )
    display_name = models.CharField(max_length=100)

    # Cost overrides (null = use provider class defaults)
    input_cost_per_mtok_override = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Override input cost per million tokens. Null = use default.",
    )
    output_cost_per_mtok_override = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Override output cost per million tokens. Null = use default.",
    )

    is_enabled = models.BooleanField(default=True)

    # Per-model rate limits (more granular than provider-level)
    rate_limit_rpm = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("provider", "model_id")

    def __str__(self):
        return f"{self.provider.name} / {self.display_name}"
