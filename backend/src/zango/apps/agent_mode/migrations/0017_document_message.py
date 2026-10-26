import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent_mode", "0016_open_prototype"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentrequirementdocument",
            name="message",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="attachments",
                to="agent_mode.agentrequirementmessage",
            ),
        ),
    ]
