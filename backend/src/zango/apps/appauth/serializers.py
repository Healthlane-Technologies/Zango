from rest_framework import serializers

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

    class Meta:
        model = AppUserAuthToken
        fields = ["role", "created", "expiry"]
