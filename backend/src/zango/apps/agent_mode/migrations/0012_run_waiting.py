from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent_mode", "0011_run_studio_report"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentrun",
            name="pending_actions",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="agentrun",
            name="studio_checkpoint",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="agentrun",
            name="resumed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="agentrun",
            name="status",
            field=models.CharField(
                choices=[
                    ("queued", "Queued"),
                    ("running", "Running"),
                    ("syncing", "Syncing"),
                    ("waiting", "Waiting for you"),
                    ("success", "Success"),
                    ("partial", "Completed with sync errors"),
                    ("failed", "Failed"),
                    ("timeout", "Timed out"),
                    ("aborted", "Aborted"),
                ],
                db_index=True,
                default="queued",
                max_length=16,
            ),
        ),
    ]
