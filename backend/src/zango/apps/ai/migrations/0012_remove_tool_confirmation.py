# Remove tool confirmation feature — drops AppLLMToolConfirmation table and
# confirmation-related fields from AppLLMTool and AppLLMToolCall.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0011_invocation_session_id"),
    ]

    operations = [
        # Remove confirmation FK and fields from AppLLMToolCall
        migrations.RemoveField(
            model_name="appllmtoolcall",
            name="confirmation",
        ),
        migrations.RemoveField(
            model_name="appllmtoolcall",
            name="confirmation_decision",
        ),
        migrations.RemoveField(
            model_name="appllmtoolcall",
            name="confirmation_decided_by",
        ),
        # Remove confirmation-related fields from AppLLMTool
        migrations.RemoveField(
            model_name="appllmtool",
            name="requires_confirmation",
        ),
        migrations.RemoveField(
            model_name="appllmtool",
            name="has_display_func",
        ),
        # Drop AppLLMToolConfirmation table
        migrations.DeleteModel(
            name="AppLLMToolConfirmation",
        ),
    ]
