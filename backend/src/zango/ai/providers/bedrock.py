"""
AWS Bedrock provider implementation using the Bedrock Converse API
(``bedrock-runtime.converse`` / ``converse_stream``). Supports models from
Anthropic, Amazon Nova, Meta Llama, and Mistral families through a single
unified message + tool-use format.

Auth: static AWS access keys (no STS / SSO).

Model IDs are stored *bare* (region-agnostic) in ``supported_models``. The
cross-region inference profile prefix (``us.`` / ``eu.`` / ``apac.``) is derived
from the configured ``aws_region`` at call time by ``_resolve_model_id()``.
"""

import time

from zango.ai.exceptions import LLMAPIError, LLMTimeoutError, RateLimitExceeded
from zango.ai.providers.base import (
    BaseLLMProvider,
    LLMFile,
    LLMResponse,
    LLMStreamChunk,
    LLMToolCall,
    LLMUsage,
)
from zango.ai.providers.registry import register_provider


# Region prefix → geography mapping for cross-region inference profiles.
# Source: https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html
_REGION_GEOGRAPHY_PREFIX = {
    "us": "us.",
    "eu": "eu.",
    "ap": "apac.",
}


def _geography_prefix_for_region(region: str):
    """Map an AWS region to a Bedrock cross-region inference profile prefix.

    Returns ``None`` for regions with no geography (``ca-central-1``,
    ``sa-east-1``) — those have no cross-region profile and must not be used
    with models that require one.
    """
    if not region:
        return None
    head = region.split("-", 1)[0]
    return _REGION_GEOGRAPHY_PREFIX.get(head)


@register_provider("bedrock", "AWS Bedrock", icon="aws.svg")
class BedrockProvider(BaseLLMProvider):
    # Pricing sourced from https://aws.amazon.com/bedrock/pricing/ (review on each release).
    # IDs are bare (region-agnostic). The geography prefix is added at call time
    # by ``_resolve_model_id()`` for entries with requires_inference_profile=True.
    supported_models = [
        # ── Anthropic Claude 4.x on Bedrock (all require a cross-region profile) ──
        # IDs verified against https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html
        {
            "id": "anthropic.claude-sonnet-4-5-20250929-v1:0",
            "name": "Claude Sonnet 4.5 (Bedrock)",
            "context_window": 200000,
            "max_output_tokens": 64000,
            "input_cost_per_mtok": 3.00,
            "output_cost_per_mtok": 15.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
            "requires_inference_profile": True,
        },
        {
            "id": "anthropic.claude-sonnet-4-20250514-v1:0",
            "name": "Claude Sonnet 4 (Bedrock)",
            "context_window": 200000,
            "max_output_tokens": 64000,
            "input_cost_per_mtok": 3.00,
            "output_cost_per_mtok": 15.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
            "requires_inference_profile": True,
        },
        {
            "id": "anthropic.claude-opus-4-1-20250805-v1:0",
            "name": "Claude Opus 4.1 (Bedrock)",
            "context_window": 200000,
            "max_output_tokens": 32000,
            "input_cost_per_mtok": 15.00,
            "output_cost_per_mtok": 75.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
            "requires_inference_profile": True,
        },
        {
            "id": "anthropic.claude-opus-4-20250514-v1:0",
            "name": "Claude Opus 4 (Bedrock)",
            "context_window": 200000,
            "max_output_tokens": 32000,
            "input_cost_per_mtok": 15.00,
            "output_cost_per_mtok": 75.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
            "requires_inference_profile": True,
        },
        # ── Anthropic Claude 3.5 on Bedrock ──────────────────────────────
        {
            "id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "name": "Claude 3.5 Sonnet v2 (Bedrock)",
            "context_window": 200000,
            "max_output_tokens": 8192,
            "input_cost_per_mtok": 3.00,
            "output_cost_per_mtok": 15.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
            "requires_inference_profile": True,
        },
        {
            "id": "anthropic.claude-3-5-haiku-20241022-v1:0",
            "name": "Claude 3.5 Haiku (Bedrock)",
            "context_window": 200000,
            "max_output_tokens": 8192,
            "input_cost_per_mtok": 1.00,
            "output_cost_per_mtok": 5.00,
            "supports_tools": True,
            "supports_vision": False,
            "supports_streaming": True,
            "requires_inference_profile": True,
        },
        {
            "id": "anthropic.claude-3-opus-20240229-v1:0",
            "name": "Claude 3 Opus (Bedrock)",
            "context_window": 200000,
            "max_output_tokens": 4096,
            "input_cost_per_mtok": 15.00,
            "output_cost_per_mtok": 75.00,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
            "requires_inference_profile": False,
        },
        # ── Amazon Nova ───────────────────────────────────────────────────
        {
            "id": "amazon.nova-pro-v1:0",
            "name": "Amazon Nova Pro",
            "context_window": 300000,
            "max_output_tokens": 5120,
            "input_cost_per_mtok": 0.80,
            "output_cost_per_mtok": 3.20,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
            "requires_inference_profile": False,
        },
        {
            "id": "amazon.nova-lite-v1:0",
            "name": "Amazon Nova Lite",
            "context_window": 300000,
            "max_output_tokens": 5120,
            "input_cost_per_mtok": 0.06,
            "output_cost_per_mtok": 0.24,
            "supports_tools": True,
            "supports_vision": True,
            "supports_streaming": True,
            "requires_inference_profile": False,
        },
        {
            "id": "amazon.nova-micro-v1:0",
            "name": "Amazon Nova Micro",
            "context_window": 128000,
            "max_output_tokens": 5120,
            "input_cost_per_mtok": 0.035,
            "output_cost_per_mtok": 0.14,
            "supports_tools": True,
            "supports_vision": False,
            "supports_streaming": True,
            "requires_inference_profile": False,
        },
        # ── Meta Llama ────────────────────────────────────────────────────
        {
            "id": "meta.llama3-1-70b-instruct-v1:0",
            "name": "Llama 3.1 70B Instruct",
            "context_window": 128000,
            "max_output_tokens": 2048,
            "input_cost_per_mtok": 0.72,
            "output_cost_per_mtok": 0.72,
            "supports_tools": True,
            "supports_vision": False,
            "supports_streaming": True,
            "requires_inference_profile": False,
        },
        # ── Mistral ───────────────────────────────────────────────────────
        {
            "id": "mistral.mistral-large-2407-v1:0",
            "name": "Mistral Large 2 (24.07)",
            "context_window": 128000,
            "max_output_tokens": 8192,
            "input_cost_per_mtok": 2.00,
            "output_cost_per_mtok": 6.00,
            "supports_tools": True,
            "supports_vision": False,
            "supports_streaming": True,
            "requires_inference_profile": False,
        },
    ]

    config_fields = [
        {
            "name": "aws_access_key_id",
            "type": "secret",
            "required": True,
            "label": "AWS Access Key ID",
        },
        {
            "name": "aws_secret_access_key",
            "type": "secret",
            "required": True,
            "label": "AWS Secret Access Key",
        },
        {
            "name": "aws_region",
            "type": "select",
            "required": True,
            "label": "AWS Region",
            "default": "us-east-1",
            "help_text": "Bedrock-enabled AWS region. The cross-region inference profile prefix is derived from this.",
            "options": [
                {"value": "us-east-1", "label": "us-east-1 (N. Virginia)"},
                {"value": "us-east-2", "label": "us-east-2 (Ohio)"},
                {"value": "us-west-2", "label": "us-west-2 (Oregon)"},
                {"value": "eu-west-1", "label": "eu-west-1 (Ireland)"},
                {"value": "eu-west-3", "label": "eu-west-3 (Paris)"},
                {"value": "eu-central-1", "label": "eu-central-1 (Frankfurt)"},
                {"value": "ap-northeast-1", "label": "ap-northeast-1 (Tokyo)"},
                {"value": "ap-south-1", "label": "ap-south-1 (Mumbai)"},
                {"value": "ap-southeast-1", "label": "ap-southeast-1 (Singapore)"},
                {"value": "ap-southeast-2", "label": "ap-southeast-2 (Sydney)"},
                {"value": "ca-central-1", "label": "ca-central-1 (Canada)"},
                {"value": "sa-east-1", "label": "sa-east-1 (São Paulo)"},
            ],
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
        try:
            import boto3

            from botocore.config import Config
            from botocore.exceptions import ClientError, ReadTimeoutError
        except ImportError as e:
            raise ValueError(
                "boto3 is not installed. Run: pip install zango[bedrock]"
            ) from e

        self._ClientError = ClientError
        self._ReadTimeoutError = ReadTimeoutError

        access_key = config.get("aws_access_key_id")
        secret_key = config.get("aws_secret_access_key")
        missing = [
            name
            for name, val in (
                ("aws_access_key_id", access_key),
                ("aws_secret_access_key", secret_key),
            )
            if not val
        ]
        if missing:
            raise ValueError(
                f"Bedrock provider is missing required credential(s): {', '.join(missing)}. "
                "Re-enter your AWS credentials in the provider settings."
            )

        common_kwargs = dict(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=config.get("aws_region", "us-east-1"),
        )
        bcfg = Config(
            read_timeout=int(config.get("timeout_seconds", 120)),
            retries={"max_attempts": int(config.get("max_retries", 2))},
        )
        self._client = boto3.client("bedrock-runtime", config=bcfg, **common_kwargs)
        self._schema_client = self._client

    # ------------------------------------------------------------------ #
    # Model-ID resolution                                                #
    # ------------------------------------------------------------------ #

    def _resolve_model_id(self, model: str) -> str:
        """Prepend the geography prefix when the model requires a cross-region profile.

        - Look the bare ID up in supported_models.
        - If ``requires_inference_profile`` is True, prepend ``us.`` / ``eu.`` /
          ``apac.`` derived from ``aws_region``.
        - Pass-through for IDs not in the catalog (user override) or models
          that don't require a profile.
        """
        # Already a resolved profile ID — pass through unchanged.
        if model.startswith(("us.", "eu.", "apac.", "global.")):
            return model

        info = next((m for m in self.supported_models if m["id"] == model), None)
        if not info or not info.get("requires_inference_profile"):
            return model

        region = self.config.get("aws_region", "us-east-1")
        prefix = _geography_prefix_for_region(region)
        if prefix is None:
            raise LLMAPIError(
                f"{model} requires a US, EU, or APAC region; "
                f"{region} is not in a supported geography."
            )
        return f"{prefix}{model}"

    # ------------------------------------------------------------------ #
    # Message / tool conversion                                          #
    # ------------------------------------------------------------------ #

    def _file_to_block(self, f: LLMFile) -> dict:
        """Convert an LLMFile to a Converse content block."""
        media_type = (f.media_type or "").lower()
        if not media_type.startswith("image/"):
            # Converse currently supports image inputs only for most models.
            # Documents go through the ``document`` block; we map basic ones.
            fmt = media_type.split("/")[-1] if "/" in media_type else "pdf"
            return {
                "document": {
                    "format": fmt or "pdf",
                    "name": (f.filename or "document").rsplit(".", 1)[0][:50]
                    or "document",
                    "source": {"bytes": f.data or b""},
                }
            }
        # image/png|jpeg|gif|webp
        fmt = media_type.split("/", 1)[1]
        if fmt == "jpg":
            fmt = "jpeg"
        return {
            "image": {
                "format": fmt,
                "source": {"bytes": f.data or b""},
            }
        }

    def _convert_messages_for_bedrock(self, messages):
        """Convert a list of ``LLMMessage`` to Bedrock Converse messages.

        Returns a tuple ``(system_blocks, converse_messages)`` where:
        - ``system_blocks`` is either ``None`` or a list like ``[{"text": "..."}]``
          (surfaced via the top-level ``system`` kwarg).
        - ``converse_messages`` is the list of ``{"role", "content"}`` dicts.
        """
        system_blocks = None
        out = []
        for msg in messages:
            if msg.role == "system":
                text = msg.content if isinstance(msg.content, str) else ""
                if text:
                    system_blocks = (system_blocks or []) + [{"text": text}]
                continue

            content_blocks = []

            # File attachments first (consistent with how OpenAI/Anthropic
            # converters prepend file blocks).
            if msg.files:
                for f in msg.files:
                    content_blocks.append(self._file_to_block(f))

            # Tool-result message (role="tool"): convert into a user-role
            # message carrying a toolResult block.
            if msg.role == "tool":
                content = msg.content
                if not isinstance(content, str):
                    import json

                    try:
                        content = json.dumps(content)
                    except Exception:
                        content = str(content)
                out.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "toolResult": {
                                    "toolUseId": msg.tool_call_id,
                                    "content": [{"text": content}],
                                }
                            }
                        ],
                    }
                )
                continue

            # Text content
            if isinstance(msg.content, str) and msg.content:
                content_blocks.append({"text": msg.content})
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, str):
                        if block:
                            content_blocks.append({"text": block})
                        continue
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type")
                    # Anthropic-style text block
                    if btype == "text" or "text" in block and btype is None:
                        txt = block.get("text") or ""
                        if txt:
                            content_blocks.append({"text": txt})
                    # Anthropic-style assistant tool_use block
                    elif btype == "tool_use":
                        content_blocks.append(
                            {
                                "toolUse": {
                                    "toolUseId": block.get("id"),
                                    "name": block.get("name"),
                                    "input": block.get("input") or {},
                                }
                            }
                        )
                    # Anthropic-style user tool_result block
                    elif btype == "tool_result":
                        result_content = block.get("content")
                        if isinstance(result_content, list):
                            text_parts = [
                                c.get("text", "") if isinstance(c, dict) else str(c)
                                for c in result_content
                            ]
                            result_text = "\n".join(p for p in text_parts if p)
                        elif isinstance(result_content, str):
                            result_text = result_content
                        else:
                            import json as _json

                            try:
                                result_text = _json.dumps(result_content)
                            except Exception:
                                result_text = str(result_content)
                        tr = {
                            "toolUseId": block.get("tool_use_id"),
                            "content": [{"text": result_text or ""}],
                        }
                        if block.get("is_error"):
                            tr["status"] = "error"
                        content_blocks.append({"toolResult": tr})
                    # Already-native Converse blocks pass through
                    elif (
                        "toolUse" in block
                        or "toolResult" in block
                        or "image" in block
                        or "document" in block
                    ):
                        content_blocks.append(block)

            # Assistant tool calls
            if msg.role == "assistant" and msg.tool_calls:
                for tc in msg.tool_calls:
                    # Accept both dict and LLMToolCall objects.
                    if hasattr(tc, "id"):
                        tc_id, tc_name, tc_input = tc.id, tc.name, tc.input
                    else:
                        tc_id = tc.get("id")
                        tc_name = tc.get("name")
                        tc_input = tc.get("input") or tc.get("arguments") or {}
                    content_blocks.append(
                        {
                            "toolUse": {
                                "toolUseId": tc_id,
                                "name": tc_name,
                                "input": tc_input if isinstance(tc_input, dict) else {},
                            }
                        }
                    )

            # Converse rejects empty text blocks; drop any we may have produced.
            content_blocks = [
                b
                for b in content_blocks
                if not ("text" in b and not (b.get("text") or "").strip())
            ]

            if not content_blocks:
                # Nothing meaningful to send for this turn — skip it entirely
                # rather than emitting an empty content block (Converse rejects).
                continue

            out.append({"role": msg.role, "content": content_blocks})

        return system_blocks, out

    def format_tools_for_api(self, tools):
        """Bedrock Converse tool format."""
        return [
            {
                "toolSpec": {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": {"json": t.input_schema},
                }
            }
            for t in tools
        ]

    # ------------------------------------------------------------------ #
    # Response parsing helpers                                           #
    # ------------------------------------------------------------------ #

    def _map_stop_reason(self, stop_reason):
        mapping = {
            "end_turn": "end_turn",
            "tool_use": "tool_use",
            "max_tokens": "max_tokens",
            "stop_sequence": "stop_sequence",
            "content_filtered": "refusal",
            "guardrail_intervened": "refusal",
        }
        return mapping.get(stop_reason, stop_reason)

    def _wrap_client_error(self, e):
        """Map a botocore ClientError into a typed Zango exception."""
        err = getattr(e, "response", {}) or {}
        code = (err.get("Error") or {}).get("Code", "")
        status = (err.get("ResponseMetadata") or {}).get("HTTPStatusCode")
        if code in ("ThrottlingException", "TooManyRequestsException"):
            return RateLimitExceeded(str(e))
        return LLMAPIError(str(e), status_code=status, original_error=e)

    # ------------------------------------------------------------------ #
    # Structured output helper                                          #
    # ------------------------------------------------------------------ #

    def _normalize_schema_for_bedrock(self, schema):
        """Recursively normalize a JSON Schema dict for Bedrock's Draft 2020-12 subset.

        Bedrock does not support type arrays (e.g. ["string", "null"]).
        Convert them to anyOf: [{type: X}, {type: "null"}].
        """
        if not isinstance(schema, dict):
            return schema

        result = {}
        for key, value in schema.items():
            if key == "type" and isinstance(value, list):
                # e.g. ["string", "null"] → handled below by wrapping in anyOf
                non_null = [t for t in value if t != "null"]
                has_null = "null" in value
                if has_null and len(non_null) == 1:
                    # Replace this node's "type" with anyOf at the parent level
                    result["anyOf"] = [{"type": non_null[0]}, {"type": "null"}]
                elif has_null and len(non_null) == 0:
                    result["type"] = "null"
                else:
                    # Multiple non-null types — wrap all in anyOf
                    result["anyOf"] = [{"type": t} for t in value]
            elif isinstance(value, dict):
                result[key] = self._normalize_schema_for_bedrock(value)
            elif isinstance(value, list):
                result[key] = [
                    self._normalize_schema_for_bedrock(item)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _build_output_config(self, response_format):
        """Translate a response_format value into a Bedrock outputConfig dict.

        Accepts:
          - a dict  → treated as a JSON Schema; passed to outputConfig.textFormat
          - "json"  → ignored (no schema enforcement, just a hint in the prompt)
          - None    → returns None (no outputConfig added)

        The schema must be serialised to a JSON string per the Bedrock API spec.
        """
        if not response_format or response_format == "json":
            return None
        if not isinstance(response_format, dict):
            return None

        import json as _json

        normalized = self._normalize_schema_for_bedrock(response_format)

        return {
            "textFormat": {
                "type": "json_schema",
                "structure": {
                    "jsonSchema": {
                        "schema": _json.dumps(normalized),
                        "name": response_format.get("title", "output_schema"),
                        "description": response_format.get("description", ""),
                    }
                },
            }
        }

    # ------------------------------------------------------------------ #
    # complete()                                                         #
    # ------------------------------------------------------------------ #

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
        # boto3 has no per-call timeout — bake it in at __init__. Consume the
        # kwarg silently to avoid unexpected-keyword errors from upstream.
        kwargs.pop("timeout_seconds", None)
        response_format = kwargs.pop("response_format", None)

        system_blocks, converse_messages = self._convert_messages_for_bedrock(messages)
        if system:
            system_blocks = (system_blocks or []) + [{"text": system}]

        inference_config = {
            "temperature": float(temperature),
            "maxTokens": int(max_tokens),
        }
        if stop_sequences:
            inference_config["stopSequences"] = list(stop_sequences)

        resolved_model = self._resolve_model_id(model)
        print(
            f"[Bedrock] raw model={model!r}  resolved={resolved_model!r}  region={self.config.get('aws_region')!r}  response_format={response_format!r}"
        )
        api_kwargs = {
            "modelId": resolved_model,
            "messages": converse_messages,
            "inferenceConfig": inference_config,
        }
        if system_blocks:
            api_kwargs["system"] = system_blocks
        if tools:
            api_kwargs["toolConfig"] = {"tools": self.format_tools_for_api(tools)}
        output_config = self._build_output_config(response_format)
        if output_config:
            api_kwargs["outputConfig"] = output_config

        client = self._schema_client if output_config else self._client
        start = time.monotonic()
        try:
            response = client.converse(**api_kwargs)
        except self._ReadTimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except self._ClientError as e:
            raise self._wrap_client_error(e) from e
        latency_ms = int((time.monotonic() - start) * 1000)

        output_msg = (response.get("output") or {}).get("message") or {}
        content_blocks = output_msg.get("content") or []

        texts = []
        tool_calls = []
        for block in content_blocks:
            if "text" in block:
                texts.append(block["text"])
            elif "toolUse" in block:
                tu = block["toolUse"]
                tool_calls.append(
                    LLMToolCall(
                        id=tu.get("toolUseId"),
                        name=tu.get("name"),
                        input=tu.get("input") or {},
                    )
                )

        usage_data = response.get("usage") or {}
        usage = LLMUsage(
            input_tokens=int(usage_data.get("inputTokens", 0) or 0),
            output_tokens=int(usage_data.get("outputTokens", 0) or 0),
        )

        return LLMResponse(
            content="\n".join(texts),
            tool_calls=tool_calls,
            stop_reason=self._map_stop_reason(response.get("stopReason")),
            usage=usage,
            model=api_kwargs["modelId"],
            raw_response=response,
            latency_ms=latency_ms,
        )

    # ------------------------------------------------------------------ #
    # stream()                                                           #
    # ------------------------------------------------------------------ #

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
        kwargs.pop("timeout_seconds", None)
        response_format = kwargs.pop("response_format", None)

        system_blocks, converse_messages = self._convert_messages_for_bedrock(messages)
        if system:
            system_blocks = (system_blocks or []) + [{"text": system}]

        inference_config = {
            "temperature": float(temperature),
            "maxTokens": int(max_tokens),
        }
        if stop_sequences:
            inference_config["stopSequences"] = list(stop_sequences)

        api_kwargs = {
            "modelId": self._resolve_model_id(model),
            "messages": converse_messages,
            "inferenceConfig": inference_config,
        }
        if system_blocks:
            api_kwargs["system"] = system_blocks
        if tools:
            api_kwargs["toolConfig"] = {"tools": self.format_tools_for_api(tools)}
        output_config = self._build_output_config(response_format)
        if output_config:
            api_kwargs["outputConfig"] = output_config

        client = self._schema_client if output_config else self._client
        try:
            response = client.converse_stream(**api_kwargs)
        except self._ReadTimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except self._ClientError as e:
            raise self._wrap_client_error(e) from e

        stop_reason = None
        usage = None

        try:
            for event in response.get("stream", []):
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"].get("delta") or {}
                    if "text" in delta:
                        yield LLMStreamChunk(delta_text=delta["text"])
                    elif "toolUse" in delta:
                        partial = delta["toolUse"].get("input")
                        if partial is not None:
                            yield LLMStreamChunk(
                                delta_tool_call={"partial_json": partial}
                            )
                elif "messageStop" in event:
                    stop_reason = event["messageStop"].get("stopReason")
                elif "metadata" in event:
                    usage_data = event["metadata"].get("usage") or {}
                    if usage_data:
                        usage = LLMUsage(
                            input_tokens=int(usage_data.get("inputTokens", 0) or 0),
                            output_tokens=int(usage_data.get("outputTokens", 0) or 0),
                        )
        except self._ReadTimeoutError as e:
            raise LLMTimeoutError(str(e)) from e
        except self._ClientError as e:
            raise self._wrap_client_error(e) from e

        yield LLMStreamChunk(
            is_final=True,
            usage=usage or LLMUsage(input_tokens=0, output_tokens=0),
            stop_reason=self._map_stop_reason(stop_reason),
        )

    # ------------------------------------------------------------------ #
    # Discovery / validation                                             #
    # ------------------------------------------------------------------ #

    @classmethod
    def fetch_models(cls, config: dict) -> list[dict]:
        """Fetch ON_DEMAND text-generation models via ``bedrock.list_foundation_models``.

        Raises ``ValueError`` with a human-readable message on auth failure
        so the platform API can surface it cleanly to the admin UI.
        """
        try:
            import boto3

            from botocore.exceptions import ClientError, NoCredentialsError
        except ImportError as e:
            raise ValueError("boto3 is not installed. Run: pip install boto3") from e

        access_key = config.get("aws_access_key_id")
        secret_key = config.get("aws_secret_access_key")
        missing = [
            n
            for n, v in (
                ("aws_access_key_id", access_key),
                ("aws_secret_access_key", secret_key),
            )
            if not v
        ]
        if missing:
            raise ValueError(
                f"Missing required AWS credential(s): {', '.join(missing)}."
            )

        region = config.get("aws_region", "us-east-1")

        try:
            bedrock_client = boto3.client(
                "bedrock",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )
            fm_response = bedrock_client.list_foundation_models(
                byOutputModality="TEXT",
                byInferenceType="ON_DEMAND",
            )
        except NoCredentialsError as e:
            raise ValueError(
                "Invalid AWS credentials. Check your Access Key ID and Secret Access Key."
            ) from e
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in (
                "UnauthorizedException",
                "AccessDeniedException",
                "InvalidClientTokenId",
                "UnrecognizedClientException",
                "InvalidSignatureException",
                "AuthFailure",
            ):
                raise ValueError(
                    f"Invalid AWS credentials or permissions denied ({code}). "
                    "Check your Access Key ID, Secret Access Key, and IAM permissions for Bedrock."
                ) from e
            raise ValueError(f"AWS Bedrock error: {e}") from e
        except Exception as e:
            raise ValueError(f"Could not connect to AWS Bedrock: {e}") from e

        # On-demand models keyed by bare modelId.
        live_by_id = {m["modelId"]: m for m in fm_response.get("modelSummaries", [])}

        # Cross-region inference profiles — these are the only way to access
        # Claude 4.x and latest Claude 3.5 models on Bedrock.
        # list_inference_profiles returns both system-defined (SYSTEM_DEFINED)
        # and customer profiles; we only want SYSTEM_DEFINED ones here.
        # profile_id → profile entry, keyed by the full profile ID as returned by AWS.
        # profile IDs look like "apac.anthropic.claude-3-5-sonnet-..." or "global.anthropic.claude-sonnet-4-6".
        # We store the full profile_id as the resolved model ID — it's what Bedrock Converse accepts.
        # We also maintain a bare_id → profile_id mapping so static catalog entries can find their profile.
        profile_by_profile_id = {}  # full profile_id → profile entry
        bare_to_profile_id = {}  # bare model ID (no geo prefix) → full profile_id
        try:
            ip_response = bedrock_client.list_inference_profiles(
                typeEquals="SYSTEM_DEFINED"
            )
            for profile in ip_response.get("inferenceProfileSummaries", []):
                profile_id = profile.get("inferenceProfileId", "")
                if not profile_id:
                    continue
                profile_by_profile_id[profile_id] = profile
                # Derive bare ID by stripping geography or global prefix
                bare_id = profile_id
                for geo in ("us.", "eu.", "apac.", "global."):
                    if bare_id.startswith(geo):
                        bare_id = bare_id[len(geo) :]
                        break
                bare_to_profile_id[bare_id] = profile_id
        except Exception:
            # list_inference_profiles may not be available in all regions/SDKs;
            # degrade gracefully.
            pass

        prefix = _geography_prefix_for_region(region)
        geography_label = {"us.": "US", "eu.": "EU", "apac.": "APAC"}.get(prefix or "")

        seen_ids = set()
        models = []

        # First: overlay static catalog entries (gives us pricing + capability flags).
        for entry in cls.supported_models:
            bare_id = entry["id"]
            live_fm = live_by_id.get(bare_id)
            matched_profile_id = bare_to_profile_id.get(bare_id)
            live_profile = (
                profile_by_profile_id.get(matched_profile_id)
                if matched_profile_id
                else None
            )
            name = (
                (live_profile.get("inferenceProfileName") if live_profile else None)
                or (live_fm.get("modelName") if live_fm else None)
                or entry["name"]
            )
            if entry.get("requires_inference_profile"):
                if matched_profile_id:
                    # Use the exact profile ID returned by AWS (may be apac. or global.)
                    resolved_id = matched_profile_id
                    geo_label = (
                        matched_profile_id.split(".")[0].upper()
                        if "." in matched_profile_id
                        else "Cross-region"
                    )
                    models.append(
                        {
                            **entry,
                            "id": resolved_id,
                            "name": name,
                            "inference_profile": f"{geo_label} cross-region",
                        }
                    )
                elif prefix is None:
                    resolved_id = bare_id
                    models.append(
                        {
                            **entry,
                            "id": resolved_id,
                            "name": name,
                            "disabled": True,
                            "disabled_reason": (
                                f"Requires a cross-region inference profile "
                                f"(US / EU / APAC). {region} is not in a "
                                f"supported geography — switch regions to use this model."
                            ),
                            "inference_profile": "Cross-region",
                        }
                    )
                else:
                    resolved_id = f"{prefix}{bare_id}"
                    models.append(
                        {
                            **entry,
                            "id": resolved_id,
                            "name": name,
                            "inference_profile": f"{geography_label} cross-region",
                        }
                    )
                seen_ids.add(resolved_id)
            else:
                models.append({**entry, "name": name})
                seen_ids.add(bare_id)

        # Second: surface live inference profiles NOT in our static catalog.
        for profile_id, profile in profile_by_profile_id.items():
            if profile_id in seen_ids:
                continue
            profile_name = profile.get("inferenceProfileName", profile_id)
            models.append(
                {
                    "id": profile_id,
                    "name": profile_name,
                    "context_window": 200000,
                    "max_output_tokens": 8192,
                    "input_cost_per_mtok": None,
                    "output_cost_per_mtok": None,
                    "supports_tools": True,
                    "supports_vision": True,
                    "supports_streaming": True,
                    "requires_inference_profile": True,
                    "inference_profile": f"{geography_label} cross-region",
                }
            )
            seen_ids.add(profile_id)

        # Third: surface on-demand models not in our static catalog or profiles.
        for mid, m in live_by_id.items():
            if mid in seen_ids:
                continue
            models.append(
                {
                    "id": mid,
                    "name": m.get("modelName", mid),
                    "context_window": 200000,
                    "max_output_tokens": 8192,
                    "input_cost_per_mtok": None,
                    "output_cost_per_mtok": None,
                    "supports_tools": True,
                    "supports_vision": "IMAGE" in m.get("inputModalities", []),
                    "supports_streaming": m.get("responseStreamingSupported", False),
                    "requires_inference_profile": False,
                }
            )

        return models

    def validate_config(self):
        try:
            import boto3

            bedrock_client = boto3.client(
                "bedrock",
                aws_access_key_id=self.config.get("aws_access_key_id"),
                aws_secret_access_key=self.config.get("aws_secret_access_key"),
                region_name=self.config.get("aws_region", "us-east-1"),
            )
            bedrock_client.list_foundation_models()
        except Exception as e:
            return (False, str(e))

        # Region / model compatibility check for cross-region inference profiles.
        default_model = self.config.get("default_model")
        if default_model:
            # Strip any geography prefix the admin may have supplied so we look
            # up the bare ID in the catalog.
            bare = default_model
            for p in ("us.", "eu.", "apac.", "global."):
                if bare.startswith(p):
                    bare = bare[len(p) :]
                    break
            info = next((m for m in self.supported_models if m["id"] == bare), None)
            if info and info.get("requires_inference_profile"):
                region = self.config.get("aws_region", "us-east-1")
                if _geography_prefix_for_region(region) is None:
                    return (
                        False,
                        f"{default_model} requires a US, EU, or APAC region; "
                        f"{region} is not in a supported geography.",
                    )

        return (True, None)

    def get_models(self):
        """Fetch live models from Bedrock and overlay static catalog metadata.

        Falls back to the static catalog if the live call fails (e.g. network
        issue after the provider was already saved).
        """
        try:
            return self.__class__.fetch_models(self.config)
        except Exception:
            # Graceful degradation: return static catalog with region-resolved IDs.
            region = self.config.get("aws_region", "us-east-1")
            prefix = _geography_prefix_for_region(region)
            geography_label = {"us.": "US", "eu.": "EU", "apac.": "APAC"}.get(
                prefix or ""
            )
            out = []
            for entry in self.supported_models:
                if entry.get("requires_inference_profile"):
                    if prefix is None:
                        out.append(
                            {
                                **entry,
                                "disabled": True,
                                "disabled_reason": (
                                    f"Requires a cross-region inference profile "
                                    f"(US / EU / APAC). {region} is not in a "
                                    f"supported geography — switch regions to use this model."
                                ),
                                "inference_profile": "Cross-region",
                            }
                        )
                    else:
                        out.append(
                            {
                                **entry,
                                "id": f"{prefix}{entry['id']}",
                                "inference_profile": f"{geography_label} cross-region",
                            }
                        )
                else:
                    out.append(dict(entry))
            return out

    def compute_cost(self, usage, model):
        """Cost lookup keyed by the bare model ID (strip any geography prefix)."""
        bare = model
        for p in ("us.", "eu.", "apac."):
            if bare.startswith(p):
                bare = bare[len(p) :]
                break
        info = next((m for m in self.supported_models if m["id"] == bare), None)
        if not info:
            return 0.0
        input_cost = (usage.input_tokens / 1_000_000) * (
            info.get("input_cost_per_mtok") or 0
        )
        output_cost = (usage.output_tokens / 1_000_000) * (
            info.get("output_cost_per_mtok") or 0
        )
        return round(input_cost + output_cost, 6)
