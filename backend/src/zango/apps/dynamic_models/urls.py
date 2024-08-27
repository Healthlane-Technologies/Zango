"""Defines which API URLs."""

from django.urls import re_path

from .views import DynamicView


urlpatterns = [
    re_path(r"^((?:[\w\-:.,]+/)*)$", DynamicView.as_view(), name="dynamic-app")
]
