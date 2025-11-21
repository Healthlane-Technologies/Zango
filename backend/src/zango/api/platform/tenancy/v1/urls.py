from django.urls import include, path, re_path

from zango.api.platform.accesslogs.v1 import urls as accesslog_v1_urls
from zango.api.platform.auditlogs.v1 import urls as auditlog_v1_urls
from zango.api.platform.packages.v1 import urls as packages_v1_urls
from zango.api.platform.permissions.v1 import urls as permissions_v1_urls
from zango.api.platform.releases.v1 import urls as releases_v1_urls
from zango.api.platform.secrets.v1 import urls as secrets_v1_urls
from zango.api.platform.tasks.v1 import urls as tasks_v1_urls

from .views import (
    AppDetailViewAPIV1,
    AppViewAPIV1,
    SAMLProviderDetailViewAPIV1,
    SAMLProvidersViewAPIV1,
    ThemeDetailViewAPIV1,
    ThemeViewAPIV1,
    UserDetailViewAPIV1,
    UserRoleDetailViewAPIV1,
    UserRoleViewAPIV1,
    UserViewAPIV1,
)


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
    re_path(
        r"^(?P<app_uuid>[\w-]+)/saml-providers/$",
        SAMLProvidersViewAPIV1.as_view(),
        name="apps-apiv1-samlprovidersview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/saml-providers/(?P<saml_provider_id>[\w-]+)/$",
        SAMLProviderDetailViewAPIV1.as_view(),
        name="apps-apiv1-samlproviderdetailview",
    ),
    re_path(r"^(?P<app_uuid>[\w-]+)/packages/$", include(packages_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/tasks/", include(tasks_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/auditlog/", include(auditlog_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/access-logs/", include(accesslog_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/releases/", include(releases_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/secrets/", include(secrets_v1_urls)),
    path("", include(permissions_v1_urls)),
]
