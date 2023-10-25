from rest_framework import serializers
from zelthy.apps.shared.platformauth.models import PlatformUserModel
from zelthy.api.platform.tenancy.v1.serializers import TenantSerializerModel


class PlatformUserSerializerModel(serializers.ModelSerializer):
    apps = TenantSerializerModel(many=True)

    class Meta:
        model = PlatformUserModel
        fields = [
            "id",
            "name",
            "email",
            "apps",
            "is_superadmin",
            "is_active",
            "last_login",
            "created_at",
        ]
