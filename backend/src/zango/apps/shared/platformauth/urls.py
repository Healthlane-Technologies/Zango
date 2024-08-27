from django.urls import re_path

from zango.apps.shared.platformauth.views import (
    PlatformUserLoginView,
    PlatformUserLogoutView,
)


urlpatterns = [
    re_path(r"^login/", PlatformUserLoginView.as_view(), name="platform-login"),
    re_path(r"^logout/", PlatformUserLogoutView.as_view(), name="platform-logout"),
]
