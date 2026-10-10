from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_templates", "0005_version_spec_dialect"),
    ]

    operations = [
        migrations.AddField(
            model_name="apptemplatefile",
            name="encoding",
            field=models.CharField(blank=True, default="", max_length=8),
        ),
    ]
