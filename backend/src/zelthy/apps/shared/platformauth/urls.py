from django.urls import re_path

from .views import (
    PlatformUserLoginAPIV1,
    PlatformUserLoginView,
    PlatformUserProfileAPIV1,
)


urlpatterns = [
    re_path(r"^login/", PlatformUserLoginView.as_view(), name="platform-login"),
    re_path(
        r"^api/v1/login/",
        PlatformUserLoginAPIV1.as_view(),
        name="platform-api-v1-login",
    ),
    # url(
    #     regex=r'^api/v1/register-user/',
    #     view=PlatformUserRegisterAPIV1.as_view(),
    #     name='platform-api-v1-registeruser'
    # ),
    re_path(
        r"^api/v1/profile/",
        PlatformUserProfileAPIV1.as_view(),
        name="platform-api-v1-userprofile",
    ),
]
