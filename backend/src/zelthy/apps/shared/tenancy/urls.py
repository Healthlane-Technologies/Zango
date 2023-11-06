from django.urls import re_path

from .views import DynamicPanelView


urlpatterns = [
    re_path(r"^platform/", DynamicPanelView.as_view(), name="platform"),
]
