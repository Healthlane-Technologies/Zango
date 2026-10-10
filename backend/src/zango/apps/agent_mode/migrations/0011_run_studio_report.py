from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent_mode", "0010_requirement_workflows"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentrun",
            name="studio_report",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
