import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent_mode_platform", "0002_agentmodesettings_allow_frontend_build_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AgentAppScaffold",
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
                ("created_by", models.CharField(blank=True, editable=False, max_length=255)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("modified_by", models.CharField(blank=True, editable=False, max_length=255)),
                (
                    "object_uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, unique=True
                    ),
                ),
                ("prompt", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("naming", "Choosing a name"),
                            ("creating", "Creating the app"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="naming",
                        max_length=16,
                    ),
                ),
                ("app_name", models.CharField(blank=True, default="", max_length=30)),
                ("app_label", models.CharField(blank=True, default="", max_length=120)),
                ("app_description", models.TextField(blank=True, default="")),
                ("name_source", models.CharField(blank=True, default="", max_length=16)),
                ("app_uuid", models.UUIDField(blank=True, db_index=True, null=True)),
                ("init_task_id", models.CharField(blank=True, default="", max_length=64)),
                ("requirement_uuid", models.UUIDField(blank=True, null=True)),
                ("celery_task_id", models.CharField(blank=True, default="", max_length=64)),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_by_label", models.CharField(blank=True, default="", max_length=255)),
            ],
            options={
                "db_table": "agent_mode_app_scaffold",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="agentappscaffold",
            index=models.Index(
                fields=["status", "-created_at"],
                name="agent_mode__status_9b4e2f_idx",
            ),
        ),
    ]
