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

    def _convert_messages(self, messages):
        """Convert LLMMessage list to Anthropic's message format."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def _map_stop_reason(self, stop_reason):
        """Map Anthropic stop_reason to standard stop reasons."""
        mapping = {
            "end_turn": "end_turn",
            "tool_use": "tool_use",
            "max_tokens": "max_tokens",
            "stop_sequence": "stop_sequence",
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
        import json as json_module

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

        # Structured output: append schema to system prompt and prefill assistant
        response_format = kwargs.get("response_format")
        if response_format:
            schema_instruction = ""
            prefill = "{"
            if isinstance(response_format, dict):
                schema_instruction = (
                    "\n\nYou MUST respond with ONLY valid JSON that conforms to this JSON Schema:\n"
                    f"```json\n{json_module.dumps(response_format, indent=2)}\n```\n"
                    "Do not include any text outside the JSON."
                )
                root_type = response_format.get("type", "object")
                prefill = "[" if root_type == "array" else "{"
            elif response_format == "json":
                schema_instruction = (
                    "\n\nYou MUST respond with ONLY valid JSON. "
                    "Do not include any text, markdown formatting, or code fences outside the JSON."
                )

            if schema_instruction:
                kwargs_api["system"] = (kwargs_api.get("system") or "") + schema_instruction
                # Prefill assistant message to force JSON output
                kwargs_api["messages"] = kwargs_api["messages"] + [
                    {"role": "assistant", "content": prefill}
                ]

        start = time.monotonic()
        try:
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

        content = self._extract_text(response)
        # If we used a prefill, prepend it to the response content
        if response_format and content:
            root_type = response_format.get("type", "object") if isinstance(response_format, dict) else "object"
            prefill_char = "[" if root_type == "array" else "{"
            content = prefill_char + content

        return LLMResponse(
            content=content,
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

        try:
            with self._client.messages.stream(**kwargs_api) as stream:
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
        model_info = next(
            (m for m in self.supported_models if m["id"] == model), None
        )
        if not model_info:
            return 0.0
        return compute_anthropic_cost(usage, model_info)
