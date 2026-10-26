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
    EventKind,
)


def _auth_source(run):
    """How the CLI authenticated, from the run's session-init event.

    "none" means the Claude subscription login: nothing was billed, and the
    run's cost is only the API-equivalent figure. None when no init event is
    left (not started yet, or pruned).
    """
    data = (
        run.events.filter(kind=EventKind.INIT)
        .order_by("-seq")
        .values_list("data", flat=True)
        .first()
    )
    return data.get("api_key_source") if isinstance(data, dict) else None


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
            "checks",
            "pending_actions",
            "auth_source",
        )

    checks = serializers.SerializerMethodField()
    pending_actions = serializers.SerializerMethodField()
    auth_source = serializers.SerializerMethodField()

    def get_auth_source(self, obj):
        return _auth_source(obj)

    def get_pending_actions(self, obj):
        """What a WAITING build needs from the user (the history row shows it); [] otherwise."""
        return list(obj.pending_actions or []) if obj.status == "waiting" else []

    def get_checks(self, obj):
        """App Studio builds: how many checks passed, failed, or were not verified."""
        layers = ((obj.studio_report or {}).get("layers") or {}).values()
        statuses = [layer.get("status") for layer in layers]
        if not statuses:
            return None
        return {
            "total": len(statuses),
            "passed": statuses.count("pass"),
            "failed": statuses.count("fail"),
            "not_verified": statuses.count("skip"),
        }


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
            "report",
            "pending_actions",
            "requires_restart",
            "can_resume",
            "resumed_from",
            "auth_source",
        )

    can_resume = serializers.SerializerMethodField()
    report = serializers.SerializerMethodField()
    pending_actions = serializers.SerializerMethodField()
    auth_source = serializers.SerializerMethodField()

    def get_auth_source(self, obj):
        return _auth_source(obj)

    def get_pending_actions(self, obj):
        """What a WAITING build needs from the user; [] otherwise."""
        return list(obj.pending_actions or []) if obj.status == "waiting" else []

    def get_report(self, obj):
        """An App Studio build's checks and report (never the test users or their passwords).

        ``html_url`` is filled in by the detail view, which knows the app.
        """
        data = obj.studio_report or None
        if not data:
            return None
        report = data.get("report") or {}
        layers = data.get("layers") or {}
        skipped = data.get("skipped") or []
        return {
            "ok": bool(data.get("ok")),
            "bring_up_ok": bool(data.get("bring_up_ok")),
            "frontend": bool(data.get("frontend", True)),
            "frontend_reason": data.get("frontend_reason", ""),
            "verdict": report.get("verdict", ""),
            "not_verified": data.get("not_verified")
            or [s.get("layer") for s in skipped],
            "rounds": data.get("rounds", 0),
            "skipped": skipped,
            "layers": layers,
            "report": {
                "summary_md": report.get("summary_md", ""),
                "md_path": report.get("md_path", ""),
                "html_path": report.get("html_path", ""),
                "verdict": report.get("verdict", ""),
            },
            "html_url": None,
            # Kept for older clients.
            "summary_md": report.get("summary_md", ""),
            "html_path": report.get("html_path", ""),
            "md_path": report.get("md_path", ""),
            "checks": layers,
        }

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
    # Files the user attached to this message (chips in the chat; the file itself is
    # served by requirements/{uuid}/documents/{id}/).
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = AgentRequirementMessage
        fields = (
            "seq",
            "role",
            "content",
            "ts",
            "is_question",
            "questions",
            "preview_focus",
            "attachments",
        )

    def get_attachments(self, obj):
        return [
            {"id": d.pk, "name": d.name, "content_type": d.content_type, "size": d.size}
            for d in obj.attachments.all()
        ]


def _template_payload(obj):
    """What the panel shows about the template behind a requirement.

    The slug alone would make the UI carry its own copy of every template's
    display name, which then drifts from the pack.
    """
    template = obj.template
    if template is None:
        return None
    return {
        "slug": template.slug,
        "name": template.name,
        "one_liner": template.one_liner,
        "spec_format": template.spec_format,
        "version": template.version,
        "version_uuid": template.version_uuid,
    }


class AgentRequirementListSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(source="object_uuid", read_only=True)
    can_build = serializers.BooleanField(read_only=True)
    run_count = serializers.IntegerField(source="runs.count", read_only=True)
    latest_run = serializers.SerializerMethodField()
    template = serializers.SerializerMethodField()

    class Meta:
        model = AgentRequirement
        fields = (
            "uuid",
            "title",
            "status",
            "can_build",
            "template_slug",
            "template",
            "spec_format",
            "draft_revision",
            "preview_mode",
            "prototype_revision",
            "prototype_hash",
            "spec_version",
            "turns",
            "total_cost_usd",
            "run_count",
            "latest_run",
            "created_at",
            "approved_at",
        )

    def get_template(self, obj):
        return _template_payload(obj)

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
    template = serializers.SerializerMethodField()

    class Meta:
        model = AgentRequirement
        fields = (
            "uuid",
            "title",
            "status",
            "can_build",
            "template_slug",
            "template",
            "initial_prompt",
            "spec_markdown",
            "spec_format",
            "spec_is_draft",
            "draft_revision",
            "preview_mode",
            "prototype_revision",
            "prototype_hash",
            "validation_issues",
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

    def get_template(self, obj):
        return _template_payload(obj)

    def get_runs(self, obj):
        return [
            {
                "uuid": str(run.object_uuid),
                "status": run.status,
                "queued_at": run.queued_at.isoformat() if run.queued_at else None,
            }
            for run in obj.runs.order_by("-queued_at")[:10]
        ]
