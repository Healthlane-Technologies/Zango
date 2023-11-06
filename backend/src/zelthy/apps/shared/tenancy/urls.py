from django.urls import re_path

from .views import AppPanelView


urlpatterns = [re_path(r"^platform/", AppPanelView.as_view(), name="platform")]
