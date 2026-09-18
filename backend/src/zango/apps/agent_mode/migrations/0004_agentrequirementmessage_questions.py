from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent_mode", "0003_agentrequirement_agentrunevent_phase_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentrequirementmessage",
            name="questions",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
