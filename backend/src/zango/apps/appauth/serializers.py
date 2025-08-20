from rest_framework import serializers

from zango.core.utils import get_datetime_str_in_tenant_timezone

from .models import AppUserAuthToken, AppUserModel, UserRoleModel


class UserRoleSerializerModel(serializers.ModelSerializer):
    class Meta:
        model = UserRoleModel
        fields = "__all__"


class AppUserSerializerModel(serializers.ModelSerializer):
    class Meta:
        model = AppUserModel
        fields = "__all__"


class AppUserAuthTokenSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.name", read_only=True)
    created = serializers.SerializerMethodField()
    expiry = serializers.SerializerMethodField()

    def get_created(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.created, tenant=self.context.get("tenant")
        )

    def get_expiry(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.expiry, tenant=self.context.get("tenant")
        )

    class Meta:
        model = AppUserAuthToken
        fields = ["role", "created", "expiry"]
