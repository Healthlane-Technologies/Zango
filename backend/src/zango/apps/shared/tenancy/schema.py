from typing import List, Literal, Optional, TypedDict


try:
    from typing import Required
except ImportError:
    from typing_extensions import Required


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
    email_content: str
    email_subject: str
    email_config_key: str
    sms_template_id: str
    sms_config_key: str
    sms_extra_data: str


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


class SAMLProvider(TypedDict):
    id: int
    label: str


class SSOLoginMethod(TypedDict):
    enabled: bool
    providers: List[SAMLProvider]


class OIDCProvider(TypedDict):
    id: int
    provider: str
    name: str
    enabled: bool


class OIDCLoginMethod(TypedDict):
    enabled: bool
    providers: List[OIDCProvider]


class OTPLoginMethod(TypedDict, total=False):
    enabled: Required[bool]
    allowed_methods: List[Literal["sms", "email"]]
    email_hook: str
    sms_hook: str
    email_content: str
    email_subject: str
    email_config_key: str
    sms_template_id: str
    sms_config_key: str
    sms_extra_data: str
    otp_expiry: int


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
            "allowed_methods": ["email"],
            "expiry": 7200,
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
            "providers": [],
        },
        "oidc": {"enabled": False, "providers": []},
        "otp": {"enabled": False},
    },
    "two_factor_auth": {
        "required": False,
    },
}


def get_default_auth_config() -> AuthConfigSchema:
    return DEFAULT_AUTH_CONFIG
