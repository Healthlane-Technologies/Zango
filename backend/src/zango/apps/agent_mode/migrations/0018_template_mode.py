import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent_mode", "0017_document_message"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agentrequirement",
            name="initial_prompt",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="agentrequirementversion",
            name="preview_mode",
            field=models.CharField(blank=True, default="", max_length=8),
        ),
        migrations.AddField(
            model_name="agentrequirementversion",
            name="baseline",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="agentrun",
            name="requirement_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="runs",
                to="agent_mode.agentrequirementversion",
            ),
        ),
    ]
