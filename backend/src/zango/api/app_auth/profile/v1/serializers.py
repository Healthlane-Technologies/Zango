from rest_framework import serializers

from zango.apps.appauth.models import AppUserModel


class ProfileSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = AppUserModel
        fields = ["name", "email", "mobile", "profile_pic"]

    def get_profile_pic(self, obj):
        if obj.profile_pic:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)
            return obj.profile_pic.url
        return None
