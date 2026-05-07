"""
Typed exceptions for the Zango AI layer.
These allow callers to handle specific error conditions differently
(retry on rate limit, alert on budget, etc.)
"""


class ZangoAIError(Exception):
    """Base exception for all AI framework errors."""


class ProviderNotFound(ZangoAIError):
    """The requested provider slug is not registered."""

    def __init__(self, slug):
        self.slug = slug
        super().__init__(f"Provider '{slug}' is not registered.")


class ProviderDisabled(ZangoAIError):
    """The AppLLMProvider is disabled by admin."""

    def __init__(self, provider_name):
        self.provider_name = provider_name
        super().__init__(f"Provider '{provider_name}' is disabled.")


class ProviderConfigInvalid(ZangoAIError):
    """The provider config failed validation."""

    def __init__(self, message, field=None):
        self.field = field
        super().__init__(message)


class BudgetExceeded(ZangoAIError):
    """Monthly budget for this provider has been exceeded."""

    def __init__(self, provider_name, budget_limit):
        self.provider_name = provider_name
        self.budget_limit = budget_limit
        super().__init__(
            f"Monthly budget of ${budget_limit} exceeded for provider '{provider_name}'."
        )


class RateLimitExceeded(ZangoAIError):
    """Provider or model rate limit hit."""

    def __init__(self, message, retry_after_seconds=None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class LLMAPIError(ZangoAIError):
    """The LLM provider returned an API error. Wraps the original exception."""

    def __init__(self, message, status_code=None, original_error=None):
        super().__init__(message)
        self.status_code = status_code
        self.original_error = original_error


class LLMTimeoutError(ZangoAIError):
    """The LLM request timed out."""


class ModelNotAvailable(ZangoAIError):
    """The requested model is not enabled for this provider configuration."""

    def __init__(self, model_id, provider_name):
        self.model_id = model_id
        self.provider_name = provider_name
        super().__init__(
            f"Model '{model_id}' is not available for provider '{provider_name}'."
        )


class PromptNotFound(ZangoAIError):
    """The requested prompt name does not exist or is inactive."""

    def __init__(self, name):
        self.name = name
        super().__init__(f"Prompt '{name}' not found or inactive.")


class PromptRenderError(ZangoAIError):
    """A required template variable was not provided."""

    def __init__(self, missing_vars):
        self.missing_vars = missing_vars
        super().__init__(f"Missing template variables: {', '.join(missing_vars)}")


class AgentNotFound(ZangoAIError):
    """The requested agent name does not exist or is inactive."""

    def __init__(self, name):
        self.name = name
        super().__init__(f"Agent '{name}' not found or inactive.")


class AgentDisabled(ZangoAIError):
    """The agent exists but is disabled."""

    def __init__(self, name):
        self.name = name
        super().__init__(f"Agent '{name}' is disabled.")


class ToolNotFound(ZangoAIError):
    """The requested tool name is not in the registry."""

    def __init__(self, name):
        self.name = name
        super().__init__(f"Tool '{name}' not found in registry.")


class ToolExecutionError(ZangoAIError):
    """Tool execution failed."""


class ToolTimeout(ZangoAIError):
    """Tool execution exceeded its timeout."""

    def __init__(self, tool_name, timeout_seconds):
        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Tool '{tool_name}' timed out after {timeout_seconds}s.")


class OutputParseError(ZangoAIError):
    """LLM response could not be parsed as JSON."""


class OutputValidationError(ZangoAIError):
    """LLM response JSON does not match the configured output schema."""

    def __init__(self, message, field=None, errors=None):
        super().__init__(message)
        self.field = field
        self.errors = errors  # list of validation error dicts
