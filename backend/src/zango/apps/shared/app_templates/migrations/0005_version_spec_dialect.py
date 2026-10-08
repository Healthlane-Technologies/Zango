from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_templates", "0004_version_references"),
    ]

    operations = [
        migrations.AddField(
            model_name="apptemplateversion",
            name="spec_dialect",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
