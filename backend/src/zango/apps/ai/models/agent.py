"""
Agent configurations — named LLM agent that ties together a provider,
model, prompts, and parameters. The main developer-facing abstraction.
"""

from decimal import Decimal

from django.db import models
from django.db.models import F

from zango.core.model_mixins import FullAuditMixin


class AppLLMAgent(FullAuditMixin):
    """
    A named, configured LLM agent. Ties together provider, model, prompts,
    and parameters. App code references agents by name via get_agent().
    """

    OUTPUT_SCHEMA_CHOICES = [
        ("JSON", "JSON"),
        ("Text", "Text"),
        ("Markdown", "Markdown"),
    ]

    # Identity
    name = models.CharField(
        max_length=150,
        unique=True,
        help_text="Slug identifier, e.g. 'assessment-question-generator'",
    )
    description = models.TextField(blank=True, default="")

    # Provider & Model
    provider = models.ForeignKey(
        "ai.AppLLMProvider",
        null=True,
        on_delete=models.SET_NULL,
        related_name="agents",
        help_text="Which provider configuration to use",
    )
    model = models.CharField(
        max_length=100,
        help_text="Model ID from provider's enabled_models",
    )

    # Prompts
    system_prompt = models.ForeignKey(
        "ai.AppLLMPrompt",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="agents_as_system",
        help_text="System prompt template",
    )
    user_prompt = models.ForeignKey(
        "ai.AppLLMPrompt",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="agents_as_user",
        help_text="User prompt template",
    )

    # Parameters
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=4096)
    timeout_seconds = models.IntegerField(default=30)
    output_schema = models.CharField(
        max_length=20, choices=OUTPUT_SCHEMA_CHOICES, default="Text"
    )
    output_json_schema = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON Schema definition for structured output when output_schema is JSON",
    )

    tools = models.JSONField(default=list, help_text="List of tool names")

    # Memory
    short_term_memory = models.BooleanField(
        default=False,
        help_text="Enable session-scoped conversation history",
    )
    short_term_memory_max_messages = models.IntegerField(
        default=20,
        help_text="Max past user/assistant pairs to load per call (sliding window)",
    )

    # Status
    is_enabled = models.BooleanField(default=True)

    # Usage stats (updated atomically)
    total_invocations = models.IntegerField(default=0)
    total_cost_usd = models.DecimalField(
        max_digits=12, decimal_places=6, default=Decimal("0")
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.provider})"

    def record_usage(self, cost: float):
        """Atomically update agent usage counters."""
        AppLLMAgent.objects.filter(pk=self.pk).update(
            total_invocations=F("total_invocations") + 1,
            total_cost_usd=F("total_cost_usd") + cost,
        )

    def get_system_prompt_content(self, **variables):
        """Return rendered system prompt or None."""
        if not self.system_prompt or not self.system_prompt.active_version:
            return None
        if variables:
            return self.system_prompt.active_version.render(**variables)
        return self.system_prompt.active_version.content

    def get_user_prompt_content(self, **variables):
        """Return rendered user prompt or None."""
        if not self.user_prompt or not self.user_prompt.active_version:
            return None
        if variables:
            return self.user_prompt.active_version.render(**variables)
        return self.user_prompt.active_version.content
