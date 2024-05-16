from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt

from zango.apps.shared.platformauth.views import (
    PlatformUserLoginView,
    PlatformUserLogoutView,
)


urlpatterns = [
    re_path(r"^login/", PlatformUserLoginView.as_view(), name="platform-login"),
    re_path(r"^logout/", PlatformUserLogoutView.as_view(), name="platform-logout"),
]
