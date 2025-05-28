from django.urls import re_path

from zango.apps.shared.platformauth.views import (
    AppOpenIDLogin,
    OpenIDInitiateView,
    OpenIDValidationView,
    PlatformUserLoginView,
    PlatformUserLogoutView,
)


urlpatterns = [
    re_path(r"^login/", PlatformUserLoginView.as_view(), name="platform-login"),
    re_path(r"^logout/", PlatformUserLogoutView.as_view(), name="platform-logout"),
    re_path(
        r"^openid/initiate/(?P<provider>[\w-]+)/$",
        OpenIDInitiateView.as_view(),
        name="oidc-initiate",
    ),
    re_path(r"^openid/router/$", OpenIDValidationView.as_view(), name="oidc-validate"),
    re_path(r"^openid/login/$", AppOpenIDLogin.as_view(), name="oidc-login"),
]
