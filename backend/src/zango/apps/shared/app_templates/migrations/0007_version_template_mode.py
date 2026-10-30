from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_templates", "0006_file_encoding"),
    ]

    operations = [
        migrations.AddField(
            model_name="apptemplateversion",
            name="launch",
            field=models.CharField(
                choices=[
                    ("brief", "From a brief"),
                    ("direct", "Open the template as it is"),
                ],
                default="brief",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="apptemplateversion",
            name="welcome",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="apptemplateversion",
            name="prototype_parts",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="apptemplateversion",
            name="prototype_hash",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
