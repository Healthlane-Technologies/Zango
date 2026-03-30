# Generated manually — Tools subsystem models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0005_invocation_agent_prompt"),
    ]

    operations = [
        # 1. AppLLMTool
        migrations.CreateModel(
            name="AppLLMTool",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.CharField(blank=True, editable=False, max_length=255)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("modified_by", models.CharField(blank=True, editable=False, max_length=255)),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField()),
                ("section", models.CharField(default="general", max_length=50)),
                ("parameters_schema", models.JSONField(help_text="JSON Schema for the tool's input parameters")),
                ("python_path", models.CharField(max_length=255)),
                ("safety", models.CharField(choices=[("read_only", "Read Only"), ("write", "Write"), ("external", "External")], default="read_only", max_length=20)),
                ("requires_confirmation", models.BooleanField(default=False)),
                ("timeout_seconds", models.IntegerField(default=30)),
                ("rate_limit_rpm", models.IntegerField(blank=True, null=True)),
                ("return_type", models.CharField(blank=True, max_length=100, null=True)),
                ("has_display_func", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("schema_hash", models.CharField(max_length=64)),
                ("total_calls", models.IntegerField(default=0)),
                ("total_errors", models.IntegerField(default=0)),
                ("total_timeouts", models.IntegerField(default=0)),
                ("avg_execution_ms", models.IntegerField(default=0)),
                ("last_called_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["section", "name"],
                "abstract": False,
                "indexes": [
                    models.Index(fields=["is_active", "section"], name="ai_tool_active_section_idx"),
                    models.Index(fields=["name"], name="ai_tool_name_idx"),
                ],
            },
            bases=(models.Model,),
        ),
        # 2. AppLLMToolConfirmation
        migrations.CreateModel(
            name="AppLLMToolConfirmation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.CharField(blank=True, editable=False, max_length=255)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("modified_by", models.CharField(blank=True, editable=False, max_length=255)),
                ("tool_name", models.CharField(max_length=100)),
                ("tool_input", models.JSONField()),
                ("tool_input_display", models.TextField(blank=True, default="")),
                ("pipeline_state", models.JSONField(default=dict)),
                ("round_number", models.IntegerField(default=1)),
                ("status", models.CharField(choices=[("pending", "Awaiting decision"), ("approved", "Approved"), ("denied", "Denied"), ("auto_approved", "Auto-approved"), ("auto_approved_by_policy", "Auto-approved by policy"), ("expired", "Expired")], default="pending", max_length=30)),
                ("decided_by_user", models.CharField(blank=True, default="", max_length=255)),
                ("decided_by_policy", models.CharField(blank=True, default="", max_length=200)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("denial_reason", models.TextField(blank=True, default="")),
                ("expires_at", models.DateTimeField()),
                ("invocation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="confirmations", to="ai.appllminvocation")),
                ("tool", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="ai.appllmtool")),
            ],
            options={
                "ordering": ["-created_at"],
                "abstract": False,
                "indexes": [
                    models.Index(fields=["status", "-created_at"], name="ai_confirm_status_idx"),
                    models.Index(fields=["status", "expires_at"], name="ai_confirm_expiry_idx"),
                ],
            },
            bases=(models.Model,),
        ),
        # 3. AppLLMToolCall
        migrations.CreateModel(
            name="AppLLMToolCall",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.CharField(blank=True, editable=False, max_length=255)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("modified_by", models.CharField(blank=True, editable=False, max_length=255)),
                ("tool_name", models.CharField(max_length=100)),
                ("tool_input", models.JSONField()),
                ("tool_output", models.JSONField(blank=True, null=True)),
                ("round_number", models.IntegerField(default=1)),
                ("execution_time_ms", models.IntegerField(blank=True, null=True)),
                ("status", models.CharField(choices=[("success", "Success"), ("error", "Error"), ("timeout", "Timeout"), ("validation_error", "Validation Error"), ("denied", "Denied"), ("pending", "Pending")], max_length=20)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("error_traceback", models.TextField(blank=True, null=True)),
                ("confirmation_decision", models.CharField(blank=True, choices=[("auto_approved", "Auto-approved"), ("auto_approved_by_policy", "Auto-approved by policy"), ("approved", "Approved by human"), ("denied", "Denied by human"), ("denied_by_policy", "Denied by policy"), ("expired", "Expired")], max_length=30, null=True)),
                ("confirmation_decided_by", models.CharField(blank=True, max_length=255, null=True)),
                ("invocation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tool_calls", to="ai.appllminvocation")),
                ("tool", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="calls", to="ai.appllmtool")),
                ("confirmation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tool_call", to="ai.appllmtoolconfirmation")),
            ],
            options={
                "ordering": ["invocation", "round_number", "created_at"],
                "abstract": False,
                "indexes": [
                    models.Index(fields=["invocation", "round_number"], name="ai_toolcall_inv_round_idx"),
                    models.Index(fields=["tool_name", "-created_at"], name="ai_toolcall_name_idx"),
                    models.Index(fields=["status", "-created_at"], name="ai_toolcall_status_idx"),
                ],
            },
            bases=(models.Model,),
        ),
    ]
