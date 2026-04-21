"""
OpenAI provider implementation using the official `openai` Python SDK.
Supports: GPT-4o, GPT-4o-mini, o1, o3 model families.
"""

import time

from zango.ai.exceptions import LLMAPIError, LLMTimeoutError, RateLimitExceeded
from zango.ai.providers.base import (
    BaseLLMProvider,
    LLMResponse,
    LLMStreamChunk,
    LLMToolCall,
    LLMUsage,
)
from zango.ai.providers.registry import register_provider


@register_provider("openai", "OpenAI", icon="openai.svg")
class OpenAIProvider(BaseLLMProvider):
    supported_models = [
        {
            "id": "gpt-4o",
            "name": "GPT-4o",
            "context_window": 128000,
            "max_output_tokens": 16384,
            "input_cost_per_mtok": 2.50,
            "output_cost_per_mtok": 10.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "gpt-4o-mini",
            "name": "GPT-4o Mini",
            "context_window": 128000,
            "max_output_tokens": 16384,
            "input_cost_per_mtok": 0.15,
            "output_cost_per_mtok": 0.60,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
        },
        {
            "id": "o3-mini",
            "name": "o3-mini",
            "context_window": 200000,
            "max_output_tokens": 100000,
            "input_cost_per_mtok": 1.10,
            "output_cost_per_mtok": 4.40,
            "supports_tools": True,
            "supports_vision": False,
            "supports_streaming": True,
        },
    ]

    config_fields = [
        {
            "name": "api_key",
            "type": "secret",
            "required": True,
            "label": "API Key",
        },
        {
            "name": "organization",
            "type": "string",
            "required": False,
            "label": "Organization ID",
        },
        {
            "name": "default_model",
            "type": "select",
            "required": True,
            "label": "Default Model",
            "options_from": "supported_models",
        },
    ]

    def __init__(self, config):
        super().__init__(config)
        import openai

        self._openai = openai
        kwargs = {"api_key": config["api_key"]}
        if config.get("organization"):
            kwargs["organization"] = config["organization"]
        self._client = openai.OpenAI(**kwargs)

    def _convert_messages(self, messages, system=None):
        """Convert LLMMessage list to OpenAI's message format."""
        result = []
        if system:
            result.append({"role": "system", "content": system})
        for msg in messages:
            d = {"role": msg.role, "content": msg.build_content_for_openai()}
            if msg.tool_calls:
                d["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                d["tool_call_id"] = msg.tool_call_id
            result.append(d)
        return result

    def _map_stop_reason(self, finish_reason):
        """Map OpenAI finish_reason to standard stop reasons."""
        mapping = {
            "stop": "end_turn",
            "tool_calls": "tool_use",
            "length": "max_tokens",
            "content_filter": "content_filter",
        }
        return mapping.get(finish_reason, finish_reason)

    def _enforce_additional_properties_false(self, schema):
        """
        Recursively patch a JSON schema for OpenAI strict mode:
        - additionalProperties: false on every object
        - required must list every key in properties
        - nullable fields: replace type: [X, "null"] with type: X + nullable workaround
          (OpenAI strict mode doesn't support type arrays; use anyOf instead)
        """
        if not isinstance(schema, dict):
            return schema
        schema = dict(schema)

        # Normalise nullable type arrays: ["string", "null"] -> anyOf: [{type: string}, {type: null}]
        if isinstance(schema.get("type"), list):
            types = schema.pop("type")
            schema["anyOf"] = [{"type": t} for t in types]

        if schema.get("type") == "object" or "properties" in schema:
            schema["additionalProperties"] = False
            if "properties" in schema:
                schema["properties"] = {
                    k: self._enforce_additional_properties_false(v)
                    for k, v in schema["properties"].items()
                }
                # Every property key must appear in required
                all_keys = list(schema["properties"].keys())
                schema["required"] = all_keys

        if "items" in schema:
            schema["items"] = self._enforce_additional_properties_false(schema["items"])
        if "$defs" in schema:
            schema["$defs"] = {
                k: self._enforce_additional_properties_false(v)
                for k, v in schema["$defs"].items()
            }
        if "anyOf" in schema:
            schema["anyOf"] = [
                self._enforce_additional_properties_false(s) for s in schema["anyOf"]
            ]
        return schema

    def format_tools_for_api(self, tools):
        """Convert LLMToolDef to OpenAI's tool format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]

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
        api_kwargs = {
            "model": model,
            "messages": self._convert_messages(messages, system=system),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            api_kwargs["tools"] = self.format_tools_for_api(tools)
        if stop_sequences:
            api_kwargs["stop"] = stop_sequences

        # Structured output / JSON mode
        response_format = kwargs.get("response_format")
        if isinstance(response_format, dict):
            api_kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "strict": True,
                    "schema": self._enforce_additional_properties_false(
                        response_format
                    ),
                },
            }
        elif response_format == "json":
            api_kwargs["response_format"] = {"type": "json_object"}

        start = time.monotonic()
        try:
            response = self._client.chat.completions.create(**api_kwargs)
        except self._openai.RateLimitError as e:
            raise RateLimitExceeded(str(e)) from e
        except self._openai.APITimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except self._openai.APIError as e:
            raise LLMAPIError(
                str(e), status_code=getattr(e, "status_code", None), original_error=e
            ) from e
        latency_ms = int((time.monotonic() - start) * 1000)

        choice = response.choices[0]
        tool_calls = []
        if choice.message.tool_calls:
            import json

            for tc in choice.message.tool_calls:
                tool_calls.append(
                    LLMToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        input=json.loads(tc.function.arguments),
                    )
                )

        usage = LLMUsage(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            stop_reason=self._map_stop_reason(choice.finish_reason),
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
        api_kwargs = {
            "model": model,
            "messages": self._convert_messages(messages, system=system),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            api_kwargs["tools"] = self.format_tools_for_api(tools)
        if stop_sequences:
            api_kwargs["stop"] = stop_sequences

        try:
            stream = self._client.chat.completions.create(**api_kwargs)
            for chunk in stream:
                if not chunk.choices:
                    # Final chunk with usage only
                    if chunk.usage:
                        yield LLMStreamChunk(
                            is_final=True,
                            usage=LLMUsage(
                                input_tokens=chunk.usage.prompt_tokens,
                                output_tokens=chunk.usage.completion_tokens,
                            ),
                        )
                    continue

                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                if delta.content:
                    yield LLMStreamChunk(delta_text=delta.content)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        yield LLMStreamChunk(
                            delta_tool_call={
                                "index": tc.index,
                                "id": tc.id,
                                "name": getattr(tc.function, "name", None),
                                "arguments": getattr(tc.function, "arguments", None),
                            }
                        )

                if finish_reason:
                    yield LLMStreamChunk(
                        is_final=True,
                        stop_reason=self._map_stop_reason(finish_reason),
                    )
        except self._openai.RateLimitError as e:
            raise RateLimitExceeded(str(e)) from e
        except self._openai.APITimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except self._openai.APIError as e:
            raise LLMAPIError(
                str(e), status_code=getattr(e, "status_code", None), original_error=e
            ) from e

    def validate_config(self):
        try:
            self._client.chat.completions.create(
                model=self.config.get("default_model", "gpt-4o-mini"),
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
