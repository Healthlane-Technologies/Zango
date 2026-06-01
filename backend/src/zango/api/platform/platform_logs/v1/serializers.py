"""Serializers for the Platform Logs API.

LogLine / LogStream / LogPage serializers wrap the connector dataclasses
(not Django models) so they're hand-rolled rather than ModelSerializer.

LogConnectorConfigSerializer is a regular ModelSerializer for the admin
upsert endpoint. The `config` JSON blob is validated by trying to build a
live connector — see `validate()`.
"""

from __future__ import annotations

from rest_framework import serializers

from zango.apps.platform_logs import connectors as connector_registry
from zango.apps.platform_logs.connectors.exceptions import ConnectorConfigError
from zango.apps.platform_logs.models import (
    Component,
    ConnectorType,
    LogConnectorConfig,
)


# ---------------------------------------------------------------------------
# Read serializers — wrap connector dataclasses
# ---------------------------------------------------------------------------


class LogStreamSerializer(serializers.Serializer):
    name = serializers.CharField()
    last_event_ts = serializers.DateTimeField(allow_null=True)
    first_event_ts = serializers.DateTimeField(allow_null=True)
    retention_in_days = serializers.IntegerField(allow_null=True)


class LogLineSerializer(serializers.Serializer):
    ts = serializers.DateTimeField()
    level = serializers.CharField()
    message = serializers.CharField()
    stream = serializers.CharField()
    structured = serializers.JSONField(allow_null=True)
    cursor_token = serializers.CharField(allow_blank=True)

    def to_representation(self, instance):
        return {
            "ts": instance.ts.isoformat() if instance.ts else None,
            "level": instance.level.value if hasattr(instance.level, "value") else instance.level,
            "message": instance.message,
            "stream": instance.stream,
            "structured": instance.structured,
            "cursor_token": instance.cursor_token,
        }


class CursorSerializer(serializers.Serializer):
    token = serializers.CharField()
    direction = serializers.CharField()

    def to_representation(self, instance):
        if instance is None:
            return None
        return {
            "token": instance.token,
            "direction": instance.direction.value
            if hasattr(instance.direction, "value")
            else instance.direction,
        }


class LogPageSerializer(serializers.Serializer):
    lines = LogLineSerializer(many=True)
    next_cursor = CursorSerializer(allow_null=True)
    has_more = serializers.BooleanField()

    def to_representation(self, instance):
        return {
            "lines": LogLineSerializer(instance.lines, many=True).data,
            "next_cursor": CursorSerializer(instance.next_cursor).data
            if instance.next_cursor
            else None,
            "has_more": instance.has_more,
        }


# ---------------------------------------------------------------------------
# Write serializer — connector config upsert
# ---------------------------------------------------------------------------


class LogConnectorConfigSerializer(serializers.ModelSerializer):
    """Serializer for GET/POST on /connectors/.

    Validates the `config` JSON by attempting to instantiate the connector
    class against it. A bad payload (missing region, malformed format, etc.)
    is rejected at the API boundary rather than at first read time.
    """

    class Meta:
        model = LogConnectorConfig
        fields = [
            "id",
            "environment",
            "component",
            "connector",
            "config",
            "is_active",
            "created_at",
            "modified_at",
        ]
        read_only_fields = ["id", "created_at", "modified_at"]

    def validate_environment(self, value: str) -> str:
        if not value or len(value) > 32:
            raise serializers.ValidationError("environment must be 1-32 chars.")
        return value

    def validate_component(self, value: str) -> str:
        valid = {c.value for c in Component}
        if value not in valid:
            raise serializers.ValidationError(
                f"component must be one of {sorted(valid)}"
            )
        return value

    def validate_connector(self, value: str) -> str:
        valid = {c.value for c in ConnectorType}
        if value not in valid:
            raise serializers.ValidationError(
                f"connector must be one of {sorted(valid)}"
            )
        return value

    def validate(self, attrs):
        """Round-trip the config through the connector factory to catch
        missing fields, bad formats, etc. before persisting."""
        connector_type = attrs.get("connector") or (
            self.instance.connector if self.instance else None
        )
        cfg = attrs.get("config", {}) or {}

        # Build a transient LogConnectorConfig in memory; do NOT save.
        stub = LogConnectorConfig(
            connector=connector_type or "",
            config=cfg,
        )
        try:
            connector_registry.build(stub)
        except ConnectorConfigError as exc:
            raise serializers.ValidationError({"config": str(exc)})
        return attrs
