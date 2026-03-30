"""
Abstract base class for all LLM providers. Each provider must implement these methods.
The base class handles common concerns: cost computation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant", "tool"
    content: Any  # str or list of content blocks (for multimodal)
    tool_call_id: Optional[str] = None  # For OpenAI tool result messages
    tool_calls: Optional[list] = None  # For OpenAI assistant messages with tool calls


@dataclass
class LLMToolDef:
    name: str
    description: str
    input_schema: dict  # JSON Schema


@dataclass
class LLMUsage:
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0


@dataclass
class LLMToolCall:
    id: str
    name: str
    input: dict


@dataclass
class LLMResponse:
    content: str  # Text content of the response
    tool_calls: list[LLMToolCall]  # Tool use requests from the LLM
    stop_reason: str  # "end_turn", "tool_use", "max_tokens"
    usage: LLMUsage
    model: str  # Actual model used (resolved)
    raw_response: Any  # The original SDK response object
    latency_ms: int  # Total request time
    time_to_first_token_ms: Optional[int] = None  # For streaming
    cost_usd: float = 0.0  # Computed cost
    invocation_id: Optional[int] = None  # DB invocation PK (set by ProviderClient)


@dataclass
class LLMStreamChunk:
    delta_text: Optional[str] = None  # Incremental text
    delta_tool_call: Optional[dict] = None  # Incremental tool call
    is_final: bool = False  # Last chunk
    usage: Optional[LLMUsage] = None  # Only on final chunk
    stop_reason: Optional[str] = None  # Only on final chunk


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

    # -- Class-level metadata (set by subclass or @register_provider) --
    slug: str = ""
    display_name: str = ""
    supported_models: list[dict] = []
    config_fields: list[dict] = []

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
        tools: Optional[list[LLMToolDef]] = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        stop_sequences: Optional[list[str]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Synchronous completion. Blocks until the full response is received.
        Must handle provider-specific request formatting and response parsing.
        Must measure and return latency_ms.
        Must raise typed exceptions (see exceptions module).
        """

    @abstractmethod
    def stream(
        self,
        messages: list[LLMMessage],
        model: str,
        tools: Optional[list[LLMToolDef]] = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        stop_sequences: Optional[list[str]] = None,
        **kwargs,
    ) -> Iterator[LLMStreamChunk]:
        """
        Streaming completion. Yields chunks as they arrive.
        The final chunk must have is_final=True with usage and stop_reason.
        """

    @abstractmethod
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate that the provider config is correct and credentials work.
        Makes a minimal API call (e.g., list models or a tiny completion).
        Returns (True, None) on success, (False, "error message") on failure.
        """

    @abstractmethod
    def get_models(self) -> list[dict]:
        """
        Return the list of available models for this provider.
        Can be static (from supported_models) or dynamic (API call).
        """

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.
        Used for pre-flight checks (will this fit in context window?).
        """

    def compute_cost(self, usage: LLMUsage, model: str) -> float:
        """
        Compute cost in USD for a given usage.
        Default implementation uses the model's cost_per_mtok from supported_models.
        Can be overridden for providers with complex pricing.
        """
        model_info = next(
            (m for m in self.supported_models if m["id"] == model), None
        )
        if not model_info:
            return 0.0
        input_cost = (
            usage.input_tokens / 1_000_000
        ) * model_info.get("input_cost_per_mtok", 0)
        output_cost = (
            usage.output_tokens / 1_000_000
        ) * model_info.get("output_cost_per_mtok", 0)
        return round(input_cost + output_cost, 6)

    def format_tools_for_api(self, tools: list[LLMToolDef]) -> list[dict]:
        """
        Convert generic LLMToolDef objects to provider-specific tool format.
        Default implementation returns Anthropic format.
        OpenAI provider overrides this.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in tools
        ]
