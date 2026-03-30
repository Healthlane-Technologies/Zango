# Generated manually for Zango AI framework — Agent model

import decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0003_prompt"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppLLMAgent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.CharField(blank=True, editable=False, max_length=255),
                ),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "modified_by",
                    models.CharField(blank=True, editable=False, max_length=255),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Slug identifier, e.g. 'assessment-question-generator'",
                        max_length=150,
                        unique=True,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "model",
                    models.CharField(
                        help_text="Model ID from provider's enabled_models",
                        max_length=100,
                    ),
                ),
                ("temperature", models.FloatField(default=0.7)),
                ("max_tokens", models.IntegerField(default=4096)),
                ("timeout_seconds", models.IntegerField(default=30)),
                (
                    "output_schema",
                    models.CharField(
                        choices=[
                            ("JSON", "JSON"),
                            ("Text", "Text"),
                            ("Markdown", "Markdown"),
                        ],
                        default="Text",
                        max_length=20,
                    ),
                ),
                (
                    "guardrails",
                    models.JSONField(
                        default=list, help_text="List of guardrail names"
                    ),
                ),
                (
                    "tools",
                    models.JSONField(
                        default=list, help_text="List of tool names"
                    ),
                ),
                ("is_enabled", models.BooleanField(default=True)),
                ("total_invocations", models.IntegerField(default=0)),
                (
                    "total_cost_usd",
                    models.DecimalField(
                        decimal_places=6,
                        default=decimal.Decimal("0"),
                        max_digits=12,
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        help_text="Which provider configuration to use",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agents",
                        to="ai.appllmprovider",
                    ),
                ),
                (
                    "system_prompt",
                    models.ForeignKey(
                        blank=True,
                        help_text="System prompt template",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agents_as_system",
                        to="ai.appllmprompt",
                    ),
                ),
                (
                    "user_prompt",
                    models.ForeignKey(
                        blank=True,
                        help_text="User prompt template",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agents_as_user",
                        to="ai.appllmprompt",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
                "indexes": [
                    models.Index(
                        fields=["provider"],
                        name="ai_agent_provider_idx",
                    ),
                    models.Index(
                        fields=["is_enabled"],
                        name="ai_agent_enabled_idx",
                    ),
                ],
            },
            bases=(models.Model,),
        ),
    ]
