from django.core.exceptions import ValidationError
from django.db import connection

from zango.core.utils import get_auth_priority


class UserAuthConfigValidationMixin:
    def validate_user_role_two_factor_not_overridden(
        self, auth_config, user, roles=None
    ):
        if not roles:
            roles = user.roles.filter(is_active=True)
        user_two_factor_auth_enabled = auth_config.get("two_factor_auth", {}).get(
            "required", True
        )
        for role in roles:
            if role.auth_config.get("two_factor_auth", {}):
                role_two_factor_auth = role.auth_config["two_factor_auth"]
                if (
                    role_two_factor_auth.get("required")
                    and not user_two_factor_auth_enabled
                ):
                    raise ValidationError(
                        f"Two-factor authentication is required for {role.name} role."
                    )

    def validate_tenant_two_factor_not_overridden(self, tenant, auth_config):
        try:
            getattr(tenant, "auth_config")
        except AttributeError:
            return
        if tenant.auth_config.get("two_factor_auth", {}).get("required"):
            if not auth_config.get("two_factor_auth", {}).get("required", True):
                raise ValidationError(
                    "Two-factor authentication is required for this tenant."
                )

    def validate_email_and_mobile_passed_if_2fa_enabled(
        self, auth_config, user, tenant, roles=None
    ):
        if not roles:
            roles = user.roles.filter(is_active=True)
        auth_priority = get_auth_priority(tenant=tenant, user=user)
        twofa_enabled = auth_priority.get("two_factor_auth", {}).get("required", False)
        for role in roles:
            role_twofa_config = get_auth_priority(
                tenant=tenant, user_role=role, policy="two_factor_auth"
            )
            if role_twofa_config.get("required", False):
                twofa_enabled = True
                break
        if auth_priority.get("two_factor_auth"):
            auth_priority["two_factor_auth"]["required"] = twofa_enabled
        else:
            auth_priority["two_factor_auth"] = {
                "required": twofa_enabled,
            }
        if twofa_enabled:
            if not user.email or not user.mobile:
                raise ValidationError(
                    "Mobile number and email are required to enable two-factor authentication."
                )

    def validate_email_and_phone_passed(self, user_auth_config, email, phone, tenant):
        try:
            getattr(tenant, "auth_config")
        except AttributeError:
            return
        tenant_auth_config = tenant.auth_config
        login_methods = tenant_auth_config.get("login_methods")
        if login_methods.get("otp", {}).get("enabled", False):
            allowed_methods = login_methods["otp"].get("allowed_methods")
            if ["email"] == allowed_methods and not email:
                raise ValidationError(
                    "Email is required since email based login is enabled"
                )
            if ["sms"] == allowed_methods and not phone:
                raise ValidationError(
                    "Phone is required since SMS based login is enabled"
                )

        if login_methods.get("password", {}).get("enabled", False):
            allowed_methods = login_methods["password"].get("allowed_usernames", [])
            if ["email"] == allowed_methods and not email:
                raise ValidationError(
                    "Email is required since email based login is enabled"
                )
            if ["phone"] == allowed_methods and not phone:
                raise ValidationError(
                    "Phone is required since SMS based login is enabled"
                )

    def validate_auth_config(self, auth_config, user, roles=None, tenant=None):
        if not tenant:
            tenant = connection.tenant
        self.validate_user_role_two_factor_not_overridden(auth_config, user, roles)
        self.validate_tenant_two_factor_not_overridden(tenant, auth_config)
        self.validate_email_and_mobile_passed_if_2fa_enabled(
            auth_config, user, tenant, roles
        )
        self.validate_email_and_phone_passed(
            auth_config, user.email, user.mobile, tenant
        )
        return auth_config
