from django.urls import path, re_path

from .login import AppLoginViewAPIV1
from .login_with_code import ConfirmLoginCodeViewAPIV1, RequestLoginCodeViewAPIV1
from .logout import AppLogoutViewAPIV1
from .mfa import GetMFACodeViewAPIV1, MFAVerifyViewAPIV1
from .password import (
    PasswordChangeViewAPIV1,
    RequestResetPasswordViewAPIV1,
    ResetPasswordViewAPIV1,
    SetPasswordViewAPIV1,
)
from .role import SwitchRoleAPIV1, UserRoleViewAPIV1
from .saml import SAMLLoginInitViewV1, SAMLOpsApi, acs, metadata
from .session import AppSessionsViewAPIV1


urlpatterns = [
    path(
        "app/login/code/request/",
        RequestLoginCodeViewAPIV1.as_api_view(client="app"),
        name="request_login_code",
    ),
    path(
        "app/login/code/confirm/",
        ConfirmLoginCodeViewAPIV1.as_api_view(client="app"),
        name="confirm_login_code",
    ),
    path(
        "app/login/",
        AppLoginViewAPIV1.as_api_view(client="app"),
        name="app-login",
    ),
    path(
        "login/code/request/",
        RequestLoginCodeViewAPIV1.as_api_view(client="browser"),
        name="request_login_code",
    ),
    path(
        "login/code/confirm/",
        ConfirmLoginCodeViewAPIV1.as_api_view(client="browser"),
        name="confirm_login_code",
    ),
    path("login/", AppLoginViewAPIV1.as_api_view(client="browser"), name="app-login"),
    path(
        "app/logout/",
        AppLogoutViewAPIV1.as_api_view(client="app"),
        name="app-logout",
    ),
    path("logout/", AppLogoutViewAPIV1.as_api_view(client="browser"), name="logout"),
    path("role/set/", UserRoleViewAPIV1.as_api_view(client="browser"), name="set-role"),
    path("app/role/set/", UserRoleViewAPIV1.as_api_view(client="app"), name="set-role"),
    path("role/switch/", SwitchRoleAPIV1.as_view(), name="switch-role"),
    path("password/change/", PasswordChangeViewAPIV1.as_view(), name="change-password"),
    path(
        "mfa/getcode/",
        GetMFACodeViewAPIV1.as_api_view(client="browser"),
        name="mfa-authenticate-view",
    ),
    path(
        "app/mfa/getcode/",
        GetMFACodeViewAPIV1.as_api_view(client="app"),
        name="app-mfa-authenticate-view",
    ),
    path(
        "app/mfa/verify/",
        MFAVerifyViewAPIV1.as_api_view(client="app"),
        name="app-mfa-verify-view",
    ),
    path(
        "mfa/verify/",
        MFAVerifyViewAPIV1.as_api_view(client="browser"),
        name="mfa-verify-view",
    ),
    path(
        "password/set/",
        SetPasswordViewAPIV1.as_api_view(client="browser"),
        name="account_set_password",
    ),
    path(
        "app/password/set/",
        SetPasswordViewAPIV1.as_api_view(client="app"),
        name="app-account_set_password",
    ),
    path(
        "app/password/reset/request/",
        RequestResetPasswordViewAPIV1.as_api_view(client="app"),
        name="app-account_reset_password",
    ),
    path(
        "password/reset/request/",
        RequestResetPasswordViewAPIV1.as_api_view(client="browser"),
        name="account_reset_password",
    ),
    path(
        "app/password/reset/",
        ResetPasswordViewAPIV1.as_api_view(client="app"),
        name="app-reset-password-from-key",
    ),
    path(
        "password/reset/",
        ResetPasswordViewAPIV1.as_api_view(client="browser"),
        name="reset-password-from-key",
    ),
    path(
        "app/sessions/",
        AppSessionsViewAPIV1.as_api_view(client="app"),
        name="app-sessions",
    ),
    path(
        "sessions/",
        AppSessionsViewAPIV1.as_api_view(client="browser"),
        name="sessions",
    ),
    re_path(r"saml/metadata/(?P<saml_client_id>\d+)/$", metadata, name="saml-metadata"),
    re_path(r"saml/acs/(?P<saml_client_id>\d+)/", acs, name="saml-acs"),
    re_path(r"saml/init/", SAMLLoginInitViewV1.as_view(), name="fetch_saml_config"),
    re_path(r"saml/ops/", SAMLOpsApi.as_view(), name="saml-ops"),
]
