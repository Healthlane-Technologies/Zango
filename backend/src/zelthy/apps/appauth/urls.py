"""Defines which API URLs."""
from django.urls import re_path

from .views import (
    AppLogoutView,
)

urlpatterns = [
    re_path(r"^logout/", view=AppLogoutView.as_view(), name="app-logout-view")
]
