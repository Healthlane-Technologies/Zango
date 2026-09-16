from django.urls import path

from .views import PlatformGeneralSettingsView, SubdomainPreviewView


urlpatterns = [
    path("", PlatformGeneralSettingsView.as_view()),
    path("preview-subdomain/", SubdomainPreviewView.as_view()),
]
