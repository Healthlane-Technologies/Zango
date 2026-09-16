from django.urls import path

from .views import AgentModeSettingsValidateView, AgentModeSettingsView


urlpatterns = [
    path("settings/", AgentModeSettingsView.as_view()),
    path("settings/validate/", AgentModeSettingsValidateView.as_view()),
]
