from django.urls import path

from .views import (
    PlatformAIAccountCheckView,
    PlatformAIAccountDetailView,
    PlatformAIAccountsView,
    PlatformAIAccountValidateView,
)


urlpatterns = [
    path("", PlatformAIAccountsView.as_view()),
    path("check/", PlatformAIAccountCheckView.as_view()),
    path("<uuid:account_uuid>/", PlatformAIAccountDetailView.as_view()),
    path("<uuid:account_uuid>/validate/", PlatformAIAccountValidateView.as_view()),
]
