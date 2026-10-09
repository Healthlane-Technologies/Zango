from django.urls import include, path, re_path

from zango.api.platform.accesslogs.v1 import urls as accesslog_v1_urls
from zango.api.platform.ai.v1 import urls as ai_v1_urls
from zango.api.platform.auditlogs.v1 import urls as auditlog_v1_urls
from zango.api.platform.packages.v1 import urls as packages_v1_urls
from zango.api.platform.permissions.v1 import urls as permissions_v1_urls
from zango.api.platform.releases.v1 import urls as releases_v1_urls
from zango.api.platform.secrets.v1 import urls as secrets_v1_urls
from zango.api.platform.tasks.v1 import urls as tasks_v1_urls

from .oidc_views import (
    AppUserIdentitiesViewAPIV1,
    OIDCDiscoverViewAPIV1,
    OIDCProviderDetailViewAPIV1,
    OIDCProvidersViewAPIV1,
    OIDCProviderTestViewAPIV1,
)
from .views import (
    AppDetailViewAPIV1,
    AppStatusActionView,
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
        r"^(?P<app_uuid>[\w-]+)/status/(?P<action>[\w-]+)/$",
        AppStatusActionView.as_view(),
        name="apps-apiv1-appstatusaction",
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
    re_path(
        r"^(?P<app_uuid>[\w-]+)/oidc-providers/$",
        OIDCProvidersViewAPIV1.as_view(),
        name="apps-apiv1-oidcprovidersview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/oidc-providers/discover/$",
        OIDCDiscoverViewAPIV1.as_view(),
        name="apps-apiv1-oidcdiscoverview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/oidc-providers/(?P<oidc_provider_id>\d+)/$",
        OIDCProviderDetailViewAPIV1.as_view(),
        name="apps-apiv1-oidcproviderdetailview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/oidc-providers/(?P<oidc_provider_id>\d+)/test/$",
        OIDCProviderTestViewAPIV1.as_view(),
        name="apps-apiv1-oidcprovidertestview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/users/(?P<user_id>\d+)/identities/$",
        AppUserIdentitiesViewAPIV1.as_view(),
        name="apps-apiv1-useridentitiesview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/users/(?P<user_id>\d+)/identities/(?P<identity_id>\d+)/$",
        AppUserIdentitiesViewAPIV1.as_view(),
        name="apps-apiv1-useridentitydetailview",
    ),
    re_path(r"^(?P<app_uuid>[\w-]+)/packages/$", include(packages_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/tasks/", include(tasks_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/auditlog/", include(auditlog_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/access-logs/", include(accesslog_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/releases/", include(releases_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/secrets/", include(secrets_v1_urls)),
    re_path(r"^(?P<app_uuid>[\w-]+)/ai/", include(ai_v1_urls)),
    path("", include(permissions_v1_urls)),
]
