from rest_framework import serializers

from django.core.exceptions import ValidationError

from zango.apps.appauth.models import AppUserModel
from zango.apps.appauth.serializers import UserRoleSerializerModel
from zango.core.utils import get_auth_priority, get_datetime_str_in_tenant_timezone


def _get_twofa_can_enable(user, auth_config, tenant):
    """
    Returns (can_enable, issue_message) for enabling 2FA.
    Checks that a cross-channel 2FA method is available:
    the required 2FA channel must not be the same as the user's login channel,
    must have its config key set on the tenant, and the user must have
    the corresponding contact info.
    """
    twofa_config = auth_config.get("two_factor_auth", {})
    login_methods = getattr(tenant, "auth_config", {}).get("login_methods", {})

    otp = login_methods.get("otp", {})
    password = login_methods.get("password", {})

    otp_enabled = otp.get("enabled", False)
    otp_methods = otp.get("allowed_methods", [])

    email_is_login = (otp_enabled and "email" in otp_methods) or (
        password.get("enabled", False) and "email" in password.get("allowed_usernames", [])
    )
    sms_is_login = otp_enabled and "sms" in otp_methods

    if email_is_login and not sms_is_login:
        required_channels = ["sms"]
    elif sms_is_login and not email_is_login:
        required_channels = ["email"]
    else:
        # both channels used for login, SSO-only, or password-only — require both
        required_channels = ["sms", "email"]

    issues = []
    for channel in required_channels:
        if channel == "sms":
            if not twofa_config.get("sms_config_key"):
                issues.append("SMS two-factor authentication is not configured.")
            elif not user.mobile:
                issues.append("Your mobile number is required to enable two-factor authentication.")
        elif channel == "email":
            if not twofa_config.get("email_config_key"):
                issues.append("Email two-factor authentication is not configured.")
            elif not user.email:
                issues.append("Your email is required to enable two-factor authentication.")

    if issues:
        return False, " ".join(issues)
    return True, None


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
            can_enable, issue = _get_twofa_can_enable(self.instance, auth_config, tenant)
            auth_config["two_factor_auth"]["can_enable"] = can_enable
            if issue:
                auth_config["two_factor_auth"]["issue"] = issue
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
