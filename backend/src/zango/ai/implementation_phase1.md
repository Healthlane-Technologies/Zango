Here's the implementation prompt scoped to the Provider layer:

---

```markdown
# Zango AI Framework — Backend Implementation: Provider Layer

## Context

Zango is a Django-based multi-tenant framework for building enterprise business applications. 
It uses:
- PostgreSQL with schema-per-tenant isolation
- Gunicorn (sync WSGI) for the app server
- Celery + Redis for background tasks
- Django ORM with `DynamicModelBase` as the base class for all tenant-scoped models
- An "App Panel" (admin UI) at the platform level for managing apps, users, packages, etc.

We are building an **AI/LLM Operations layer** natively into Zango. This layer gives enterprise apps managed LLM access with full audit trails, cost tracking, prompt versioning, and governance.

This prompt covers **Phase 1: The Provider Layer** — the foundational abstraction that connects  Zango apps to LLM providers (Anthropic, OpenAI, Azure OpenAI, AWS Bedrock).

## Architecture Overview

The Provider system has two tiers:

### Tier 1: Platform-Level Provider Registry (Code-defined)
- Provider definitions (Anthropic, OpenAI, etc.) are defined in Python code within the framework
- Each provider class knows how to: make completion calls, stream responses, count tokens, 
  compute costs, handle errors, and format tool definitions
- These are NOT database models — they are registered Python classes, similar to how Django 
  discovers admin classes
- They appear in the App Panel as "Available Providers" that an app can configure

### Tier 2: App-Level Provider Configuration (Database-stored)
- When an app admin wants to use Anthropic, they "configure" it — providing API key, 
  selecting models, setting rate limits, budgets
- This creates an `AppLLMProvider` record in the app's tenant schema
- Multiple configurations per provider are allowed (e.g., "claude-production" with Opus, 
  "claude-fast" with Haiku, different API keys for different teams)
- Agents reference these app-level configurations, never the raw provider classes

```
Platform Registry (code)          App Configuration (DB)
┌─────────────────────┐          ┌──────────────────────────────┐
│ AnthropicProvider    │───────→  │ AppLLMProvider               │
│ OpenAIProvider       │───────→  │  - name: "claude-primary"    │
│ AzureOpenAIProvider  │          │  - provider: "anthropic"     │
│ BedrockProvider      │          │  - api_key: <encrypted>      │
│                      │          │  - default_model: "claude-.. │
│ (Python classes,     │          │  - rate_limit: 100/min       │
│  framework code)     │          │  - monthly_budget: $500      │
└─────────────────────┘          │  - enabled: true             │
                                  └──────────────────────────────┘
```

## File Structure

All AI framework code lives under `zango/ai/`:

```
zango/
├── ai/
│   ├── __init__.py              # Public API: get_agent, get_provider
│   ├── providers/
│   │   ├── __init__.py          # Provider registry + autodiscovery
│   │   ├── base.py              # BaseLLMProvider abstract class
│   │   ├── registry.py          # PROVIDER_REGISTRY, register/lookup functions
│   │   ├── anthropic.py         # AnthropicProvider implementation
│   │   ├── openai.py            # OpenAIProvider implementation
│   │   ├── azure_openai.py      # AzureOpenAIProvider implementation
│   │   └── bedrock.py           # BedrockProvider implementation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── provider.py          # AppLLMProvider, AppLLMProviderModel DB models
│   │   └── invocation.py        # AppLLMInvocation log model (basic, for provider-level logging)
│   ├── encryption.py            # API key encryption/decryption utilities | this can be done using already available secrets feature
│   ├── exceptions.py            # AI-specific exception classes
│   ├── cost.py                  # Cost computation utilities
│   └── api/
│       ├── __init__.py
│       ├── serializers.py       # DRF serializers for provider CRUD
│       └── views.py             # API views for App Panel provider management
```

## Detailed Implementation Specifications

### 1. Provider Registry (`zango/ai/providers/registry.py`)

```python
"""
Global registry of available LLM provider classes.
Provider classes register themselves on import via the @register_provider decorator.
The registry is provider_slug → ProviderClass mapping.
"""

PROVIDER_REGISTRY: dict[str, type["BaseLLMProvider"]] = {}

def register_provider(slug: str, display_name: str, icon: str = None):
    """
    Class decorator that registers a provider class in the global registry.
    
    Usage:
        @register_provider("anthropic", "Anthropic", icon="anthropic.svg")
        class AnthropicProvider(BaseLLMProvider):
            ...
    """

def get_provider_class(slug: str) -> type["BaseLLMProvider"]:
    """Look up a provider class by slug. Raises ProviderNotFound if not registered."""

def get_available_providers() -> list[dict]:
    """
    Returns metadata about all registered providers for the App Panel UI.
    Each entry includes: slug, display_name, icon, supported_models list,
    required_config_fields, optional_config_fields.
    """
```

### 2. Base Provider (`zango/ai/providers/base.py`)

```python
"""
Abstract base class for all LLM providers. Each provider must implement these methods.
The base class handles common concerns: logging, cost computation, rate limit tracking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator, Optional, Any

@dataclass
class LLMMessage:
    role: str           # "system", "user", "assistant", "tool"
    content: Any        # str or list of content blocks (for multimodal)

@dataclass  
class LLMToolDef:
    name: str
    description: str
    input_schema: dict  # JSON Schema

@dataclass
class LLMUsage:
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int = 0   # Anthropic prompt caching
    cache_read_tokens: int = 0       # Anthropic prompt caching

@dataclass
class LLMToolCall:
    id: str
    name: str
    input: dict

@dataclass
class LLMResponse:
    content: str                         # Text content of the response
    tool_calls: list[LLMToolCall]        # Tool use requests from the LLM
    stop_reason: str                     # "end_turn", "tool_use", "max_tokens"
    usage: LLMUsage
    model: str                           # Actual model used (resolved)
    raw_response: Any                    # The original SDK response object
    latency_ms: int                      # Total request time
    time_to_first_token_ms: int | None   # For streaming

@dataclass
class LLMStreamChunk:
    delta_text: str | None               # Incremental text
    delta_tool_call: dict | None         # Incremental tool call
    is_final: bool = False               # Last chunk
    usage: LLMUsage | None = None        # Only on final chunk
    stop_reason: str | None = None       # Only on final chunk

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Subclasses must implement:
    - complete()          synchronous completion
    - stream()            streaming completion (generator)
    - validate_config()   check that config/credentials are valid
    - get_models()        return list of available models
    - estimate_tokens()   estimate token count for messages
    """
    
    # -- Class-level metadata (set by subclass) --
    slug: str                    # "anthropic", "openai", etc.
    display_name: str            # "Anthropic", "OpenAI", etc.
    supported_models: list[dict] # [{"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", ...}]
    
    # Each model entry should contain:
    # {
    #     "id": "claude-sonnet-4-20250514",             # API model identifier
    #     "name": "Claude Sonnet 4",                  # Display name
    #     "context_window": 200000,                   # Max context tokens
    #     "max_output_tokens": 8192,                  # Max output tokens
    #     "input_cost_per_mtok": 3.00,                # Cost per million input tokens (USD)
    #     "output_cost_per_mtok": 15.00,              # Cost per million output tokens (USD)
    #     "supports_tools": True,                     # Whether model supports tool use
    #     "supports_vision": True,                    # Whether model supports image input
    #     "supports_streaming": True,                 # Whether model supports streaming
    # }
    
    # -- Config fields declaration (for Panel UI form generation) --
    config_fields: list[dict]
    # Each field: {"name": "api_key", "type": "secret", "required": True, "label": "API Key"}
    # Types: "secret" (encrypted), "string", "url", "select", "integer", "boolean"
    # "secret" type fields are encrypted before DB storage and never returned in API responses
    
    def __init__(self, config: dict):
        """
        config comes from AppLLMProvider.config (decrypted secrets).
        Each provider validates and uses the config fields it needs.
        """
        self.config = config
    
    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        model: str,
        tools: list[LLMToolDef] | None = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        system: str | None = None,
        stop_sequences: list[str] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Synchronous completion. Blocks until the full response is received.
        Must handle provider-specific request formatting and response parsing.
        Must measure and return latency_ms.
        Must raise typed exceptions (see exceptions section below).
        """
    
    @abstractmethod
    def stream(
        self,
        messages: list[LLMMessage],
        model: str,
        tools: list[LLMToolDef] | None = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        system: str | None = None,
        stop_sequences: list[str] | None = None,
        **kwargs,
    ) -> Iterator[LLMStreamChunk]:
        """
        Streaming completion. Yields chunks as they arrive.
        The final chunk must have is_final=True with usage and stop_reason.
        """
    
    @abstractmethod
    def validate_config(self) -> tuple[bool, str | None]:
        """
        Validate that the provider config is correct and credentials work.
        Makes a minimal API call (e.g., list models or a tiny completion).
        Returns (True, None) on success, (False, "error message") on failure.
        Called from the App Panel when admin saves a provider config.
        """
    
    @abstractmethod
    def get_models(self) -> list[dict]:
        """
        Return the list of available models for this provider.
        Can be static (from supported_models) or dynamic (API call to list models).
        """
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.
        Used for pre-flight checks (will this fit in context window?).
        Should use the provider's tokenizer if available, or a reasonable approximation.
        """
    
    def compute_cost(self, usage: LLMUsage, model: str) -> float:
        """
        Compute cost in USD for a given usage.
        Default implementation uses the model's cost_per_mtok from supported_models.
        Can be overridden for providers with complex pricing (e.g., Bedrock).
        """
        model_info = next((m for m in self.supported_models if m["id"] == model), None)
        if not model_info:
            return 0.0
        input_cost = (usage.input_tokens / 1_000_000) * model_info["input_cost_per_mtok"]
        output_cost = (usage.output_tokens / 1_000_000) * model_info["output_cost_per_mtok"]
        return round(input_cost + output_cost, 6)
    
    def format_tools_for_api(self, tools: list[LLMToolDef]) -> list[dict]:
        """
        Convert generic LLMToolDef objects to provider-specific tool format.
        Default implementation returns Anthropic format. OpenAI provider overrides this.
        """
```

### 3. Anthropic Provider (`zango/ai/providers/anthropic.py`)

```python
"""
Anthropic provider implementation using the official `anthropic` Python SDK.
Supports: Claude Opus, Sonnet, Haiku model families.
Handles: prompt caching, tool use, streaming, extended thinking.
"""

@register_provider("anthropic", "Anthropic", icon="anthropic.svg")
class AnthropicProvider(BaseLLMProvider):
    
    slug = "anthropic"
    display_name = "Anthropic"
    
    supported_models = [
        {
            "id": "claude-opus-4-20250514",
            "name": "Claude Opus 4",
            "context_window": 200000,
            "max_output_tokens": 32000,
            "input_cost_per_mtok": 15.00,
            "output_cost_per_mtok": 75.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "claude-sonnet-4-20250514",
            "name": "Claude Sonnet 4",
            "context_window": 200000,
            "max_output_tokens": 16000,
            "input_cost_per_mtok": 3.00,
            "output_cost_per_mtok": 15.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "claude-haiku-4-5-20251001",
            "name": "Claude Haiku 4.5",
            "context_window": 200000,
            "max_output_tokens": 8192,
            "input_cost_per_mtok": 0.80,
            "output_cost_per_mtok": 4.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
    ]
    
    config_fields = [
        {"name": "api_key", "type": "secret", "required": True, "label": "API Key",
         "help_text": "Your Anthropic API key (starts with sk-ant-)"},
        {"name": "default_model", "type": "select", "required": True, 
         "label": "Default Model", "options_from": "supported_models"},
        {"name": "max_retries", "type": "integer", "required": False, 
         "label": "Max Retries", "default": 2},
        {"name": "timeout_seconds", "type": "integer", "required": False,
         "label": "Timeout (seconds)", "default": 120},
    ]
    
    def __init__(self, config):
        super().__init__(config)
        import anthropic
        self._client = anthropic.Anthropic(
            api_key=config["api_key"],
            max_retries=config.get("max_retries", 2),
            timeout=config.get("timeout_seconds", 120),
        )
    
    def complete(self, messages, model, tools=None, temperature=1.0, 
                 max_tokens=4096, system=None, **kwargs):
        """
        Implementation notes:
        - Convert LLMMessage list to Anthropic's message format
        - system prompt goes in the `system` parameter, not in messages
        - tools get converted via format_tools_for_api()
        - Measure latency with time.monotonic()
        - Map Anthropic's response.stop_reason to our standard stop reasons
        - Extract usage from response.usage
        - Handle anthropic.APIError subtypes and raise our typed exceptions
        """
    
    def stream(self, messages, model, tools=None, temperature=1.0,
               max_tokens=4096, system=None, **kwargs):
        """
        Implementation notes:
        - Use self._client.messages.stream() context manager
        - Yield LLMStreamChunk for each text delta and tool call delta
        - Track cumulative usage from stream events
        - Final chunk gets is_final=True with complete usage
        """
    
    def validate_config(self):
        """
        Make a minimal completion call:
        messages=[{"role": "user", "content": "Hi"}], max_tokens=1
        If it succeeds, credentials are valid.
        """
    
    def get_models(self):
        return self.supported_models
    
    def estimate_tokens(self, text):
        """
        Use anthropic.Anthropic().count_tokens(text) if available,
        otherwise approximate at 4 chars per token.
        """
    
    def compute_cost(self, usage, model):
        """
        Override to handle prompt caching pricing:
        - cache_creation_tokens: 1.25x input price
        - cache_read_tokens: 0.1x input price
        """
```

### 4. OpenAI Provider (`zango/ai/providers/openai.py`)

```python
"""
OpenAI provider implementation using the official `openai` Python SDK.
Supports: GPT-4o, GPT-4o-mini, o1, o3 model families.
"""

@register_provider("openai", "OpenAI", icon="openai.svg")
class OpenAIProvider(BaseLLMProvider):
    
    config_fields = [
        {"name": "api_key", "type": "secret", "required": True, "label": "API Key"},
        {"name": "organization", "type": "string", "required": False, "label": "Organization ID"},
        {"name": "default_model", "type": "select", "required": True, 
         "label": "Default Model", "options_from": "supported_models"},
    ]
    
    """
    Implementation notes:
    - OpenAI uses `functions` / `tools` format (different from Anthropic)
    - format_tools_for_api() must convert LLMToolDef to OpenAI's tool format:
      {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}
    - Response parsing: choices[0].message.content, choices[0].message.tool_calls
    - Stop reason mapping: "stop" → "end_turn", "tool_calls" → "tool_use", "length" → "max_tokens"
    - Usage: response.usage.prompt_tokens, response.usage.completion_tokens
    """
```

### 5. Azure OpenAI Provider (`zango/ai/providers/azure_openai.py`)

```python
"""
Azure OpenAI provider. Uses the openai SDK with azure-specific config.
Key difference: requires azure_endpoint and api_version in addition to api_key.
Model IDs are deployment names, not standard model names.
"""

@register_provider("azure_openai", "Azure OpenAI", icon="azure.svg")
class AzureOpenAIProvider(BaseLLMProvider):
    
    config_fields = [
        {"name": "api_key", "type": "secret", "required": True, "label": "API Key"},
        {"name": "azure_endpoint", "type": "url", "required": True, 
         "label": "Azure Endpoint", "help_text": "https://your-resource.openai.azure.com/"},
        {"name": "api_version", "type": "string", "required": True,
         "label": "API Version", "default": "2024-10-21"},
        {"name": "default_deployment", "type": "string", "required": True,
         "label": "Default Deployment Name"},
    ]
    
    """
    Implementation notes:
    - Uses openai.AzureOpenAI client instead of openai.OpenAI
    - Model parameter is the deployment name, not a standard model ID
    - Cost computation may differ — Azure pricing is per-deployment
    - Admin must manually set cost_per_mtok since Azure pricing varies by agreement
    """
```

### 6. Database Models (`zango/ai/models/provider.py`)

```python
"""
Tenant-scoped database models for app-level LLM provider configuration.
These models live in each app's schema (not the shared/public schema).
They store the app admin's configuration of available providers.
"""


class AppLLMProvider(models.Model):
    """
    An app's configured connection to an LLM provider.
    One app can have multiple configurations (e.g., different API keys, models).
    """
    
    # Identity
    name = models.CharField(max_length=100, unique=True,
        help_text="Admin-friendly name, e.g., 'claude-primary', 'gpt4-fallback'")
    description = models.TextField(blank=True, default="")
    
    # Links to the platform-level provider registry
    provider_slug = models.CharField(max_length=50,
        help_text="References the registered provider class, e.g., 'anthropic', 'openai'")
    
    # Configuration (encrypted secrets + plain config merged)
    # Stored as JSON. Secret fields (identified by provider's config_fields type="secret")
    # are encrypted before storage using Fernet symmetric encryption.
    # The encryption key is derived from Django's SECRET_KEY + a provider-specific salt.
    config_encrypted = models.BinaryField(
        help_text="Encrypted JSON containing all config including API keys")
    
    # The default model to use when agents don't specify one
    default_model = models.CharField(max_length=100,
        help_text="Default model ID from the provider's supported_models list")
    
    # Rate limiting
    rate_limit_rpm = models.IntegerField(null=True, blank=True,
        help_text="Max requests per minute. Null = no limit.")
    rate_limit_tpm = models.IntegerField(null=True, blank=True,
        help_text="Max tokens per minute. Null = no limit.")
    
    # Budget controls
    monthly_budget_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Monthly spending cap in USD. Null = no limit.")
    budget_alert_threshold = models.DecimalField(
        max_digits=5, decimal_places=2, default=80.00,
        help_text="Alert when this percentage of monthly budget is consumed")
    current_month_spend_usd = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Running total of spend for current month. Reset on 1st.")
    budget_reset_day = models.IntegerField(default=1,
        help_text="Day of month to reset the budget counter")
    
    # Status
    is_enabled = models.BooleanField(default=True)
    is_validated = models.BooleanField(default=False,
        help_text="True if validate_config() succeeded at least once")
    last_validated_at = models.DateTimeField(null=True, blank=True)
    validation_error = models.TextField(null=True, blank=True,
        help_text="Last validation error message, if any")
    
    # Usage stats (updated periodically, not real-time)
    total_invocations = models.IntegerField(default=0)
    total_input_tokens = models.BigIntegerField(default=0)
    total_output_tokens = models.BigIntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(..., null=True, on_delete=models.SET_NULL)
    
    class Meta:
        app_label = 'dynamic_models'  # or whatever Zango uses for tenant models
        ordering = ['name']
    
    def get_provider_class(self):
        """Returns the registered provider class for this config's provider_slug."""
        from zango.ai.providers.registry import get_provider_class
        return get_provider_class(self.provider_slug)
    
    def get_client(self):
        """
        Instantiates and returns a configured provider client.
        Decrypts config, creates provider instance.
        Raises ProviderDisabled if is_enabled is False.
        Raises BudgetExceeded if monthly budget is blown.
        """
        if not self.is_enabled:
            raise ProviderDisabled(self.name)
        if self.monthly_budget_usd and self.current_month_spend_usd >= self.monthly_budget_usd:
            raise BudgetExceeded(self.name, self.monthly_budget_usd)
        
        config = self._decrypt_config()
        provider_cls = self.get_provider_class()
        return provider_cls(config)
    
    def _decrypt_config(self) -> dict:
        """Decrypt config_encrypted and return as dict."""
        from zango.ai.encryption import decrypt_config
        return decrypt_config(self.config_encrypted)
    
    def record_usage(self, usage: "LLMUsage", cost: float):
        """
        Atomically update usage counters.
        Uses F() expressions to avoid race conditions.
        """
        from django.db.models import F
        AppLLMProvider.objects.filter(pk=self.pk).update(
            total_invocations=F('total_invocations') + 1,
            total_input_tokens=F('total_input_tokens') + usage.input_tokens,
            total_output_tokens=F('total_output_tokens') + usage.output_tokens,
            total_cost_usd=F('total_cost_usd') + cost,
            current_month_spend_usd=F('current_month_spend_usd') + cost,
        )
    
    def check_budget(self) -> dict:
        """
        Returns budget status:
        {"within_budget": True/False, "used": 123.45, "limit": 500.00, "pct": 24.69}
        """


class AppLLMProviderModel(DynamicModelBase):
    """
    Tracks which models are enabled for a given provider configuration.
    Allows admins to restrict which models are available to agents.
    Also allows overriding cost rates (e.g., for enterprise agreements with custom pricing).
    """
    
    provider = models.ForeignKey(AppLLMProvider, on_delete=models.CASCADE,
        related_name='enabled_models')
    
    model_id = models.CharField(max_length=100,
        help_text="The model identifier, e.g., 'claude-sonnet-4-20250514'")
    display_name = models.CharField(max_length=100)
    
    # Cost overrides (null = use provider class defaults)
    input_cost_per_mtok_override = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text="Override input cost per million tokens. Null = use default.")
    output_cost_per_mtok_override = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text="Override output cost per million tokens. Null = use default.")
    
    is_enabled = models.BooleanField(default=True)
    
    # Per-model rate limits (more granular than provider-level)
    rate_limit_rpm = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('provider', 'model_id')
```

### 7. Invocation Log (`zango/ai/models/invocation.py`)

```python
"""
Every LLM call made through the framework is logged here.
This is the audit trail. It captures everything: what was sent, what came back, 
who triggered it, how much it cost, and how long it took.

In Phase 1 (provider layer), we log at the raw completion level.
In later phases, this model gets extended with agent_id, prompt_version_id, 
conversation_session_id, etc.
"""

class AppLLMInvocation(DynamicModelBase):
    """Immutable log entry for every LLM API call."""
    
    # Which provider configuration was used
    provider = models.ForeignKey(AppLLMProvider, on_delete=models.SET_NULL, null=True)
    provider_name = models.CharField(max_length=100,
        help_text="Denormalized — preserved even if provider is deleted")
    provider_slug = models.CharField(max_length=50)
    model = models.CharField(max_length=100,
        help_text="The actual model used for this call")
    
    # Request
    request_messages = models.JSONField(
        help_text="The full messages array sent to the LLM")
    request_system = models.TextField(null=True, blank=True,
        help_text="System prompt, if any")
    request_tools = models.JSONField(null=True, blank=True,
        help_text="Tool definitions sent to the LLM")
    request_params = models.JSONField(default=dict,
        help_text="temperature, max_tokens, etc.")
    
    # Response
    response_content = models.TextField(null=True, blank=True,
        help_text="Text content of the response")
    response_tool_calls = models.JSONField(null=True, blank=True,
        help_text="Tool calls requested by the LLM")
    stop_reason = models.CharField(max_length=20, null=True)
    
    # Usage & Cost
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cache_creation_tokens = models.IntegerField(default=0)
    cache_read_tokens = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Performance
    latency_ms = models.IntegerField(null=True)
    time_to_first_token_ms = models.IntegerField(null=True)
    
    # Context — who/what triggered this
    triggered_by = models.CharField(max_length=20, choices=[
        ('user', 'User action (request/response)'),
        ('celery', 'Background task'),
        ('cron', 'Scheduled task'),
        ('system', 'System/internal'),
    ], default='user')
    user = models.ForeignKey(..., null=True, on_delete=models.SET_NULL,
        help_text="The app user who triggered this, if applicable")
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
        ('rate_limited', 'Rate Limited'),
        ('budget_exceeded', 'Budget Exceeded'),
    ], default='success')
    error_message = models.TextField(null=True, blank=True)
    error_type = models.CharField(max_length=100, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Future: these will be populated when agent/prompt layers are built
    # agent_id = models.ForeignKey('AppLLMAgent', null=True, ...)
    # prompt_version_id = models.ForeignKey('AppLLMPromptVersion', null=True, ...)
    # conversation_session_id = models.ForeignKey('AppLLMConversationSession', null=True, ...)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
```

### 8. API Key Encryption (`zango/ai/encryption.py`)

```python
"""
Encryption utilities for storing API keys and other secrets.
Uses Fernet symmetric encryption with a key derived from Django's SECRET_KEY.

IMPORTANT: 
- API keys are encrypted before storage and decrypted only when needed
- Decrypted keys are NEVER returned in API responses
- The encryption key derivation uses PBKDF2 with a provider-specific salt
"""

# Use: cryptography.fernet.Fernet
# Key derivation: PBKDF2HMAC from Django's SECRET_KEY + "zango-ai-provider-keys" salt
# 
# Functions:
# - encrypt_config(config_dict: dict, secret_field_names: list[str]) -> bytes
#   Takes the full config dict, encrypts values of secret fields, returns encrypted blob
#
# - decrypt_config(encrypted_blob: bytes) -> dict
#   Returns the full config dict with secrets in plaintext
#
# - mask_config(config_dict: dict, secret_field_names: list[str]) -> dict
#   Returns config with secret values replaced by "sk-ant-****...****"
#   Used for API responses to the panel
```

### 9. Exception Classes (`zango/ai/exceptions.py`)

```python
"""
Typed exceptions for the AI layer. These allow callers to handle
specific error conditions differently (retry on rate limit, alert on budget, etc.)
"""

class ZangoAIError(Exception):
    """Base exception for all AI framework errors."""

class ProviderNotFound(ZangoAIError):
    """The requested provider slug is not registered."""

class ProviderDisabled(ZangoAIError):
    """The AppLLMProvider is disabled by admin."""

class ProviderConfigInvalid(ZangoAIError):
    """The provider config failed validation."""

class BudgetExceeded(ZangoAIError):
    """Monthly budget for this provider has been exceeded."""

class RateLimitExceeded(ZangoAIError):
    """Provider or model rate limit hit. Includes retry_after_seconds if available."""
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
```

### 10. App Panel API (`zango/ai/api/views.py`)

The App Panel needs these endpoints to manage providers:

```python
"""
REST API endpoints for the App Panel's provider management UI.
All endpoints are scoped to the current tenant (app).
Authentication: Session auth (panel admin user).
"""

# GET  /api/v1/ai/providers/available/
# Returns: List of all registered provider classes with their metadata
# (slug, display_name, config_fields, supported_models)
# This is READ from the PROVIDER_REGISTRY, not the database
# Used to populate the "Add Provider" dropdown in the panel

# GET  /api/v1/ai/providers/
# Returns: List of configured AppLLMProvider instances for this app
# Includes: name, provider_slug, default_model, is_enabled, is_validated,
#           usage stats, budget status
# EXCLUDES: decrypted API keys (shows masked version only)

# POST /api/v1/ai/providers/
# Creates a new AppLLMProvider configuration
# Body: {name, provider_slug, config: {api_key: "sk-...", default_model: "...", ...}}
# On save: encrypts secret fields, optionally runs validate_config()
# Returns: created provider (with masked secrets)

# GET  /api/v1/ai/providers/<id>/
# Returns: single provider detail with usage stats and budget info

# PUT  /api/v1/ai/providers/<id>/
# Updates provider config. If config contains secret fields with masked values
# (e.g., "sk-ant-****"), those fields are NOT updated (keeps existing encrypted value).
# Only updates secrets when a new plaintext value is provided.

# POST /api/v1/ai/providers/<id>/validate/
# Runs validate_config() against the provider. Returns success/failure.
# Updates is_validated and last_validated_at fields.

# POST /api/v1/ai/providers/<id>/toggle/
# Enables or disables the provider. Body: {is_enabled: true/false}

# DELETE /api/v1/ai/providers/<id>/
# Soft-deletes (marks disabled + appends "[deleted]" to name) rather than hard delete.
# Hard delete only if provider has zero invocations.

# GET  /api/v1/ai/providers/<id>/usage/
# Returns usage/cost breakdown:
# - Daily cost for the last 30 days
# - Per-model breakdown
# - Budget status (used/limit/percentage)
# - Total invocations, tokens, cost

# GET  /api/v1/ai/invocations/
# Returns: paginated list of invocation logs
# Filters: provider_id, status, date_range, user_id, triggered_by
# Each entry is summary view (no full request/response messages)

# GET  /api/v1/ai/invocations/<id>/
# Returns: full invocation detail including request_messages, response, etc.
# This is the "audit drill-down" view

# POST /api/v1/ai/providers/<id>/reset-budget/
# Manually resets current_month_spend_usd to 0
# Requires admin confirmation
```

### 11. Public API for App Developers (`zango/ai/__init__.py`)

```python
"""
Public API for application developers using the AI framework.
This is what app code imports and uses.
"""

def get_provider(name: str) -> "ProviderClient":
    """
    Get a configured provider client by its AppLLMProvider name.
    
    Usage:
        from zango.ai import get_provider
        
        provider = get_provider("claude-primary")
        response = provider.complete(
            messages=[LLMMessage(role="user", content="Hello")],
            model="claude-sonnet-4-20250514",
        )
        print(response.content)
        print(response.usage.input_tokens)
        print(response.cost)
    
    The returned client wraps the raw provider with:
    - Automatic invocation logging
    - Cost computation and budget tracking
    - Rate limit checking
    - Error type normalization
    """

class ProviderClient:
    """
    Wrapper around a BaseLLMProvider instance that adds framework concerns.
    App developers interact with this, not the raw provider.
    """
    
    def __init__(self, app_provider: AppLLMProvider):
        self._app_provider = app_provider
        self._client = app_provider.get_client()
    
    def complete(self, messages, model=None, **kwargs) -> LLMResponse:
        """
        1. Resolve model (use default if not specified)
        2. Check rate limits
        3. Check budget
        4. Call provider.complete()
        5. Compute cost
        6. Log invocation (AppLLMInvocation.objects.create(...))
        7. Update provider usage counters
        8. Return LLMResponse (with cost attached)
        
        On error:
        - Log the failed invocation with status='error'
        - Raise typed exception
        """
    
    def stream(self, messages, model=None, **kwargs) -> Iterator[LLMStreamChunk]:
        """Same as complete() but streaming. Logs on stream completion."""
    
    def complete_async(self, messages, model=None, **kwargs) -> str:
        """
        Dispatches completion to a Celery task. Returns task_id.
        The Celery task calls complete() synchronously.
        Result stored in AppLLMInvocation.
        """
```

## Behavioral Requirements

### Budget Enforcement
- Before every LLM call, check `current_month_spend_usd < monthly_budget_usd`
- If budget is exceeded, raise `BudgetExceeded` — do NOT make the API call
- When spend crosses `budget_alert_threshold` percentage, log a warning
  (alert mechanism will be added in later phases)
- Budget counter resets automatically on `budget_reset_day` of each month
  (implement as a check at call time: if current day >= reset_day and last reset was last month, reset)

### Rate Limit Enforcement  
- Use a sliding window counter in Redis (if available) or database
- Track both RPM (requests per minute) and TPM (tokens per minute)
- On rate limit hit from our side: raise `RateLimitExceeded` immediately
- On rate limit hit from provider API: parse retry-after header, raise `RateLimitExceeded` 
  with `retry_after_seconds`

### Encryption
- API keys must NEVER be stored in plaintext in the database
- API keys must NEVER appear in API responses (always masked)
- API keys must NEVER appear in log files or error messages
- Decryption happens only at the moment of making an LLM call, in memory

### Invocation Logging
- Every LLM call MUST produce an invocation log entry, even on failure
- Log entries are immutable — never updated after creation (append-only)
- The full request messages are stored (for audit). In later phases, we may add
  an option to redact PII before logging
- Response content is stored in full

## Testing Requirements

### Unit Tests
- Provider registry: register, lookup, list, not-found
- Encryption: round-trip encrypt/decrypt, masked output
- Cost computation: all provider types, with and without overrides
- Budget checking: within budget, at threshold, exceeded, reset logic
- Each provider's message format conversion (mock the SDK client)

### Integration Tests
- Create AppLLMProvider via API, verify encrypted storage
- Validate provider config (with mocked SDK)
- Make a completion call through ProviderClient, verify invocation log created
- Budget exceeded scenario: verify call is blocked and logged
- Update provider config with masked secrets: verify original secret preserved

## Dependencies

Add to requirements:
- `anthropic>=0.40.0`      (Anthropic SDK)
- `openai>=1.50.0`         (OpenAI + Azure OpenAI SDK)  
- `cryptography>=42.0.0`   (Fernet encryption)
- `boto3` is already present for AWS but needed for Bedrock

## Migration Notes

- All models use DynamicModelBase which handles tenant schema isolation
- Migrations must be created using Zango's migration tooling (not vanilla Django makemigrations)
- The `config_encrypted` field is BinaryField — ensure the DB column type supports it
- Indexes on AppLLMInvocation are critical for query performance as the table will grow fast
- Consider partitioning AppLLMInvocation by month for large deployments (future concern)
```

---

That's the full implementation prompt for the Provider layer. It covers the registry, base abstraction, 4 provider implementations, DB models, encryption, exceptions, Panel API, and the developer-facing `get_provider()` API. Scoped specifically to Phase 1 — no agents, prompts, tools, or memory yet.

