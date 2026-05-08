"""
Abstract base class for all LLM providers. Each provider must implement these methods.
The base class handles common concerns: cost computation.
"""

import base64
import mimetypes

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterator, Optional


@dataclass
class LLMFile:
    """
    A file attachment for a multimodal agent query.

    Always use a named constructor — do not instantiate directly::

        from zango.ai import get_agent, LLMFile

        agent = get_agent("prescription-processor")

        # Model file field (most common in app code)
        response = agent.run(
            files=[LLMFile.from_django_file(prescription.prescription_file)]
        )

        # Request upload
        response = agent.run(
            files=[LLMFile.from_django_file(request.FILES["report"])]
        )

        # Raw bytes
        response = agent.run(
            files=[LLMFile.from_bytes(pdf_bytes, media_type="application/pdf")]
        )

        # Public URL
        response = agent.run(
            files=[LLMFile.from_url("https://example.com/scan.jpg")]
        )

        # Local file path
        response = agent.run(
            files=[LLMFile.from_path("/tmp/prescription.pdf")]
        )
    """

    data: Optional[bytes] = None
    media_type: Optional[str] = None  # e.g. "image/png", "application/pdf"
    url: Optional[str] = None  # public URL (alternative to data)
    filename: Optional[str] = None  # optional display / log name

    # ------------------------------------------------------------------ #
    # Convenience constructors                                             #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_django_file(cls, django_file) -> "LLMFile":
        """
        Accept a Django file field value (``ZFileField``, ``FileField``,
        ``InMemoryUploadedFile``, ``TemporaryUploadedFile``).

        Works with model file fields::

            LLMFile.from_django_file(prescription.prescription_file)

        And with request upload files::

            LLMFile.from_django_file(request.FILES["report"])
        """
        django_file.seek(0)
        data = django_file.read()
        # FieldFile (model field) has no content_type; guess from name
        media_type = getattr(django_file, "content_type", None)
        if not media_type:
            name = getattr(django_file, "name", "") or ""
            media_type, _ = mimetypes.guess_type(name)
        return cls(
            data=data,
            media_type=media_type or "application/octet-stream",
            filename=getattr(django_file, "name", None),
        )

    @classmethod
    def from_bytes(
        cls, data: bytes, media_type: str, filename: str = None
    ) -> "LLMFile":
        """
        Create from raw bytes with an explicit media type::

            LLMFile.from_bytes(pdf_bytes, media_type="application/pdf")
        """
        return cls(data=data, media_type=media_type, filename=filename)

    @classmethod
    def from_url(cls, url: str, media_type: str = None) -> "LLMFile":
        """
        Create from a publicly accessible URL::

            LLMFile.from_url("https://example.com/scan.jpg")
        """
        if not media_type:
            media_type, _ = mimetypes.guess_type(url)
        return cls(url=url, media_type=media_type or "application/octet-stream")

    @classmethod
    def from_path(cls, path: str) -> "LLMFile":
        """
        Read a local file path::

            LLMFile.from_path("/tmp/prescription.pdf")
        """
        media_type, _ = mimetypes.guess_type(path)
        with open(path, "rb") as f:
            data = f.read()
        return cls(
            data=data,
            media_type=media_type or "application/octet-stream",
            filename=path,
        )

    # ------------------------------------------------------------------ #
    # Provider-specific serialisers                                        #
    # ------------------------------------------------------------------ #

    def _b64(self) -> str:
        return base64.standard_b64encode(self.data).decode("utf-8")

    def to_anthropic_block(self) -> dict:
        """Anthropic content block (image or document)."""
        media_type = self.media_type or "application/octet-stream"
        is_image = media_type.startswith("image/")

        if self.url:
            # file-id:// scheme means uploaded via Anthropic Files API
            if self.url.startswith("file-id://"):
                file_id = self.url[len("file-id://") :]
                block_type = "image" if is_image else "document"
                return {
                    "type": block_type,
                    "source": {"type": "file", "file_id": file_id},
                }
            block_type = "image" if is_image else "document"
            return {"type": block_type, "source": {"type": "url", "url": self.url}}

        encoded = self._b64()
        if is_image:
            return {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": encoded},
            }
        return {
            "type": "document",
            "source": {"type": "base64", "media_type": media_type, "data": encoded},
        }

    def to_openai_block(self) -> dict:
        """OpenAI content block (image_url)."""
        media_type = self.media_type or "application/octet-stream"
        if self.url:
            return {"type": "image_url", "image_url": {"url": self.url}}
        data_url = f"data:{media_type};base64,{self._b64()}"
        return {"type": "image_url", "image_url": {"url": data_url}}


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant", "tool"
    content: Any  # str or list of content blocks (for multimodal)
    tool_call_id: Optional[str] = None  # For OpenAI tool result messages
    tool_calls: Optional[list] = None  # For OpenAI assistant messages with tool calls
    files: Optional[list[LLMFile]] = None  # File / image attachments

    def build_content_for_anthropic(self) -> Any:
        """Return content ready for the Anthropic API (with file blocks prepended)."""
        if not self.files:
            return self.content
        blocks = [f.to_anthropic_block() for f in self.files]
        if isinstance(self.content, str) and self.content:
            blocks.append({"type": "text", "text": self.content})
        elif isinstance(self.content, list):
            blocks.extend(self.content)
        return blocks

    def build_content_for_openai(self) -> Any:
        """Return content ready for the OpenAI API (with file blocks prepended)."""
        if not self.files:
            return self.content
        blocks = [f.to_openai_block() for f in self.files]
        if isinstance(self.content, str) and self.content:
            blocks.append({"type": "text", "text": self.content})
        elif isinstance(self.content, list):
            blocks.extend(self.content)
        return blocks


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
    stop_reason: str  # "end_turn", "tool_use", "max_tokens", "refusal"
    usage: LLMUsage
    model: str  # Actual model used (resolved)
    raw_response: Any  # The original SDK response object
    latency_ms: int  # Total request time
    time_to_first_token_ms: Optional[int] = None  # For streaming
    cost_usd: float = 0.0  # Computed cost
    invocation_id: Optional[int] = None  # DB invocation PK (set by ProviderClient)
    session_id: Optional[str] = (
        None  # Memory session ID (set by AgentClient when memory_enabled)
    )
    parsed_content: Optional[Any] = (
        None  # Parsed + validated JSON dict (set when output_schema=JSON)
    )


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

    @classmethod
    def fetch_models(cls, config: dict) -> list[dict]:
        """
        Fetch available models from the provider API using the supplied config.
        Called before the provider is saved — credentials may not yet be stored in DB.

        Returns a list of model dicts in the same shape as supported_models:
            {"id": str, "name": str, "context_window": int, "max_output_tokens": int,
             "supports_tools": bool, "supports_vision": bool, "supports_streaming": bool}

        Default: instantiates the provider with config and calls get_models().
        Override in subclasses that support a live /models API endpoint.

        Raises an exception (with a human-readable message) on auth failure.
        """
        instance = cls(config)
        return instance.get_models()

    def compute_cost(self, usage: LLMUsage, model: str) -> float:
        """
        Compute cost in USD for a given usage.
        Default implementation uses the model's cost_per_mtok from supported_models.
        Can be overridden for providers with complex pricing.
        """
        model_info = next((m for m in self.supported_models if m["id"] == model), None)
        if not model_info:
            return 0.0
        input_cost = (usage.input_tokens / 1_000_000) * model_info.get(
            "input_cost_per_mtok", 0
        )
        output_cost = (usage.output_tokens / 1_000_000) * model_info.get(
            "output_cost_per_mtok", 0
        )
        return round(input_cost + output_cost, 6)

    def prepare_files(self, files: list["LLMFile"]) -> list["LLMFile"]:
        """
        Pre-process files before the agentic loop starts.

        Default behaviour (Anthropic and any provider without a file upload API):
        return files unchanged — they will be sent as base64 in round 1 only,
        then stripped from subsequent rounds by AgentClient.

        Providers that support a file upload API (e.g. OpenAI) should override
        this to upload each file once and return lightweight LLMFile objects
        that carry only a reference (url="file-id://...") instead of raw bytes.
        This avoids re-sending large files on every tool round.
        """
        return files

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
