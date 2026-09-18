from django.urls import path

from .views import (
    AgentAppScaffoldCreateView,
    AgentAppScaffoldDetailView,
    AgentAppScaffoldRequirementView,
    AgentModeAvailabilityPlatformView,
    AgentModeSettingsValidateView,
    AgentModeSettingsView,
)


urlpatterns = [
    path("settings/", AgentModeSettingsView.as_view()),
    path("settings/validate/", AgentModeSettingsValidateView.as_view()),
    path("availability/", AgentModeAvailabilityPlatformView.as_view()),
    # Build with Agent — describe it, and the agent names and launches the app.
    path("scaffolds/", AgentAppScaffoldCreateView.as_view()),
    path("scaffolds/<uuid:scaffold_uuid>/", AgentAppScaffoldDetailView.as_view()),
    path(
        "scaffolds/<uuid:scaffold_uuid>/requirement/",
        AgentAppScaffoldRequirementView.as_view(),
    ),
]
