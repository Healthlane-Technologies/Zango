from rest_framework import serializers

from zango.apps.accesslogs.models import AppAccessLog
from zango.core.utils import get_datetime_str_in_tenant_timezone


class AccessLogSerializerModel(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    attempt_time = serializers.SerializerMethodField()
    session_expired_at = serializers.SerializerMethodField()

    def get_attempt_time(self, obj):
        if obj.attempt_time:
            return get_datetime_str_in_tenant_timezone(
                obj.attempt_time, self.context["tenant"]
            )
        return "NA"

    def get_session_expired_at(self, obj):
        if obj.session_expired_at:
            return get_datetime_str_in_tenant_timezone(
                obj.session_expired_at, self.context["tenant"]
            )

        return "NA"

    def get_user(self, obj):
        return f"{obj.user.name} ({obj.user.id})" if obj.user else "NA"

    def get_role(self, obj):
        return obj.role.name if obj.role else "NA"

    class Meta:
        model = AppAccessLog
        fields = [
            "id",
            "ip_address",
            "user",
            "username",
            "attempt_type",
            "attempt_time",
            "role",
            "user_agent",
            "is_login_successful",
            "session_expired_at",
        ]
