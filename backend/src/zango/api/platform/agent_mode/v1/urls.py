from django.urls import path

from .views import (
    AgentModeAvailabilityView,
    AgentRequirementApproveView,
    AgentRequirementDetailView,
    AgentRequirementDocumentFileView,
    AgentRequirementDocumentsView,
    AgentRequirementFlagsConfirmView,
    AgentRequirementListCreateView,
    AgentRequirementMessageView,
    AgentRequirementSpecFinalizeView,
    AgentRequirementSpecValidateView,
    AgentRequirementSpecView,
    AgentRunAbortView,
    AgentRunContinueView,
    AgentRunDetailView,
    AgentRunEventTailView,
    AgentRunListCreateView,
    AgentRunReportView,
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
        "requirements/<uuid:requirement_uuid>/spec/validate/",
        AgentRequirementSpecValidateView.as_view(),
    ),
    path(
        "requirements/<uuid:requirement_uuid>/flags/confirm/",
        AgentRequirementFlagsConfirmView.as_view(),
    ),
    path(
        "requirements/<uuid:requirement_uuid>/documents/",
        AgentRequirementDocumentsView.as_view(),
    ),
    path(
        "requirements/<uuid:requirement_uuid>/documents/<int:doc_id>/",
        AgentRequirementDocumentFileView.as_view(),
    ),
    path(
        "requirements/<uuid:requirement_uuid>/spec/finalize/",
        AgentRequirementSpecFinalizeView.as_view(),
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
    path("runs/<uuid:run_uuid>/continue/", AgentRunContinueView.as_view()),
    path("runs/<uuid:run_uuid>/report.html", AgentRunReportView.as_view()),
]
