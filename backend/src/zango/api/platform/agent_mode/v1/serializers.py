"""Serializers for Agent Mode runs.

Nothing here may expose the Anthropic credential: the key lives only in the
worker process's ClaudeAgentOptions.env and is redacted out of every event
before insert.
"""

from decimal import Decimal

from rest_framework import serializers

from zango.apps.agent_mode.models import (
    AgentRequirement,
    AgentRequirementMessage,
    AgentRun,
)


class AgentRunListSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(source="object_uuid", read_only=True)
    is_terminal = serializers.BooleanField(read_only=True)

    class Meta:
        model = AgentRun
        fields = (
            "uuid",
            "title",
            "status",
            "is_terminal",
            "trigger_kind",
            "triggered_by",
            "queued_at",
            "started_at",
            "ended_at",
            "duration_ms",
            "total_cost_usd",
            "num_turns",
            "requires_restart",
        )


class AgentRunDetailSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(source="object_uuid", read_only=True)
    is_terminal = serializers.BooleanField(read_only=True)
    resumed_from = serializers.UUIDField(
        source="resumed_from.object_uuid", read_only=True, allow_null=True
    )

    class Meta:
        model = AgentRun
        fields = (
            "uuid",
            "prompt",
            "title",
            "status",
            "is_terminal",
            "trigger_kind",
            "triggered_by",
            "abort_requested",
            "queued_at",
            "started_at",
            "agent_ended_at",
            "ended_at",
            "duration_ms",
            "model",
            "effort",
            "permission_mode",
            "max_turns",
            "max_budget_usd",
            "skill_name",
            "workspace_path",
            "session_id",
            "resumed_from",
            "result_subtype",
            "terminal_reason",
            "result_text",
            "num_turns",
            "duration_api_ms",
            "total_cost_usd",
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "cache_creation_tokens",
            "model_usage",
            "error_type",
            "error_message",
            "api_error_status",
            "files_changed",
            "tool_use_counts",
            "post_steps",
            "test_users",
            "requires_restart",
            "can_resume",
            "resumed_from",
        )

    can_resume = serializers.SerializerMethodField()

    def get_can_resume(self, obj):
        # A successful run has nothing to continue; one with no session cannot
        # be continued even if it failed.
        return bool(
            obj.session_id and obj.status in ("failed", "timeout", "aborted", "partial")
        )


class AgentRunCreateSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=20_000, trim_whitespace=True)
    model = serializers.CharField(max_length=64, required=False, allow_blank=True)
    effort = serializers.ChoiceField(
        choices=["low", "medium", "high", "xhigh", "max"],
        required=False,
        allow_blank=True,
    )
    max_turns = serializers.IntegerField(required=False, min_value=1, max_value=500)
    max_budget_usd = serializers.DecimalField(
        max_digits=10, decimal_places=4, required=False, min_value=Decimal("0")
    )

    def validate_prompt(self, value):
        if not value.strip():
            raise serializers.ValidationError("A requirement is required.")
        return value.strip()


class AgentRequirementMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRequirementMessage
        fields = ("seq", "role", "content", "ts", "is_question", "questions")


class AgentRequirementListSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(source="object_uuid", read_only=True)
    can_build = serializers.BooleanField(read_only=True)
    run_count = serializers.IntegerField(source="runs.count", read_only=True)
    latest_run = serializers.SerializerMethodField()

    class Meta:
        model = AgentRequirement
        fields = (
            "uuid",
            "title",
            "status",
            "can_build",
            "spec_version",
            "turns",
            "total_cost_usd",
            "run_count",
            "latest_run",
            "created_at",
            "approved_at",
        )

    def get_latest_run(self, obj):
        """So the list shows whether the last build worked, not just that one
        happened."""
        run = obj.runs.order_by("-queued_at").first()
        if run is None:
            return None
        return {"uuid": str(run.object_uuid), "status": run.status}


class AgentRequirementDetailSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(source="object_uuid", read_only=True)
    can_build = serializers.BooleanField(read_only=True)
    messages = AgentRequirementMessageSerializer(many=True, read_only=True)
    runs = serializers.SerializerMethodField()

    class Meta:
        model = AgentRequirement
        fields = (
            "uuid",
            "title",
            "status",
            "can_build",
            "initial_prompt",
            "spec_markdown",
            "spec_version",
            "turns",
            "total_cost_usd",
            "is_thinking",
            "error_message",
            "created_at",
            "approved_at",
            "approved_by",
            "messages",
            "runs",
        )

    def get_runs(self, obj):
        return [
            {
                "uuid": str(run.object_uuid),
                "status": run.status,
                "queued_at": run.queued_at.isoformat() if run.queued_at else None,
            }
            for run in obj.runs.order_by("-queued_at")[:10]
        ]
