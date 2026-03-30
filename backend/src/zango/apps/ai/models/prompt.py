"""
Versioned prompt templates with variable slots.
Prompts are referenced by name from app code; the Panel controls which version is live.
"""

import re

from django.db import models

from zango.core.model_mixins import FullAuditMixin


class AppLLMPrompt(FullAuditMixin):
    """
    A named prompt template. Each prompt can have multiple versions;
    exactly one version is active at any time.
    """

    TYPE_CHOICES = [
        ("system", "System"),
        ("user", "User"),
    ]

    name = models.CharField(
        max_length=150,
        unique=True,
        help_text="Slug-like identifier, e.g. 'assessment-question-system'",
    )
    description = models.TextField(blank=True, default="")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    active_version = models.ForeignKey(
        "ai.AppLLMPromptVersion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="The currently active version of this prompt",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.type})"


class AppLLMPromptVersion(FullAuditMixin):
    """
    An immutable versioned snapshot of a prompt's content.
    Once created, content and version_number never change — only status changes.
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    prompt = models.ForeignKey(
        AppLLMPrompt, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    content = models.TextField(help_text="Prompt template with {{variable}} placeholders")
    change_description = models.TextField(
        blank=True, default="", help_text="What changed in this version"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="draft"
    )
    variables = models.JSONField(
        default=list,
        help_text="Auto-extracted list of template variable names",
    )

    class Meta:
        unique_together = ("prompt", "version_number")
        ordering = ["-version_number"]

    def __str__(self):
        return f"{self.prompt.name} v{self.version_number} ({self.status})"

    @staticmethod
    def extract_variables(content: str) -> list[str]:
        """Extract unique {{variable_name}} placeholders from content."""
        matches = re.findall(r"\{\{(\w+)\}\}", content)
        # Deduplicate while preserving order
        seen = set()
        result = []
        for var in matches:
            if var not in seen:
                seen.add(var)
                result.append(var)
        return result

    def render(self, **kwargs) -> str:
        """
        Replace {{variable}} placeholders with provided values.
        Raises PromptRenderError if required variables are missing.
        """
        result = self.content
        for key, value in kwargs.items():
            result = result.replace("{{" + key + "}}", str(value))

        # Check for unreplaced variables
        remaining = re.findall(r"\{\{(\w+)\}\}", result)
        if remaining:
            from zango.ai.exceptions import PromptRenderError

            raise PromptRenderError(remaining)

        return result
