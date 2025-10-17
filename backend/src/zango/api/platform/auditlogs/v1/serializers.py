from rest_framework import serializers

from zango.apps.auditlogs.models import LogEntry
from zango.core.utils import get_datetime_str_in_current_timezone


class AuditLogSerializerModel(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    actor_type = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()
    object_uuid = serializers.SerializerMethodField()
    object_type = serializers.SerializerMethodField()

    def get_action(self, obj):
        return obj.get_action_display().capitalize()

    def get_timestamp(self, obj):
        return get_datetime_str_in_current_timezone(
            obj.timestamp, self.context["tenant"]
        )

    def get_actor(self, obj):
        return (
            obj.tenant_actor.name
            if obj.tenant_actor
            else obj.platform_actor.name
            if obj.platform_actor
            else None
        )

    def get_actor_type(self, obj):
        return (
            "tenant_actor"
            if obj.tenant_actor
            else "platform_actor"
            if obj.platform_actor
            else None
        )

    def get_object_uuid(self, obj):
        if obj.object_ref is not None:
            return str(obj.object_ref.object_uuid)

    def get_object_type(self, obj):
        return obj.content_type.model

    class Meta:
        model = LogEntry
        fields = [
            "id",
            "actor",
            "actor_type",
            "action",
            "object_id",
            "object_uuid",
            "object_type",
            "timestamp",
            "changes",
        ]
