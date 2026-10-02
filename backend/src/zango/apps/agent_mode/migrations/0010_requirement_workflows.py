from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent_mode", "0009_requirement_documents_and_drafting"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentrequirement",
            name="workflows",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
