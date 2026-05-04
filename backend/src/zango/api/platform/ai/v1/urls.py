from django.urls import path

from .views import (
    AgentDetailViewAPIV1,
    AgentDuplicateViewAPIV1,
    AgentSessionDetailViewAPIV1,
    AgentSessionsListViewAPIV1,
    AgentsListViewAPIV1,
    AgentTestViewAPIV1,
    AgentToggleViewAPIV1,
    AvailableProvidersViewAPIV1,
    ConfirmationDecideViewAPIV1,
    ConfirmationsListViewAPIV1,
    InvocationDetailViewAPIV1,
    InvocationListViewAPIV1,
    InvocationStatsViewAPIV1,
    PendingConfirmationsCountViewAPIV1,
    PromptCompareViewAPIV1,
    PromptDetailViewAPIV1,
    PromptsListViewAPIV1,
    PromptVersionDetailViewAPIV1,
    PromptVersionPromoteViewAPIV1,
    PromptVersionsListViewAPIV1,
    ProviderDetailViewAPIV1,
    ProviderResetBudgetViewAPIV1,
    ProvidersListViewAPIV1,
    ProviderToggleViewAPIV1,
    ProviderUsageViewAPIV1,
    ProviderValidateViewAPIV1,
    ToolDetailViewAPIV1,
    ToolSectionsViewAPIV1,
    ToolsListViewAPIV1,
    ToolSyncViewAPIV1,
)


urlpatterns = [
    # Available providers (registry metadata) — must come before <int:provider_id>
    path("providers/available/", AvailableProvidersViewAPIV1.as_view()),
    # Provider CRUD
    path("providers/", ProvidersListViewAPIV1.as_view()),
    path("providers/<int:provider_id>/", ProviderDetailViewAPIV1.as_view()),
    # Provider actions
    path(
        "providers/<int:provider_id>/validate/",
        ProviderValidateViewAPIV1.as_view(),
    ),
    path(
        "providers/<int:provider_id>/toggle/",
        ProviderToggleViewAPIV1.as_view(),
    ),
    path(
        "providers/<int:provider_id>/usage/",
        ProviderUsageViewAPIV1.as_view(),
    ),
    path(
        "providers/<int:provider_id>/reset-budget/",
        ProviderResetBudgetViewAPIV1.as_view(),
    ),
    # Prompt CRUD
    path("prompts/", PromptsListViewAPIV1.as_view()),
    path("prompts/<int:prompt_id>/", PromptDetailViewAPIV1.as_view()),
    # Prompt versions
    path("prompts/<int:prompt_id>/versions/", PromptVersionsListViewAPIV1.as_view()),
    path(
        "prompts/<int:prompt_id>/versions/<int:version_id>/",
        PromptVersionDetailViewAPIV1.as_view(),
    ),
    path(
        "prompts/<int:prompt_id>/versions/<int:version_id>/promote/",
        PromptVersionPromoteViewAPIV1.as_view(),
    ),
    # Prompt compare
    path("prompts/<int:prompt_id>/compare/", PromptCompareViewAPIV1.as_view()),
    # Agent CRUD
    path("agents/", AgentsListViewAPIV1.as_view()),
    path("agents/<int:agent_id>/", AgentDetailViewAPIV1.as_view()),
    path("agents/<int:agent_id>/toggle/", AgentToggleViewAPIV1.as_view()),
    path("agents/<int:agent_id>/duplicate/", AgentDuplicateViewAPIV1.as_view()),
    path("agents/<int:agent_id>/test/", AgentTestViewAPIV1.as_view()),
    # Agent memory sessions — must come after named action paths
    path(
        "agents/<int:agent_id>/sessions/",
        AgentSessionsListViewAPIV1.as_view(),
    ),
    path(
        "agents/<int:agent_id>/sessions/<str:session_id_str>/",
        AgentSessionDetailViewAPIV1.as_view(),
    ),
    # Tools — sync/sections must come before <int:tool_id>
    path("tools/sync/", ToolSyncViewAPIV1.as_view()),
    path("tools/sections/", ToolSectionsViewAPIV1.as_view()),
    path("tools/", ToolsListViewAPIV1.as_view()),
    path("tools/<int:tool_id>/", ToolDetailViewAPIV1.as_view()),
    # Confirmations — pending-count must come before <int:confirmation_id>
    path("confirmations/pending-count/", PendingConfirmationsCountViewAPIV1.as_view()),
    path("confirmations/", ConfirmationsListViewAPIV1.as_view()),
    path(
        "confirmations/<int:confirmation_id>/decide/",
        ConfirmationDecideViewAPIV1.as_view(),
    ),
    # Invocation logs — stats must come before <int:invocation_id>
    path("invocations/stats/", InvocationStatsViewAPIV1.as_view()),
    path("invocations/", InvocationListViewAPIV1.as_view()),
    path("invocations/<int:invocation_id>/", InvocationDetailViewAPIV1.as_view()),
]
