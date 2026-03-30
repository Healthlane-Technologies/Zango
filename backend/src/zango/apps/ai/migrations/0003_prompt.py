# Generated manually for Zango AI framework — Prompt Registry

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "ai",
            "0002_rename_ai_appllminv_provide_idx_ai_appllmin_provide_fdec95_idx_and_more",
        ),
    ]

    operations = [
        # 1. Create AppLLMPrompt WITHOUT active_version FK (circular dep)
        migrations.CreateModel(
            name="AppLLMPrompt",
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
                        help_text="Slug-like identifier, e.g. 'assessment-question-system'",
                        max_length=150,
                        unique=True,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "type",
                    models.CharField(
                        choices=[("system", "System"), ("user", "User")],
                        max_length=10,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["name"],
                "abstract": False,
            },
            bases=(models.Model,),
        ),
        # 2. Create AppLLMPromptVersion with FK to AppLLMPrompt
        migrations.CreateModel(
            name="AppLLMPromptVersion",
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
                ("version_number", models.PositiveIntegerField()),
                (
                    "content",
                    models.TextField(
                        help_text="Prompt template with {{variable}} placeholders"
                    ),
                ),
                (
                    "change_description",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="What changed in this version",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("active", "Active"),
                            ("inactive", "Inactive"),
                        ],
                        default="draft",
                        max_length=10,
                    ),
                ),
                (
                    "variables",
                    models.JSONField(
                        default=list,
                        help_text="Auto-extracted list of template variable names",
                    ),
                ),
                (
                    "prompt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="ai.appllmprompt",
                    ),
                ),
            ],
            options={
                "ordering": ["-version_number"],
                "abstract": False,
                "unique_together": {("prompt", "version_number")},
                "indexes": [
                    models.Index(
                        fields=["prompt", "-version_number"],
                        name="ai_promptver_prompt_ver_idx",
                    ),
                    models.Index(
                        fields=["status"],
                        name="ai_promptver_status_idx",
                    ),
                ],
            },
            bases=(models.Model,),
        ),
        # 3. Add active_version FK on AppLLMPrompt (circular ref resolved)
        migrations.AddField(
            model_name="appllmprompt",
            name="active_version",
            field=models.ForeignKey(
                blank=True,
                help_text="The currently active version of this prompt",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="ai.appllmpromptversion",
            ),
        ),
    ]
