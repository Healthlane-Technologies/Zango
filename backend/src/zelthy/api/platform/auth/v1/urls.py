from django.urls import re_path

from .views import PlatformUserViewAPIV1, PlatformUserDetailViewAPIV1


urlpatterns = [
    re_path(
        r"^platform-users/$",
        PlatformUserViewAPIV1.as_view(),
        name="platformauth-apiv1-userview",
    ),
    re_path(
        r"^platform-users/(?P<user_id>[\w-]+)/$",
        PlatformUserDetailViewAPIV1.as_view(),
        name="platformauth-apiv1-userdetailview",
    ),
]
