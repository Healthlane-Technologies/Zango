"""
Zango AI Framework — Public API for application developers.

Usage:
    from zango.ai import get_provider, LLMMessage

    provider = get_provider("claude-primary")
    response = provider.complete(
        messages=[LLMMessage(role="user", content="Hello")],
        model="claude-sonnet-4-20250514",
    )
    print(response.content)
    print(response.usage.input_tokens)
    print(response.cost_usd)
"""

from zango.ai.exceptions import OutputParseError, OutputValidationError
from zango.ai.providers.base import (
    LLMFile,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
    LLMToolCall,
    LLMToolDef,
    LLMUsage,
)


def get_provider(name: str):
    """
    Get a configured provider client by its AppLLMProvider name.

    Returns a ProviderClient that wraps the raw provider with:
    - Automatic invocation logging
    - Cost computation and budget tracking
    - Rate limit checking
    - Error type normalization
    """
    from zango.ai.client import ProviderClient
    from zango.apps.ai.models import AppLLMProvider

    app_provider = AppLLMProvider.objects.get(name=name)
    return ProviderClient(app_provider)


def get_prompt(name: str):
    """
    Get the active version of a prompt by its name.

    Returns an AppLLMPromptVersion instance with a .render(**kwargs) method.

    Usage:
        from zango.ai import get_prompt

        prompt = get_prompt("assessment-question-system")
        rendered = prompt.render(
            question_count=10,
            employee_role="pharmacovigilance specialist",
        )
    """
    from zango.ai.exceptions import PromptNotFound
    from zango.apps.ai.models import AppLLMPrompt

    try:
        prompt = AppLLMPrompt.objects.select_related("active_version").get(
            name=name, is_active=True
        )
    except AppLLMPrompt.DoesNotExist:
        raise PromptNotFound(name)

    if not prompt.active_version:
        raise PromptNotFound(name)

    return prompt.active_version


def get_agent(name: str):
    """
    Get a configured agent by name. Returns AgentClient with .run() method.

    Usage:
        from zango.ai import get_agent

        agent = get_agent("assessment-question-generator")
        response = agent.run(
            variables={"question_count": 10, "employee_role": "nurse"},
        )
        print(response.content)
    """
    from zango.ai.agent_client import AgentClient
    from zango.ai.exceptions import AgentNotFound
    from zango.apps.ai.models import AppLLMAgent

    try:
        agent = AppLLMAgent.objects.select_related(
            "provider", "system_prompt__active_version", "user_prompt__active_version"
        ).get(name=name)
    except AppLLMAgent.DoesNotExist:
        raise AgentNotFound(name)

    return AgentClient(agent)


__all__ = [
    "get_provider",
    "get_prompt",
    "get_agent",
    "LLMFile",
    "LLMMessage",
    "LLMResponse",
    "LLMStreamChunk",
    "LLMToolCall",
    "LLMToolDef",
    "LLMUsage",
    "OutputParseError",
    "OutputValidationError",
]
