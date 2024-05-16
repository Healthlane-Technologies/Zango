from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt

from zango.apps.shared.platformauth.views import PlatformUserLoginView
from zango.core.decorators import internal_access_only


urlpatterns = [
    re_path(
        r"^login/", internal_access_only(PlatformUserLoginView.as_view()), name="login"
    ),
]
