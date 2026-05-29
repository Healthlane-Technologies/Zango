"""
Azure OpenAI provider. Uses the openai SDK with azure-specific config.
Key difference: requires azure_endpoint and api_version in addition to api_key.
Model IDs are deployment names, not standard model names.
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


@register_provider("azure_openai", "Azure OpenAI", icon="azure.svg")
class AzureOpenAIProvider(BaseLLMProvider):
    supported_models = []  # Azure models depend on deployment, configured per-app

    config_fields = [
        {
            "name": "api_key",
            "type": "secret",
            "required": True,
            "label": "API Key",
        },
        {
            "name": "azure_endpoint",
            "type": "url",
            "required": True,
            "label": "Azure Endpoint",
            "help_text": "https://your-resource.openai.azure.com/",
        },
        {
            "name": "api_version",
            "type": "string",
            "required": True,
            "label": "API Version",
            "default": "2024-10-21",
        },
        {
            "name": "default_deployment",
            "type": "string",
            "required": True,
            "label": "Default Deployment Name",
        },
    ]

    def __init__(self, config):
        super().__init__(config)
        import openai

        self._openai = openai
        self._client = openai.AzureOpenAI(
            api_key=config["api_key"],
            azure_endpoint=config["azure_endpoint"],
            api_version=config.get("api_version", "2024-10-21"),
        )

    def _convert_messages(self, messages, system=None):
        """Convert LLMMessage list to OpenAI's message format."""
        result = []
        if system:
            result.append({"role": "system", "content": system})
        for msg in messages:
            d = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                d["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                d["tool_call_id"] = msg.tool_call_id
            result.append(d)
        return result

    def _map_stop_reason(self, finish_reason):
        mapping = {
            "stop": "end_turn",
            "tool_calls": "tool_use",
            "length": "max_tokens",
            "content_filter": "content_filter",
        }
        return mapping.get(finish_reason, finish_reason)

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
        # For Azure, model param is the deployment name
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
                    "schema": response_format,
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

    @classmethod
    def fetch_models(cls, config: dict) -> list[dict]:
        """
        Azure OpenAI doesn't have a standard "list chat models" endpoint —
        models are tied to deployments configured in the Azure portal.
        We call GET /openai/deployments to list what's deployed under this resource.
        Falls back to an empty list with a clear error on auth failure.
        """
        import openai

        try:
            client = openai.AzureOpenAI(
                api_key=config["api_key"],
                azure_endpoint=config["azure_endpoint"],
                api_version=config.get("api_version", "2024-10-21"),
                max_retries=0,
            )
            raw = client.models.list()
        except openai.AuthenticationError as e:
            raise ValueError(
                "Invalid credentials. Check your Azure API key and endpoint."
            ) from e
        except openai.APIConnectionError as e:
            raise ValueError(
                "Could not reach your Azure OpenAI endpoint. Verify the endpoint URL."
            ) from e
        except openai.APIError as e:
            raise ValueError(f"Azure OpenAI API error: {e}") from e

        models = []
        for m in raw.data:
            models.append(
                {
                    "id": m.id,
                    "name": m.id,  # Azure deployment names are the model ID
                    "context_window": 128000,
                    "max_output_tokens": 16384,
                    "input_cost_per_mtok": None,
                    "output_cost_per_mtok": None,
                    "supports_tools": True,
                    "supports_vision": False,
                    "supports_streaming": True,
                }
            )
        return models

    def validate_config(self):
        try:
            deployment = self.config.get("default_deployment", "")
            self._client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return (True, None)
        except Exception as e:
            return (False, str(e))

    def get_models(self):
        # Azure models are deployment-specific, return whatever is configured
        return self.supported_models
