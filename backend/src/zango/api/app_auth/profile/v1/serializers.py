from rest_framework import serializers

from django.core.exceptions import ValidationError

from zango.apps.appauth.models import AppUserModel
from zango.apps.appauth.serializers import UserRoleSerializerModel
from zango.core.utils import get_auth_priority, get_datetime_str_in_tenant_timezone


class ProfileSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    roles = UserRoleSerializerModel(many=True)
    auth_config = serializers.JSONField(required=False)
    last_password_changed = serializers.SerializerMethodField()

    class Meta:
        model = AppUserModel
        fields = [
            "name",
            "email",
            "mobile",
            "profile_pic",
            "roles",
            "auth_config",
            "last_password_changed",
        ]

    def get_last_password_changed(self, obj):
        try:
            from django_tenants.utils import schema_context

            with schema_context(self.context.get("tenant").schema_name):
                from zango.apps.appauth.models import OldPasswords

                return get_datetime_str_in_tenant_timezone(
                    OldPasswords.objects.filter(user=obj)
                    .latest("password_datetime")
                    .password_datetime,
                    tenant=self.context.get("tenant"),
                )
        except Exception:
            import traceback

            traceback.print_exc()
            return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tenant = self.context.get("tenant")
        auth_config = get_auth_priority(tenant=tenant, user=instance)
        twofa_enabled = auth_config.get("two_factor_auth", {}).get("required", False)
        for role in instance.roles.all():
            role_twofa_config = get_auth_priority(
                tenant=tenant, user_role=role, policy="two_factor_auth"
            )
            if role_twofa_config.get("required", False):
                twofa_enabled = True
                break
        auth_config["two_factor_auth"]["required"] = twofa_enabled
        if not twofa_enabled:
            if not self.instance.mobile or not self.instance.email:
                auth_config["two_factor_auth"]["can_enable"] = False
                auth_config["two_factor_auth"]["issue"] = (
                    "Mobile number and email are required to enable two-factor authentication."
                )
            else:
                auth_config["two_factor_auth"]["can_enable"] = False
        else:
            can_disable_twofa = True
            try:
                self.instance.validate_auth_config(
                    {"two_factor_auth": {"required": False}},
                    self.instance,
                    self.instance.roles.all(),
                    tenant,
                )
            except ValidationError:
                can_disable_twofa = False

            # Check if user can disable two_factor_auth
            auth_config["two_factor_auth"]["can_disable"] = can_disable_twofa

        data["auth_config"] = auth_config

        return data

    def get_profile_pic(self, obj):
        if obj.profile_pic:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)
            return obj.profile_pic.url
        return None
