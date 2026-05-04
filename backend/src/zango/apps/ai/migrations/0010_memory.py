import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0009_invocation_run_id"),
    ]

    operations = [
        # 1. Add memory fields to AppLLMAgent
        migrations.AddField(
            model_name="appllmagent",
            name="memory_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Enable session-scoped conversation history",
            ),
        ),
        migrations.AddField(
            model_name="appllmagent",
            name="memory_max_messages",
            field=models.IntegerField(
                default=20,
                help_text="Max past user/assistant pairs to load per call",
            ),
        ),
        # 2. AppLLMMemorySession
        migrations.CreateModel(
            name="AppLLMMemorySession",
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
                    "session_id",
                    models.CharField(
                        db_index=True,
                        max_length=255,
                        help_text="Caller-supplied opaque identifier",
                    ),
                ),
                (
                    "user_ref",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        help_text="Optional opaque reference to the app user",
                    ),
                ),
                (
                    "last_active_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Updated on every agent.run() call that touches this session",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "metadata",
                    models.JSONField(
                        default=dict,
                        help_text="Arbitrary caller-supplied metadata",
                    ),
                ),
                (
                    "agent",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="ai.appllmagent",
                    ),
                ),
            ],
            options={
                "ordering": ["-last_active_at"],
                "abstract": False,
            },
        ),
        migrations.AddConstraint(
            model_name="appllmmemorysession",
            constraint=models.UniqueConstraint(
                fields=["agent", "session_id"],
                name="ai_mem_session_unique",
            ),
        ),
        # 3. AppLLMMemoryMessage
        migrations.CreateModel(
            name="AppLLMMemoryMessage",
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
                    "role",
                    models.CharField(
                        max_length=20,
                        help_text="'user' or 'assistant'",
                    ),
                ),
                (
                    "content",
                    models.JSONField(
                        help_text="Message content — str or list of content blocks",
                    ),
                ),
                (
                    "tool_calls",
                    models.JSONField(
                        blank=True,
                        null=True,
                        help_text="Tool call list for assistant messages",
                    ),
                ),
                (
                    "tool_call_id",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=100,
                        help_text="Tool call ID for tool-result messages",
                    ),
                ),
                (
                    "sequence",
                    models.PositiveIntegerField(
                        help_text="Monotonically increasing counter within the session",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="ai.appllmmemorysession",
                    ),
                ),
                (
                    "invocation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="memory_messages",
                        to="ai.appllminvocation",
                    ),
                ),
            ],
            options={
                "ordering": ["sequence"],
                "abstract": False,
            },
        ),
        migrations.AddIndex(
            model_name="appllmmemorymessage",
            index=models.Index(
                fields=["session", "sequence"],
                name="ai_mem_msg_seq_idx",
            ),
        ),
    ]
