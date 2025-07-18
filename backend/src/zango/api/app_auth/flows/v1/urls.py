from django.urls import path

from .login import AppLoginViewAPIV1, UserRoleViewAPIV1
from .login_with_code import ConfirmLoginCodeViewAPIV1, RequestLoginCodeViewAPIV1
from .logout import AppLogoutViewAPIV1
from .mfa import GetMFACodeViewAPIV1, MFAVerifyViewAPIV1
from .password import PasswordChangeViewAPIV1, SetPasswordViewAPIV1


urlpatterns = [
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
    path("logout/", AppLogoutViewAPIV1.as_api_view(client="browser"), name="logout"),
    path("role/change/", UserRoleViewAPIV1.as_view(), name="set-role"),
    path("password/change/", PasswordChangeViewAPIV1.as_view(), name="change-password"),
    path("mfa/getcode/", GetMFACodeViewAPIV1.as_view(), name="mfa-authenticate-view"),
    path(
        "mfa/verify/",
        MFAVerifyViewAPIV1.as_api_view(client="browser"),
        name="mfa-verify-view",
    ),
    path("password/set/", SetPasswordViewAPIV1.as_view(), name="account_set_password"),
]
