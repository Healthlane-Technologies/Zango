from rest_framework import serializers

from zango.apps.release.models import AppRelease


class AppReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppRelease
        fields = [
            "id",
            "version",
            "description",
            "status",
            "release_result",
        ]
