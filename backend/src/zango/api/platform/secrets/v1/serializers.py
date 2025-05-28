from rest_framework import serializers

from zango.apps.secrets.models import SecretsModel
from zango.core.utils import get_datetime_str_in_tenant_timezone


class SecretSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    modified_at = serializers.SerializerMethodField()
    value = serializers.CharField(write_only=True, required=False)
    id = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = SecretsModel
        fields = [
            "id",
            "key",
            "is_active",
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

    def update(self, instance, validated_data):
        if "value" not in validated_data:
            current_value = instance.get_unencrypted_val()
            validated_data["value"] = current_value
            instance = super().update(instance, validated_data)
            return instance
        else:
            return super().update(instance, validated_data)
