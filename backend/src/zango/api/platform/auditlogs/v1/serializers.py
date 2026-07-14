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
        # FK targets (PlatformUserModel, AppUserModel) can be hard-deleted
        # independently of LogEntry rows. Accessing the descriptor raises
        # DoesNotExist when the target is gone — guard so a single
        # dangling row can't 500 the whole audit-log endpoint.
        try:
            if obj.tenant_actor_id and obj.tenant_actor:
                return obj.tenant_actor.name
        except Exception:
            pass
        try:
            if obj.platform_actor_id and obj.platform_actor:
                return obj.platform_actor.name
        except Exception:
            pass
        return None

    def get_actor_type(self, obj):
        # Base type on FK id, not descriptor — id survives dangling refs.
        if obj.tenant_actor_id:
            return "tenant_actor"
        if obj.platform_actor_id:
            return "platform_actor"
        return None

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
