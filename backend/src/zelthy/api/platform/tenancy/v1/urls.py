from django.urls import re_path, path, include

from .views import (
    AppViewAPIV1,
    AppDetailViewAPIV1,
    UserRoleViewAPIV1,
    UserRoleDetailViewAPIV1,
    UserViewAPIV1,
    UserDetailViewAPIV1,
    ThemeViewAPIV1,
    ThemeDetailViewAPIV1,
)

from zelthy.api.platform.permissions.v1 import urls as permissions_v1_urls
from zelthy.api.platform.packages.v1 import urls as packages_v1_urls
from zelthy.api.platform.tasks.v1 import urls as tasks_v1_urls
from zelthy.api.platform.codeassist.v1 import urls as codeassist_v1_urls


urlpatterns = [
    re_path(r"$", AppViewAPIV1.as_view(), name="apps-apiv1-appview"),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/$",
        AppDetailViewAPIV1.as_view(),
        name="apps-apiv1-appdetailview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/roles/$",
        UserRoleViewAPIV1.as_view(),
        name="apps-apiv1-roleview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/roles/(?P<role_id>[\w-]+)/$",
        UserRoleDetailViewAPIV1.as_view(),
        name="apps-apiv1-roledetailview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/users/$",
        UserViewAPIV1.as_view(),
        name="apps-apiv1-userview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/users/(?P<user_id>[\w-]+)/$",
        UserDetailViewAPIV1.as_view(),
        name="apps-apiv1-userdetailview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/themes/$",
        ThemeViewAPIV1.as_view(),
        name="apps-apiv1-themeview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/themes/(?P<theme_id>[\w-]+)/$",
        ThemeDetailViewAPIV1.as_view(),
        name="apps-apiv1-themedetailview",
    ),
    re_path(r"^(?P<app_uuid>[\w-]+)/packages/$", include(packages_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/tasks/", include(tasks_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/code-assist/", include(codeassist_v1_urls)),
    path("", include(permissions_v1_urls)),
]
