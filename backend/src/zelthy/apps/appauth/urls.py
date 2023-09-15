"""Defines which API URLs."""
from django.urls import re_path

from .views import AppUserLoginView, AppUserLandingView, AppLogoutView

urlpatterns = [
    re_path(r"^login/", AppUserLoginView.as_view(), name="app-login-view"),
    re_path(
        r"^user-landing/",
        AppUserLandingView.as_view(),
        name="appuser-landing-view",
    ),
    re_path(r"^logout/", view=AppLogoutView.as_view(), name="app-logout-view"),
]
