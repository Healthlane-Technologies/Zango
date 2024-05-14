from django.urls import re_path

from zcore.apps.shared.platformauth.views import PlatformUserLoginView
from zcore.core.decorators import internal_access_only

urlpatterns = [
    re_path(r"^login/", internal_access_only(PlatformUserLoginView.as_view()), name="login"),
]