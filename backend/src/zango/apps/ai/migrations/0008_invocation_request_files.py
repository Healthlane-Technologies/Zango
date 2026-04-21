from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0007_remove_appllmagent_ai_agent_provider_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appllminvocation',
            name='request_files',
            field=models.JSONField(
                blank=True,
                null=True,
                help_text='Metadata of files attached to the request (filename, media_type, size_bytes)',
            ),
        ),
    ]
