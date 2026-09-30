from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent_mode", "0004_agentrequirementmessage_questions"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentrequirement",
            name="template_slug",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="agentrequirement",
            name="spec_format",
            field=models.CharField(
                choices=[("markdown", "Markdown"), ("yaml", "YAML")],
                default="markdown",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="agentrequirement",
            name="spec_is_draft",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="agentrequirementversion",
            name="spec_format",
            field=models.CharField(
                choices=[("markdown", "Markdown"), ("yaml", "YAML")],
                default="markdown",
                max_length=16,
            ),
        ),
    ]
