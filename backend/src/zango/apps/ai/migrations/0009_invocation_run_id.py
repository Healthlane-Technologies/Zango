from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0008_invocation_request_files'),
    ]

    operations = [
        migrations.AddField(
            model_name='appllminvocation',
            name='run_id',
            field=models.UUIDField(
                blank=True,
                null=True,
                db_index=True,
                help_text='Groups all LLM call rounds belonging to a single agent.run() invocation',
            ),
        ),
        migrations.AddField(
            model_name='appllminvocation',
            name='round_number',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                help_text='Which round within the agent run (1 = first call, 2 = after first tool round, etc.)',
            ),
        ),
    ]
