from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_templates", "0007_version_template_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="apptemplate",
            name="listed",
            field=models.BooleanField(default=True),
        ),
    ]
