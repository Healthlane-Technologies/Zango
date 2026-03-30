# Generated manually — Add agent + prompt tracking to AppLLMInvocation

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0004_agent"),
    ]

    operations = [
        migrations.AddField(
            model_name="appllminvocation",
            name="agent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="invocations",
                to="ai.appllmagent",
            ),
        ),
        migrations.AddField(
            model_name="appllminvocation",
            name="agent_name",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
        migrations.AddField(
            model_name="appllminvocation",
            name="system_prompt_name",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
        migrations.AddField(
            model_name="appllminvocation",
            name="system_prompt_version",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="appllminvocation",
            name="user_prompt_name",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
        migrations.AddField(
            model_name="appllminvocation",
            name="user_prompt_version",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="appllminvocation",
            name="rendered_system_prompt",
            field=models.TextField(
                blank=True,
                help_text="Fully rendered system prompt after variable substitution",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="appllminvocation",
            name="context_snapshot",
            field=models.JSONField(
                blank=True,
                help_text="Variables/context passed at runtime",
                null=True,
            ),
        ),
        migrations.AddIndex(
            model_name="appllminvocation",
            index=models.Index(
                fields=["agent", "-created_at"],
                name="ai_appllminv_agent_idx",
            ),
        ),
    ]
