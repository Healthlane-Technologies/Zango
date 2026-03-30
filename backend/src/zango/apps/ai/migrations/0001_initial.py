# Generated manually for Zango AI framework

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AppLLMProvider",
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
                        help_text="Admin-friendly name, e.g., 'claude-primary', 'gpt4-fallback'",
                        max_length=100,
                        unique=True,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "provider_slug",
                    models.CharField(
                        help_text="References the registered provider class, e.g., 'anthropic', 'openai'",
                        max_length=50,
                    ),
                ),
                (
                    "config_encrypted",
                    models.BinaryField(
                        help_text="Encrypted JSON containing all config including API keys"
                    ),
                ),
                (
                    "default_model",
                    models.CharField(
                        help_text="Default model ID from the provider's supported_models list",
                        max_length=100,
                    ),
                ),
                (
                    "rate_limit_rpm",
                    models.IntegerField(
                        blank=True,
                        help_text="Max requests per minute. Null = no limit.",
                        null=True,
                    ),
                ),
                (
                    "rate_limit_tpm",
                    models.IntegerField(
                        blank=True,
                        help_text="Max tokens per minute. Null = no limit.",
                        null=True,
                    ),
                ),
                (
                    "monthly_budget_usd",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Monthly spending cap in USD. Null = no limit.",
                        max_digits=10,
                        null=True,
                    ),
                ),
                (
                    "budget_alert_threshold",
                    models.DecimalField(
                        decimal_places=2,
                        default=80.00,
                        help_text="Alert when this percentage of monthly budget is consumed",
                        max_digits=5,
                    ),
                ),
                (
                    "current_month_spend_usd",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Running total of spend for current month. Reset on budget_reset_day.",
                        max_digits=10,
                    ),
                ),
                (
                    "budget_reset_day",
                    models.IntegerField(
                        default=1,
                        help_text="Day of month to reset the budget counter",
                    ),
                ),
                (
                    "last_budget_reset",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp of last budget reset",
                        null=True,
                    ),
                ),
                ("is_enabled", models.BooleanField(default=True)),
                (
                    "is_validated",
                    models.BooleanField(
                        default=False,
                        help_text="True if validate_config() succeeded at least once",
                    ),
                ),
                ("last_validated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "validation_error",
                    models.TextField(
                        blank=True,
                        help_text="Last validation error message, if any",
                        null=True,
                    ),
                ),
                ("total_invocations", models.IntegerField(default=0)),
                ("total_input_tokens", models.BigIntegerField(default=0)),
                ("total_output_tokens", models.BigIntegerField(default=0)),
                (
                    "total_cost_usd",
                    models.DecimalField(
                        decimal_places=6, default=0, max_digits=12
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="AppLLMProviderModel",
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
                    "model_id",
                    models.CharField(
                        help_text="The model identifier, e.g., 'claude-sonnet-4-20250514'",
                        max_length=100,
                    ),
                ),
                ("display_name", models.CharField(max_length=100)),
                (
                    "input_cost_per_mtok_override",
                    models.DecimalField(
                        blank=True,
                        decimal_places=4,
                        help_text="Override input cost per million tokens. Null = use default.",
                        max_digits=10,
                        null=True,
                    ),
                ),
                (
                    "output_cost_per_mtok_override",
                    models.DecimalField(
                        blank=True,
                        decimal_places=4,
                        help_text="Override output cost per million tokens. Null = use default.",
                        max_digits=10,
                        null=True,
                    ),
                ),
                ("is_enabled", models.BooleanField(default=True)),
                (
                    "rate_limit_rpm",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enabled_models",
                        to="ai.appllmprovider",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "unique_together": {("provider", "model_id")},
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="AppLLMInvocation",
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
                    "provider_name",
                    models.CharField(
                        help_text="Denormalized — preserved even if provider is deleted",
                        max_length=100,
                    ),
                ),
                ("provider_slug", models.CharField(max_length=50)),
                (
                    "model",
                    models.CharField(
                        help_text="The actual model used for this call",
                        max_length=100,
                    ),
                ),
                (
                    "request_messages",
                    models.JSONField(
                        help_text="The full messages array sent to the LLM"
                    ),
                ),
                (
                    "request_system",
                    models.TextField(
                        blank=True,
                        help_text="System prompt, if any",
                        null=True,
                    ),
                ),
                (
                    "request_tools",
                    models.JSONField(
                        blank=True,
                        help_text="Tool definitions sent to the LLM",
                        null=True,
                    ),
                ),
                (
                    "request_params",
                    models.JSONField(
                        default=dict,
                        help_text="temperature, max_tokens, etc.",
                    ),
                ),
                (
                    "response_content",
                    models.TextField(
                        blank=True,
                        help_text="Text content of the response",
                        null=True,
                    ),
                ),
                (
                    "response_tool_calls",
                    models.JSONField(
                        blank=True,
                        help_text="Tool calls requested by the LLM",
                        null=True,
                    ),
                ),
                (
                    "stop_reason",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("input_tokens", models.IntegerField(default=0)),
                ("output_tokens", models.IntegerField(default=0)),
                ("cache_creation_tokens", models.IntegerField(default=0)),
                ("cache_read_tokens", models.IntegerField(default=0)),
                (
                    "cost_usd",
                    models.DecimalField(
                        decimal_places=6, default=0, max_digits=10
                    ),
                ),
                ("latency_ms", models.IntegerField(blank=True, null=True)),
                (
                    "time_to_first_token_ms",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "triggered_by",
                    models.CharField(
                        choices=[
                            ("user", "User action (request/response)"),
                            ("celery", "Background task"),
                            ("cron", "Scheduled task"),
                            ("system", "System/internal"),
                        ],
                        default="user",
                        max_length=20,
                    ),
                ),
                (
                    "user_id_ref",
                    models.CharField(
                        blank=True,
                        help_text="The app user ID who triggered this, if applicable",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "celery_task_id",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("success", "Success"),
                            ("error", "Error"),
                            ("timeout", "Timeout"),
                            ("rate_limited", "Rate Limited"),
                            ("budget_exceeded", "Budget Exceeded"),
                        ],
                        default="success",
                        max_length=20,
                    ),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "error_type",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="invocations",
                        to="ai.appllmprovider",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "abstract": False,
                "indexes": [
                    models.Index(
                        fields=["provider", "-created_at"],
                        name="ai_appllminv_provide_idx",
                    ),
                    models.Index(
                        fields=["status", "-created_at"],
                        name="ai_appllminv_status_idx",
                    ),
                    models.Index(
                        fields=["-created_at"],
                        name="ai_appllminv_created_idx",
                    ),
                ],
            },
            bases=(models.Model,),
        ),
    ]
