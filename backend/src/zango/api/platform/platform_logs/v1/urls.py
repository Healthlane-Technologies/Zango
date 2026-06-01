"""URL routing for Platform Logs v1.

Two patterns are exposed:

    in_app_urls   — mounted under /api/v1/apps/<app_uuid>/logs/
    admin_urls    — mounted under /api/v1/platform/logs/
"""

from django.urls import path

from .views import (
    ComponentListView,
    ConnectorListUpsertView,
    ConnectorTestView,
    DeepLinkView,
    FacetsView,
    LogBrowseView,
    LogTailView,
    StreamListView,
)


# In-app endpoints — gated by IsPlatformUserAllowedApp.
in_app_urls = [
    path("components/", ComponentListView.as_view(), name="platform-logs-components"),
    path("<str:component>/", LogBrowseView.as_view(), name="platform-logs-browse"),
    path("<str:component>/tail/", LogTailView.as_view(), name="platform-logs-tail"),
    path("<str:component>/streams/", StreamListView.as_view(), name="platform-logs-streams"),
    path("<str:component>/facets/", FacetsView.as_view(), name="platform-logs-facets"),
    path("<str:component>/deep-link/", DeepLinkView.as_view(), name="platform-logs-deep-link"),
]


# Platform-admin endpoints — gated by IsSuperAdminPlatformUser.
admin_urls = [
    path("connectors/", ConnectorListUpsertView.as_view(), name="platform-logs-connectors"),
    path("connectors/test/", ConnectorTestView.as_view(), name="platform-logs-connectors-test"),
]
