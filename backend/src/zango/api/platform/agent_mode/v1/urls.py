from django.urls import path

from .views import (
    AgentModeAvailabilityView,
    AgentRequirementApproveView,
    AgentRequirementDetailView,
    AgentRequirementListCreateView,
    AgentRequirementMessageView,
    AgentRequirementSpecView,
    AgentRunAbortView,
    AgentRunDetailView,
    AgentRunEventTailView,
    AgentRunListCreateView,
    AgentRunResumeView,
)


urlpatterns = [
    path("availability/", AgentModeAvailabilityView.as_view()),
    # Phase 1 — requirement gathering
    path("requirements/", AgentRequirementListCreateView.as_view()),
    path("requirements/<uuid:requirement_uuid>/", AgentRequirementDetailView.as_view()),
    path(
        "requirements/<uuid:requirement_uuid>/messages/",
        AgentRequirementMessageView.as_view(),
    ),
    path(
        "requirements/<uuid:requirement_uuid>/spec/",
        AgentRequirementSpecView.as_view(),
    ),
    path(
        "requirements/<uuid:requirement_uuid>/approve/",
        AgentRequirementApproveView.as_view(),
    ),
    # Phase 2 — development runs
    path("runs/", AgentRunListCreateView.as_view()),
    path("runs/<uuid:run_uuid>/", AgentRunDetailView.as_view()),
    path("runs/<uuid:run_uuid>/event-tail/", AgentRunEventTailView.as_view()),
    path("runs/<uuid:run_uuid>/abort/", AgentRunAbortView.as_view()),
    path("runs/<uuid:run_uuid>/resume/", AgentRunResumeView.as_view()),
]
