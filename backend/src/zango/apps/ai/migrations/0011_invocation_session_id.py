from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0010_memory"),
    ]

    operations = [
        migrations.AddField(
            model_name="appllminvocation",
            name="session_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Groups all agent.run() calls belonging to a single memory session. Null for non-memory agents.",
                max_length=255,
                null=True,
            ),
        ),
    ]
