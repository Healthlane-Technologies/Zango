from django.urls import re_path

from .views import DynamicPanelView, CodeAssistView


urlpatterns = [
    re_path(r"^platform/", DynamicPanelView.as_view(), name="platform"),
    re_path(r"^code-assist/(?P<app_uuid>[\w-]+)/$", CodeAssistView.as_view(), name="platform")
    ]
