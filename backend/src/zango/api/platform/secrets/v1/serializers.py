from rest_framework import serializers

from zango.apps.secrets.models import SecretsModel
from zango.core.utils import get_datetime_str_in_tenant_timezone


class SecretSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    modified_at = serializers.SerializerMethodField()
    value = serializers.CharField(write_only=True, required=False)
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = SecretsModel
        fields = [
            "id",
            "label",
            "active",
            "value",
            "created_at",
            "modified_at",
        ]

    def get_created_at(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.created_at, self.context["tenant"]
        )

    def get_modified_at(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.modified_at, self.context["tenant"]
        )
