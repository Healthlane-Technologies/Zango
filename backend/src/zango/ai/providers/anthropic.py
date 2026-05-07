"""
Anthropic provider implementation using the official `anthropic` Python SDK.
Supports: Claude Opus, Sonnet, Haiku model families.
Handles: prompt caching, tool use, streaming, extended thinking.
"""

import time

from zango.ai.cost import compute_anthropic_cost
from zango.ai.exceptions import LLMAPIError, LLMTimeoutError, RateLimitExceeded
from zango.ai.providers.base import (
    BaseLLMProvider,
    LLMResponse,
    LLMStreamChunk,
    LLMToolCall,
    LLMUsage,
)
from zango.ai.providers.registry import register_provider


@register_provider("anthropic", "Anthropic", icon="anthropic.svg")
class AnthropicProvider(BaseLLMProvider):
    # Pricing sourced from https://docs.anthropic.com/en/docs/about-claude/models (May 2026)
    # Only active and deprecated (not yet retired) models are listed.
    supported_models = [
        # ── Active models ──────────────────────────────────────────────────
        {
            "id": "claude-opus-4-7",
            "name": "Claude Opus 4.7",
            "context_window": 1000000,
            "max_output_tokens": 128000,
            "input_cost_per_mtok": 5.00,
            "output_cost_per_mtok": 25.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "claude-sonnet-4-6",
            "name": "Claude Sonnet 4.6",
            "context_window": 1000000,
            "max_output_tokens": 64000,
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
            "max_output_tokens": 64000,
            "input_cost_per_mtok": 1.00,
            "output_cost_per_mtok": 5.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "claude-opus-4-6",
            "name": "Claude Opus 4.6",
            "context_window": 1000000,
            "max_output_tokens": 128000,
            "input_cost_per_mtok": 5.00,
            "output_cost_per_mtok": 25.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "claude-sonnet-4-5-20250929",
            "name": "Claude Sonnet 4.5",
            "context_window": 200000,
            "max_output_tokens": 64000,
            "input_cost_per_mtok": 3.00,
            "output_cost_per_mtok": 15.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "claude-opus-4-5-20251101",
            "name": "Claude Opus 4.5",
            "context_window": 200000,
            "max_output_tokens": 64000,
            "input_cost_per_mtok": 5.00,
            "output_cost_per_mtok": 25.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "claude-opus-4-1-20250805",
            "name": "Claude Opus 4.1",
            "context_window": 200000,
            "max_output_tokens": 32000,
            "input_cost_per_mtok": 15.00,
            "output_cost_per_mtok": 75.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        # ── Deprecated models (retiring June 15 2026) ─────────────────────
        {
            "id": "claude-sonnet-4-20250514",
            "name": "Claude Sonnet 4 (deprecated)",
            "context_window": 200000,
            "max_output_tokens": 64000,
            "input_cost_per_mtok": 3.00,
            "output_cost_per_mtok": 15.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "claude-opus-4-20250514",
            "name": "Claude Opus 4 (deprecated)",
            "context_window": 200000,
            "max_output_tokens": 32000,
            "input_cost_per_mtok": 15.00,
            "output_cost_per_mtok": 75.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
    ]

    config_fields = [
        {
            "name": "api_key",
            "type": "secret",
            "required": True,
            "label": "API Key",
            "help_text": "Your Anthropic API key (starts with sk-ant-)",
        },
        {
            "name": "default_model",
            "type": "select",
            "required": True,
            "label": "Default Model",
            "options_from": "supported_models",
        },
        {
            "name": "max_retries",
            "type": "integer",
            "required": False,
            "label": "Max Retries",
            "default": 2,
        },
        {
            "name": "timeout_seconds",
            "type": "integer",
            "required": False,
            "label": "Timeout (seconds)",
            "default": 120,
        },
    ]

    def __init__(self, config):
        super().__init__(config)
        import anthropic

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(
            api_key=config["api_key"],
            max_retries=config.get("max_retries", 2),
            timeout=config.get("timeout_seconds", 120),
        )

    def prepare_files(self, files):
        """
        Upload each file to the Anthropic Files API (beta) once and return
        lightweight LLMFile objects carrying only the file_id.
        Falls back to raw bytes if upload fails.
        """
        import io

        from zango.ai.providers.base import LLMFile

        prepared = []
        for f in files:
            if f.url:
                prepared.append(f)
                continue
            try:
                import os

                filename = os.path.basename(f.filename or "upload") or "upload"
                file_obj = io.BytesIO(f.data)
                uploaded = self._client.beta.files.upload(
                    file=(
                        filename,
                        file_obj,
                        f.media_type or "application/octet-stream",
                    ),
                    extra_headers={"anthropic-beta": "files-api-2025-04-14"},
                )
                prepared.append(
                    LLMFile(
                        url=f"file-id://{uploaded.id}",
                        media_type=f.media_type,
                        filename=f.filename,
                    )
                )
            except Exception as exc:
                # Files API not available or failed — fall back to raw bytes
                import logging

                logging.getLogger(__name__).warning(
                    "Anthropic Files API upload failed (%s: %s) — falling back to base64",
                    type(exc).__name__,
                    exc,
                )
                prepared.append(f)
        return prepared

    def _convert_messages(self, messages):
        """Convert LLMMessage list to Anthropic's message format."""
        return [
            {"role": msg.role, "content": msg.build_content_for_anthropic()}
            for msg in messages
        ]

    def _needs_files_beta(self, converted_messages):
        """Return True if any message content block references an uploaded file_id."""
        for msg in converted_messages:
            content = msg.get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict):
                    src = block.get("source", {})
                    if isinstance(src, dict) and src.get("type") == "file":
                        return True
        return False

    def _map_stop_reason(self, stop_reason):
        """Map Anthropic stop_reason to standard stop reasons."""
        mapping = {
            "end_turn": "end_turn",
            "tool_use": "tool_use",
            "max_tokens": "max_tokens",
            "stop_sequence": "stop_sequence",
            "refusal": "refusal",
        }
        return mapping.get(stop_reason, stop_reason)

    def _extract_tool_calls(self, response):
        """Extract tool calls from Anthropic response content blocks."""
        tool_calls = []
        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append(
                    LLMToolCall(id=block.id, name=block.name, input=block.input)
                )
        return tool_calls

    def _extract_text(self, response):
        """Extract text content from Anthropic response content blocks."""
        texts = []
        for block in response.content:
            if block.type == "text":
                texts.append(block.text)
        return "\n".join(texts)

    def complete(
        self,
        messages,
        model,
        tools=None,
        temperature=1.0,
        max_tokens=4096,
        system=None,
        stop_sequences=None,
        **kwargs,
    ):
        kwargs_api = {
            "model": model,
            "messages": self._convert_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            kwargs_api["system"] = system
        if tools:
            kwargs_api["tools"] = self.format_tools_for_api(tools)
        if stop_sequences:
            kwargs_api["stop_sequences"] = stop_sequences

        # Structured output
        response_format = kwargs.get("response_format")
        if isinstance(response_format, dict):
            # Native JSON schema enforcement via output_config — incompatible with prefill
            kwargs_api["output_config"] = {
                "format": {
                    "type": "json_schema",
                    "schema": response_format,
                }
            }
        elif response_format == "json":
            # No schema supplied — fall back to prompt engineering
            kwargs_api["system"] = (kwargs_api.get("system") or "") + (
                "\n\nYou MUST respond with ONLY valid JSON. "
                "Do not include any text, markdown formatting, or code fences outside the JSON."
            )

        uses_files_beta = self._needs_files_beta(kwargs_api["messages"])

        start = time.monotonic()
        try:
            if uses_files_beta:
                response = self._client.beta.messages.create(
                    **kwargs_api, betas=["files-api-2025-04-14"]
                )
            else:
                response = self._client.messages.create(**kwargs_api)
        except self._anthropic.RateLimitError as e:
            raise RateLimitExceeded(str(e)) from e
        except self._anthropic.APITimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except self._anthropic.APIError as e:
            raise LLMAPIError(
                str(e), status_code=getattr(e, "status_code", None), original_error=e
            ) from e
        latency_ms = int((time.monotonic() - start) * 1000)

        usage = LLMUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_creation_tokens=getattr(
                response.usage, "cache_creation_input_tokens", 0
            )
            or 0,
            cache_read_tokens=getattr(response.usage, "cache_read_input_tokens", 0)
            or 0,
        )

        return LLMResponse(
            content=self._extract_text(response),
            tool_calls=self._extract_tool_calls(response),
            stop_reason=self._map_stop_reason(response.stop_reason),
            usage=usage,
            model=response.model,
            raw_response=response,
            latency_ms=latency_ms,
        )

    def stream(
        self,
        messages,
        model,
        tools=None,
        temperature=1.0,
        max_tokens=4096,
        system=None,
        stop_sequences=None,
        **kwargs,
    ):
        kwargs_api = {
            "model": model,
            "messages": self._convert_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            kwargs_api["system"] = system
        if tools:
            kwargs_api["tools"] = self.format_tools_for_api(tools)
        if stop_sequences:
            kwargs_api["stop_sequences"] = stop_sequences

        # Structured output — output_config is compatible with streaming
        response_format = kwargs.get("response_format")
        if isinstance(response_format, dict):
            kwargs_api["output_config"] = {
                "format": {
                    "type": "json_schema",
                    "schema": response_format,
                }
            }
        elif response_format == "json":
            kwargs_api["system"] = (kwargs_api.get("system") or "") + (
                "\n\nYou MUST respond with ONLY valid JSON. "
                "Do not include any text, markdown formatting, or code fences outside the JSON."
            )

        uses_files_beta = self._needs_files_beta(kwargs_api["messages"])

        try:
            _stream_ctx = (
                self._client.beta.messages.stream(
                    **kwargs_api, betas=["files-api-2025-04-14"]
                )
                if uses_files_beta
                else self._client.messages.stream(**kwargs_api)
            )
            with _stream_ctx as stream:
                for event in stream:
                    if hasattr(event, "type"):
                        if event.type == "content_block_delta":
                            delta = event.delta
                            if hasattr(delta, "text"):
                                yield LLMStreamChunk(delta_text=delta.text)
                            elif hasattr(delta, "partial_json"):
                                yield LLMStreamChunk(
                                    delta_tool_call={"partial_json": delta.partial_json}
                                )

                final_message = stream.get_final_message()
                usage = LLMUsage(
                    input_tokens=final_message.usage.input_tokens,
                    output_tokens=final_message.usage.output_tokens,
                    cache_creation_tokens=getattr(
                        final_message.usage, "cache_creation_input_tokens", 0
                    )
                    or 0,
                    cache_read_tokens=getattr(
                        final_message.usage, "cache_read_input_tokens", 0
                    )
                    or 0,
                )
                yield LLMStreamChunk(
                    is_final=True,
                    usage=usage,
                    stop_reason=self._map_stop_reason(final_message.stop_reason),
                )
        except self._anthropic.RateLimitError as e:
            raise RateLimitExceeded(str(e)) from e
        except self._anthropic.APITimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except self._anthropic.APIError as e:
            raise LLMAPIError(
                str(e), status_code=getattr(e, "status_code", None), original_error=e
            ) from e

    @classmethod
    def fetch_models(cls, config: dict) -> list[dict]:
        """
        Fetch available models live from GET /v1/models using the supplied API key.
        Falls back to the hardcoded supported_models list if the call fails unexpectedly.
        Raises a descriptive exception on auth / credential errors.
        """
        import anthropic

        client = anthropic.Anthropic(api_key=config["api_key"], max_retries=0)
        try:
            page = client.models.list(limit=100)
        except anthropic.AuthenticationError as e:
            raise ValueError(
                "Invalid API key. Please check your Anthropic API key and try again."
            ) from e
        except anthropic.PermissionDeniedError as e:
            raise ValueError(
                "Access denied. Your API key does not have permission to list models."
            ) from e
        except anthropic.APIConnectionError as e:
            raise ValueError(
                "Could not reach the Anthropic API. Check your network connection."
            ) from e
        except anthropic.APIError as e:
            raise ValueError(f"Anthropic API error: {e}") from e

        models = []
        for m in page.data:
            caps = getattr(m, "capabilities", None)
            supports_vision = (
                getattr(getattr(caps, "image_input", None), "supported", False)
                if caps
                else False
            )
            supports_tools = True  # All current Claude models support tools
            models.append(
                {
                    "id": m.id,
                    "name": m.display_name,
                    "context_window": getattr(m, "max_input_tokens", 200000),
                    "max_output_tokens": getattr(m, "max_tokens", 8192),
                    "input_cost_per_mtok": None,  # Not exposed by the API
                    "output_cost_per_mtok": None,
                    "supports_tools": supports_tools,
                    "supports_vision": supports_vision,
                    "supports_streaming": True,
                }
            )
        return models

    def validate_config(self):
        try:
            self._client.messages.create(
                model=self.config.get("default_model", "claude-haiku-4-5-20251001"),
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return (True, None)
        except Exception as e:
            return (False, str(e))

    def get_models(self):
        return self.supported_models

    def estimate_tokens(self, text):
        """Approximate at ~4 chars per token."""
        return max(1, len(text) // 4)

    def compute_cost(self, usage, model):
        """Override to handle prompt caching pricing."""
        model_info = next((m for m in self.supported_models if m["id"] == model), None)
        if not model_info:
            return 0.0
        return compute_anthropic_cost(usage, model_info)
