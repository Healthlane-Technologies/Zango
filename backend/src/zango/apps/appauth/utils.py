from typing import List, Literal, Required, TypedDict

from zango.apps.shared.tenancy.utils import PasswordPolicy


class TwoFactorAuth(TypedDict, total=False):
    required: Required[bool]
    allowed_methods: List[Literal["email", "sms", "totp"]]


class UserRoleAuthConfig(TypedDict, total=False):
    password_policy: PasswordPolicy
    allow_password_auth: bool
    two_factor_auth: TwoFactorAuth


class SSOIdentity(TypedDict):
    provider: str
    identity_id: str


class AppUserAuthConfig(TypedDict, total=False):
    preferred_login_method: Literal["password", "sso", "2fa_only", "biometric"]
    two_factor_auth: TwoFactorAuth
    sso_identities: List[SSOIdentity]
    redirect_url: Required[str]


USER_ROLE_AUTH_CONFIG: UserRoleAuthConfig = {}
APP_USER_AUTH_CONFIG: AppUserAuthConfig = {
    "preferred_login_method": "password",
    "two_factor_auth": {
        "required": False,
    },
    "redirect_url": "/frame/router/",
}
