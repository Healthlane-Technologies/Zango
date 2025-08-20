from rest_framework import serializers


class UserAuthConfigValidationMixin:
    def validate_user_role_two_factor_not_overridden(self, auth_config, roles):
        if not roles:
            return
        user_two_factor_auth_enabled = auth_config.get("two_factor_auth", {}).get(
            "required"
        )
        for role in roles:
            if role.auth_config.get("two_factor_auth", {}):
                role_two_factor_auth = role.auth_config["two_factor_auth"]
                if (
                    role_two_factor_auth.get("required")
                    and not user_two_factor_auth_enabled
                ):
                    raise serializers.ValidationError(
                        f"Two-factor authentication is required for {role.name} role."
                    )
