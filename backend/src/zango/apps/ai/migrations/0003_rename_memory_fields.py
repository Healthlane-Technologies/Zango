from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ai", "0002_appllmtool_memory_policy"),
    ]

    operations = [
        migrations.RenameField(
            model_name="appllmagent",
            old_name="memory_enabled",
            new_name="short_term_memory",
        ),
        migrations.RenameField(
            model_name="appllmagent",
            old_name="memory_max_messages",
            new_name="short_term_memory_max_messages",
        ),
    ]
