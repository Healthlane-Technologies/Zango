from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent_mode", "0015_event_ts_at_emit"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentrequirement",
            name="preview_mode",
            field=models.CharField(blank=True, default="kit", max_length=8),
        ),
        migrations.AddField(
            model_name="agentrequirement",
            name="prototype_parts",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="agentrequirement",
            name="prototype_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="agentrequirement",
            name="prototype_revision",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="agentrequirementversion",
            name="prototype_parts",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="agentrequirementversion",
            name="prototype_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
