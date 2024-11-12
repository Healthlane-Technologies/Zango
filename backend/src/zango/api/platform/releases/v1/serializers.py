from rest_framework import serializers

from zango.apps.release.models import AppRelease
from zango.core.utils import get_datetime_str_in_tenant_timezone


class AppReleaseSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = AppRelease
        fields = [
            "id",
            "version",
            "description",
            "status",
            "last_git_hash",
            "created_at",
        ]

    def get_created_at(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.created_at, self.context["tenant"]
        )
