from rest_framework import serializers

from zango.apps.appauth.models import AppUserModel


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUserModel
        fields = ["name", "email", "mobile"]
