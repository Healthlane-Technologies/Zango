from typing import List, Literal, TypedDict


try:
    from typing import Required
except ImportError:
    from typing_extensions import Required

from zango.apps.shared.tenancy.utils import PasswordPolicy


class TwoFactorAuth(TypedDict, total=False):
    required: Required[bool]
    allowed_methods: List[Literal["email", "sms", "totp"]]


class UserRoleAuthConfig(TypedDict, total=False):
    password_policy: PasswordPolicy
    two_factor_auth: TwoFactorAuth
    redirect_url: Required[str]


class SSOIdentity(TypedDict):
    provider: str
    identity_id: str


class AppUserAuthConfig(TypedDict, total=False):
    two_factor_auth: TwoFactorAuth
    sso_identities: List[SSOIdentity]


USER_ROLE_AUTH_CONFIG: UserRoleAuthConfig = {"redirect_url": "/frame/router/"}
APP_USER_AUTH_CONFIG: AppUserAuthConfig = {}


def get_default_user_role_auth_config():
    return USER_ROLE_AUTH_CONFIG


def get_default_app_user_auth_config():
    return APP_USER_AUTH_CONFIG
