"""Defines which API URLs."""
from django.urls import re_path

from .views import (
    AppLogoutView,
    SwitchUserRoleView
)

urlpatterns = [
    re_path(
        r"^switch_role/(?P<role_id>\d+)/$",
        SwitchUserRoleView.as_view(),
        name="appuser-switch-role-view",
    ),
    re_path(r"^logout/", view=AppLogoutView.as_view(), name="app-logout-view")
]
