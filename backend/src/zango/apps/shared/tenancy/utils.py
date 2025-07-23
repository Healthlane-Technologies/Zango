from typing import List, Literal, Optional, Required, TypedDict

import pytz

from django_tenants.utils import schema_context


class PasswordReset(TypedDict, total=False):
    enabled: Required[bool]
    allowed_methods: List[Literal["email", "sms"]]
    by_code: bool
    by_email: bool
    login_after_reset: bool
    expiry: int
    max_attempts: int
    sms_hook: str
    email_hook: str


class PasswordPolicy(TypedDict):
    min_length: int
    require_uppercase: bool
    require_lowercase: bool
    require_numbers: bool
    require_special_chars: bool
    password_history_count: int
    password_expiry_days: int
    allow_change: bool
    reset: PasswordReset


class PasswordLoginMethod(TypedDict, total=False):
    enabled: bool
    forgot_password_enabled: bool
    password_reset_link_expiry_hours: int
    allowed_usernames: List[Literal["email", "phone"]]


class SSOLoginMethod(TypedDict):
    enabled: bool


class OIDCLoginMethod(TypedDict):
    enabled: bool


class OTPLoginMethod(TypedDict, total=False):
    enabled: Required[bool]
    allowed_methods: List[Literal["sms", "email"]]
    email_hook: str
    sms_hook: str


class LoginMethods(TypedDict):
    password: PasswordLoginMethod
    sso: SSOLoginMethod
    oidc: OIDCLoginMethod
    otp: OTPLoginMethod


class TwoFactorAuth(TypedDict, total=False):
    required: bool
    enforced_from: Optional[str]
    grace_period_days: Optional[int]
    allowed_methods: Optional[List[Literal["totp", "sms", "email"]]]
    skip_for_sso: Optional[bool]
    email_hook: str
    sms_hook: str


class SessionPolicy(TypedDict):
    max_concurrent_sessions: int
    force_logout_on_password_change: bool


class AuthConfigSchema(TypedDict, total=False):
    password_policy: PasswordPolicy
    login_methods: LoginMethods
    two_factor_auth: TwoFactorAuth
    session_policy: SessionPolicy


DEFAULT_AUTH_CONFIG: AuthConfigSchema = {
    "password_policy": {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": False,
        "password_history_count": 3,
        "password_expiry_days": 90,
        "allow_change": True,
        "reset": {
            "enabled": True,
            "method": ["email"],
            "expiry_hours": 2,
        },
    },
    "login_methods": {
        "password": {
            "enabled": True,
            "forgot_password_enabled": False,
            "allowed_usernames": ["email", "phone"],
        },
        "sso": {
            "enabled": False,
        },
        "oidc": {"enabled": False},
        "otp": {"enabled": False},
    },
    "two_factor_auth": {
        "required": False,
    },
}


def get_default_auth_config() -> AuthConfigSchema:
    return DEFAULT_AUTH_CONFIG


__all__ = [
    "TIMEZONES",
    "DATEFORMAT",
    "DATETIMEFORMAT",
]

TIMEZONES = [(tz, tz) for tz in pytz.all_timezones]

DATEFORMAT = (
    ("%d %b %Y", "04 Oct 2017"),
    ("%d %B %Y", "04 October 2017"),
    ("%d/%m/%Y", "04/10/2017"),
    ("%d/%m/%y", "04/10/17"),
    ("%m/%d/%y", "10/04/17"),
    ("%d/%m/%Y", "04/10/2017"),
)

DATETIMEFORMAT = (
    ("%d %b %Y %H:%M", "04 Oct 2017 13:48"),
    ("%d %b %Y %I:%M %p", "04 Oct 2017 01:48 PM"),
    ("%d %B %Y %H:%M", "04 October 2017 13:48"),
    ("%d %B %Y %I:%M %p", "04 October 2017 01:48 PM"),
    ("%d/%m/%Y %H:%M", "04/10/2017 13:48"),
    ("%d/%m/%y %I:%M %p", "04/10/17 01:48 PM"),
    ("%m/%d/%y %H:%M", "10/04/17 13:48"),
    ("%d/%m/%Y %I:%M %p", "04/10/2017 01:48 PM"),
)

DEFAULT_THEME_CONFIG = {
    "color": {"primary": "#5048ED", "secondary": "#E1D6AE", "background": "#ffffff"},
    "button": {
        "color": "#ffffff",
        "background": "#5048ED",
        "border_color": "#C7CED3",
        "border_radius": "10",
    },
    "typography": {"font_family": "Open Sans"},
}


def assign_policies_to_anonymous_user(schema_name):
    from zango.apps.appauth.models import UserRoleModel
    from zango.apps.permissions.models import PolicyModel

    with schema_context(schema_name):
        anonymous_users_role = UserRoleModel.objects.get(name="AnonymousUsers")
        anonymous_users_role.policies.add(
            PolicyModel.objects.get(name="AllowFromAnywhere")
        )
        anonymous_users_role.save()
