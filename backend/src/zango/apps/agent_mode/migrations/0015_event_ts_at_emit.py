from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('agent_mode', '0014_message_preview_focus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentrunevent',
            name='ts',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
