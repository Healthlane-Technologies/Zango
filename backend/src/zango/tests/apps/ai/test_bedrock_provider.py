"""
Unit tests for the AWS Bedrock provider.

boto3 is fully mocked — these tests never touch AWS. They exercise:
  - Converse payload shape (messages, system, inferenceConfig, toolConfig)
  - Tool-call extraction from `toolUse` blocks
  - Stop-reason mapping
  - Streaming yields text deltas then a final chunk with usage
  - ClientError("ThrottlingException") -> RateLimitExceeded
  - Missing boto3 surfaces as ValueError from fetch_models()
  - Cross-region inference profile prefix resolution
  - get_models() filters models that need a profile when region has none
  - validate_config() flags region/model mismatch up front
"""

import sys

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from zango.ai.exceptions import LLMAPIError, RateLimitExceeded
from zango.ai.providers.base import LLMMessage, LLMToolDef


# ──────────────────────────────────────────────────────────────────────────────
# Fake botocore exceptions / Config so we can import the provider without boto3
# ──────────────────────────────────────────────────────────────────────────────

class _FakeClientError(Exception):
    def __init__(self, code="InternalServerError", status=500, message="boom"):
        self.response = {
            "Error": {"Code": code, "Message": message},
            "ResponseMetadata": {"HTTPStatusCode": status},
        }
        super().__init__(message)


class _FakeReadTimeoutError(Exception):
    pass


def _install_fake_boto3():
    """Install fake boto3 / botocore modules into sys.modules so the provider's
    lazy ``import boto3`` succeeds without the real dependency."""
    fake_boto3 = MagicMock()
    fake_boto3.client = MagicMock(return_value=MagicMock())

    fake_botocore = MagicMock()
    fake_botocore_config = MagicMock()
    fake_botocore_config.Config = MagicMock(return_value=MagicMock())
    fake_botocore_exceptions = MagicMock()
    fake_botocore_exceptions.ClientError = _FakeClientError
    fake_botocore_exceptions.ReadTimeoutError = _FakeReadTimeoutError
    fake_botocore_exceptions.NoCredentialsError = Exception

    sys.modules["boto3"] = fake_boto3
    sys.modules["botocore"] = fake_botocore
    sys.modules["botocore.config"] = fake_botocore_config
    sys.modules["botocore.exceptions"] = fake_botocore_exceptions
    return fake_boto3


def _make_provider(region="us-east-1"):
    _install_fake_boto3()
    from zango.ai.providers.bedrock import BedrockProvider

    provider = BedrockProvider(
        {
            "aws_access_key_id": "AKIA000",
            "aws_secret_access_key": "SECRET",  # pragma: allowlist secret
            "aws_region": region,
            "default_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        }
    )
    provider._client = MagicMock()
    provider._ClientError = _FakeClientError
    provider._ReadTimeoutError = _FakeReadTimeoutError
    return provider


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


class ResolveModelIdTest(SimpleTestCase):
    # ── Degraded fallback: live list unavailable → prefix construction ──────
    # The fake control-plane client returns a MagicMock for
    # list_inference_profiles, so _live_profile_map() degrades to {} and the
    # resolver falls back to deriving the prefix from the region.

    def test_us_region_prefix_fallback(self):
        p = _make_provider(region="us-east-1")
        resolved = p._resolve_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.assertEqual(resolved, "us.anthropic.claude-3-5-sonnet-20241022-v2:0")

    def test_eu_region_prefix_fallback(self):
        p = _make_provider(region="eu-west-1")
        resolved = p._resolve_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.assertEqual(resolved, "eu.anthropic.claude-3-5-sonnet-20241022-v2:0")

    def test_ap_region_uses_apac_prefix_fallback(self):
        p = _make_provider(region="ap-northeast-1")
        resolved = p._resolve_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.assertEqual(resolved, "apac.anthropic.claude-3-5-sonnet-20241022-v2:0")

    def test_unsupported_geography_raises(self):
        p = _make_provider(region="ca-central-1")
        with self.assertRaises(LLMAPIError):
            p._resolve_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0")

    def test_model_without_profile_passes_through(self):
        p = _make_provider(region="us-east-1")
        self.assertEqual(
            p._resolve_model_id("amazon.nova-pro-v1:0"),
            "amazon.nova-pro-v1:0",
        )

    def test_already_prefixed_id_passes_through(self):
        p = _make_provider(region="us-east-1")
        prefixed = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        self.assertEqual(p._resolve_model_id(prefixed), prefixed)

    # ── Live resolution: list_inference_profiles is authoritative ───────────

    def test_live_profile_id_is_used_verbatim(self):
        """When AWS reports a profile, use its exact ID (not prefix guessing)."""
        p = _make_provider(region="ap-northeast-1")
        p._profile_map = {
            "anthropic.claude-sonnet-4-5-20250929-v1:0": (
                "apac.anthropic.claude-sonnet-4-5-20250929-v1:0"
            ),
        }
        self.assertEqual(
            p._resolve_model_id("anthropic.claude-sonnet-4-5-20250929-v1:0"),
            "apac.anthropic.claude-sonnet-4-5-20250929-v1:0",
        )

    def test_model_missing_from_live_list_raises_clear_error(self):
        """A model AWS does not offer in this geography must fail clearly,
        not be fabricated into a ValidationException-bound ID (the original bug:
        apac.anthropic.claude-opus-4-1-...)."""
        p = _make_provider(region="ap-south-1")
        # Live list reachable but does NOT contain Opus 4.1.
        p._profile_map = {
            "anthropic.claude-sonnet-4-5-20250929-v1:0": (
                "apac.anthropic.claude-sonnet-4-5-20250929-v1:0"
            ),
        }
        with self.assertRaises(LLMAPIError) as ctx:
            p._resolve_model_id("anthropic.claude-opus-4-1-20250805-v1:0")
        self.assertIn("not available", str(ctx.exception).lower())

    def test_live_map_prefers_geo_profile_over_global(self):
        p = _make_provider(region="us-east-1")
        p._control_client = MagicMock()
        p._control_client.list_inference_profiles.return_value = {
            "inferenceProfileSummaries": [
                {"inferenceProfileId": "global.anthropic.claude-opus-4-1-20250805-v1:0"},
                {"inferenceProfileId": "us.anthropic.claude-opus-4-1-20250805-v1:0"},
            ]
        }
        self.assertEqual(
            p._resolve_model_id("anthropic.claude-opus-4-1-20250805-v1:0"),
            "us.anthropic.claude-opus-4-1-20250805-v1:0",
        )

    def test_live_map_is_cached(self):
        """list_inference_profiles is called at most once per provider."""
        p = _make_provider(region="us-east-1")
        p._control_client = MagicMock()
        p._control_client.list_inference_profiles.return_value = {
            "inferenceProfileSummaries": [
                {"inferenceProfileId": "us.anthropic.claude-sonnet-4-5-20250929-v1:0"},
            ]
        }
        p._resolve_model_id("anthropic.claude-sonnet-4-5-20250929-v1:0")
        p._resolve_model_id("anthropic.claude-sonnet-4-5-20250929-v1:0")
        self.assertEqual(p._control_client.list_inference_profiles.call_count, 1)


class CompletePayloadTest(SimpleTestCase):
    def _bedrock_response(self):
        return {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Hello there"}],
                }
            },
            "stopReason": "end_turn",
            "usage": {"inputTokens": 12, "outputTokens": 7},
        }

    def test_payload_shape(self):
        p = _make_provider()
        p._client.converse.return_value = self._bedrock_response()

        p.complete(
            messages=[
                LLMMessage(role="system", content="You are helpful."),
                LLMMessage(role="user", content="Hi"),
            ],
            model="amazon.nova-pro-v1:0",
            temperature=0.5,
            max_tokens=512,
            stop_sequences=["STOP"],
        )

        kwargs = p._client.converse.call_args.kwargs
        self.assertEqual(kwargs["modelId"], "amazon.nova-pro-v1:0")
        self.assertEqual(kwargs["system"], [{"text": "You are helpful."}])
        self.assertEqual(kwargs["inferenceConfig"]["temperature"], 0.5)
        self.assertEqual(kwargs["inferenceConfig"]["maxTokens"], 512)
        self.assertEqual(kwargs["inferenceConfig"]["stopSequences"], ["STOP"])
        # System message is stripped from messages
        self.assertEqual(len(kwargs["messages"]), 1)
        self.assertEqual(kwargs["messages"][0]["role"], "user")
        self.assertEqual(kwargs["messages"][0]["content"], [{"text": "Hi"}])

    def test_tool_config_included_when_tools_passed(self):
        p = _make_provider()
        p._client.converse.return_value = self._bedrock_response()

        tools = [
            LLMToolDef(
                name="search",
                description="Search records",
                input_schema={"type": "object", "properties": {}},
            )
        ]
        p.complete(
            messages=[LLMMessage(role="user", content="hi")],
            model="amazon.nova-pro-v1:0",
            tools=tools,
        )

        kwargs = p._client.converse.call_args.kwargs
        self.assertIn("toolConfig", kwargs)
        spec = kwargs["toolConfig"]["tools"][0]["toolSpec"]
        self.assertEqual(spec["name"], "search")
        self.assertIn("inputSchema", spec)
        self.assertIn("json", spec["inputSchema"])

    def test_tool_calls_extracted_from_tooluse_blocks(self):
        p = _make_provider()
        p._client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "calling tool"},
                        {
                            "toolUse": {
                                "toolUseId": "tu-1",
                                "name": "search",
                                "input": {"q": "x"},
                            }
                        },
                    ],
                }
            },
            "stopReason": "tool_use",
            "usage": {"inputTokens": 5, "outputTokens": 3},
        }

        resp = p.complete(
            messages=[LLMMessage(role="user", content="hi")],
            model="amazon.nova-pro-v1:0",
        )

        self.assertEqual(resp.stop_reason, "tool_use")
        self.assertEqual(len(resp.tool_calls), 1)
        self.assertEqual(resp.tool_calls[0].id, "tu-1")
        self.assertEqual(resp.tool_calls[0].name, "search")
        self.assertEqual(resp.tool_calls[0].input, {"q": "x"})
        self.assertEqual(resp.usage.input_tokens, 5)
        self.assertEqual(resp.usage.output_tokens, 3)

    def test_stop_reason_max_tokens_maps(self):
        p = _make_provider()
        p._client.converse.return_value = {
            "output": {"message": {"role": "assistant", "content": []}},
            "stopReason": "max_tokens",
            "usage": {"inputTokens": 1, "outputTokens": 1},
        }
        resp = p.complete(
            messages=[LLMMessage(role="user", content="hi")],
            model="amazon.nova-pro-v1:0",
        )
        self.assertEqual(resp.stop_reason, "max_tokens")

    def test_timeout_seconds_kwarg_silently_consumed(self):
        p = _make_provider()
        p._client.converse.return_value = {
            "output": {"message": {"role": "assistant", "content": [{"text": "ok"}]}},
            "stopReason": "end_turn",
            "usage": {"inputTokens": 1, "outputTokens": 1},
        }
        # Should not raise unexpected-keyword error.
        p.complete(
            messages=[LLMMessage(role="user", content="hi")],
            model="amazon.nova-pro-v1:0",
            timeout_seconds=60,
        )


class ToolResultMessageTest(SimpleTestCase):
    def test_role_tool_becomes_user_with_toolresult_block(self):
        p = _make_provider()
        p._client.converse.return_value = {
            "output": {"message": {"role": "assistant", "content": [{"text": "ok"}]}},
            "stopReason": "end_turn",
            "usage": {"inputTokens": 1, "outputTokens": 1},
        }

        p.complete(
            messages=[
                LLMMessage(role="user", content="hi"),
                LLMMessage(
                    role="assistant",
                    content="",
                    tool_calls=[{"id": "tu-1", "name": "x", "input": {}}],
                ),
                LLMMessage(role="tool", content="42", tool_call_id="tu-1"),
            ],
            model="amazon.nova-pro-v1:0",
        )

        kwargs = p._client.converse.call_args.kwargs
        # Last message is the tool result, mapped to a user role.
        last = kwargs["messages"][-1]
        self.assertEqual(last["role"], "user")
        block = last["content"][0]
        self.assertIn("toolResult", block)
        self.assertEqual(block["toolResult"]["toolUseId"], "tu-1")
        self.assertEqual(block["toolResult"]["content"], [{"text": "42"}])


class StreamingTest(SimpleTestCase):
    def test_stream_yields_text_then_final_chunk(self):
        p = _make_provider()
        events = [
            {"contentBlockDelta": {"delta": {"text": "hel"}}},
            {"contentBlockDelta": {"delta": {"text": "lo"}}},
            {"messageStop": {"stopReason": "end_turn"}},
            {"metadata": {"usage": {"inputTokens": 4, "outputTokens": 2}}},
        ]
        p._client.converse_stream.return_value = {"stream": iter(events)}

        chunks = list(
            p.stream(
                messages=[LLMMessage(role="user", content="hi")],
                model="amazon.nova-pro-v1:0",
            )
        )

        # 2 text deltas + final
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].delta_text, "hel")
        self.assertEqual(chunks[1].delta_text, "lo")
        self.assertTrue(chunks[-1].is_final)
        self.assertEqual(chunks[-1].usage.input_tokens, 4)
        self.assertEqual(chunks[-1].usage.output_tokens, 2)
        self.assertEqual(chunks[-1].stop_reason, "end_turn")


class ExceptionMappingTest(SimpleTestCase):
    def test_throttling_maps_to_rate_limit(self):
        p = _make_provider()
        p._client.converse.side_effect = _FakeClientError(
            code="ThrottlingException", status=429
        )
        with self.assertRaises(RateLimitExceeded):
            p.complete(
                messages=[LLMMessage(role="user", content="hi")],
                model="amazon.nova-pro-v1:0",
            )

    def test_generic_client_error_maps_to_llm_api_error(self):
        p = _make_provider()
        p._client.converse.side_effect = _FakeClientError(
            code="ValidationException", status=400
        )
        with self.assertRaises(LLMAPIError) as ctx:
            p.complete(
                messages=[LLMMessage(role="user", content="hi")],
                model="amazon.nova-pro-v1:0",
            )
        self.assertEqual(ctx.exception.status_code, 400)


class GetModelsTest(SimpleTestCase):
    def test_us_region_prefixes_profile_models(self):
        p = _make_provider(region="us-east-1")
        models = p.get_models()
        sonnet = next(
            m for m in models if "claude-3-5-sonnet-20241022-v2:0" in m["id"]
        )
        self.assertEqual(
            sonnet["id"], "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

    def test_unsupported_geography_marks_profile_models_disabled(self):
        p = _make_provider(region="ca-central-1")
        models = p.get_models()
        by_id = {m["id"]: m for m in models}
        # Profile-required entries still surface (so the user sees the full
        # catalog), but they carry disabled=True + a human-readable reason.
        sonnet = by_id.get("anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.assertIsNotNone(sonnet)
        self.assertTrue(sonnet["disabled"])
        self.assertIn("cross-region", sonnet["disabled_reason"].lower())
        # Non-profile models surface normally
        self.assertIn("amazon.nova-pro-v1:0", by_id)
        self.assertFalse(by_id["amazon.nova-pro-v1:0"].get("disabled"))

    def test_apac_region_resolves_sonnet_45(self):
        p = _make_provider(region="ap-south-1")
        models = p.get_models()
        sonnet = next(
            m for m in models
            if m["id"] == "apac.anthropic.claude-sonnet-4-5-20250929-v1:0"
        )
        self.assertEqual(sonnet["inference_profile"], "APAC cross-region")
        self.assertFalse(sonnet.get("disabled"))

    def test_model_without_live_profile_is_omitted(self):
        """When list_inference_profiles is reachable but lacks a profile for a
        catalog model in this region, that model must NOT appear in the list
        (the original bug: a selectable apac.anthropic.claude-opus-4-1-... that
        AWS rejects at invoke time)."""
        _install_fake_boto3()
        from zango.ai.providers.bedrock import BedrockProvider

        with patch("boto3.client") as mock_client:
            inst = mock_client.return_value
            inst.list_foundation_models.return_value = {"modelSummaries": []}
            # AWS only offers Sonnet 4.5 in APAC — no Opus 4.1 profile.
            inst.list_inference_profiles.return_value = {
                "inferenceProfileSummaries": [
                    {
                        "inferenceProfileId": (
                            "apac.anthropic.claude-sonnet-4-5-20250929-v1:0"
                        ),
                        "inferenceProfileName": "Claude Sonnet 4.5",
                    },
                ]
            }
            models = BedrockProvider.fetch_models(
                {
                    "aws_access_key_id": "x",
                    "aws_secret_access_key": "y",  # pragma: allowlist secret
                    "aws_region": "ap-south-1",
                }
            )
        ids = {m["id"] for m in models}
        # Opus 4.1 has no live APAC profile → omitted entirely (no apac./bare id).
        self.assertNotIn("apac.anthropic.claude-opus-4-1-20250805-v1:0", ids)
        self.assertNotIn("anthropic.claude-opus-4-1-20250805-v1:0", ids)
        # Sonnet 4.5 has a live profile → present.
        self.assertIn("apac.anthropic.claude-sonnet-4-5-20250929-v1:0", ids)

    def test_global_profile_labelled_global_not_region(self):
        """A global. profile must be labelled 'Global cross-region' from its own
        prefix, NOT 'APAC' derived from the calling region (display bug)."""
        _install_fake_boto3()
        from zango.ai.providers.bedrock import BedrockProvider

        with patch("boto3.client") as mock_client:
            inst = mock_client.return_value
            inst.list_foundation_models.return_value = {"modelSummaries": []}
            # A live profile not in the static catalog, with a global. prefix,
            # surfaced while calling from an APAC region.
            inst.list_inference_profiles.return_value = {
                "inferenceProfileSummaries": [
                    {
                        "inferenceProfileId": "global.anthropic.claude-sonnet-4-6",
                        "inferenceProfileName": "Global Anthropic Claude Sonnet 4.6",
                    },
                ]
            }
            models = BedrockProvider.fetch_models(
                {
                    "aws_access_key_id": "x",
                    "aws_secret_access_key": "y",  # pragma: allowlist secret
                    "aws_region": "ap-south-1",
                }
            )
        sonnet46 = next(
            m for m in models if m["id"] == "global.anthropic.claude-sonnet-4-6"
        )
        self.assertEqual(sonnet46["inference_profile"], "Global cross-region")
        self.assertNotIn("APAC", sonnet46["inference_profile"])


class ValidateConfigTest(SimpleTestCase):
    def test_flags_region_model_mismatch(self):
        p = _make_provider(region="ca-central-1")
        # Make boto3.client(...).list_foundation_models succeed
        with patch("boto3.client") as mock_client:
            mock_client.return_value.list_foundation_models.return_value = {
                "modelSummaries": []
            }
            ok, err = p.validate_config()
        self.assertFalse(ok)
        self.assertIn("supported geography", err)


class FetchModelsTest(SimpleTestCase):
    def test_missing_boto3_raises_value_error(self):
        # Force ImportError on lazy import
        with patch.dict(sys.modules, {"boto3": None}):
            from zango.ai.providers.bedrock import BedrockProvider

            with self.assertRaises(ValueError) as ctx:
                BedrockProvider.fetch_models(
                    {
                        "aws_access_key_id": "x",
                        "aws_secret_access_key": "y",
                        "aws_region": "us-east-1",
                    }
                )
            self.assertIn("boto3 is not installed", str(ctx.exception))


class ComputeCostTest(SimpleTestCase):
    def test_cost_lookup_strips_geography_prefix(self):
        from zango.ai.providers.base import LLMUsage

        p = _make_provider(region="us-east-1")
        usage = LLMUsage(input_tokens=1_000_000, output_tokens=1_000_000)
        # Cost should be the same whether the model arg has the prefix or not.
        cost_prefixed = p.compute_cost(
            usage, "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        )
        cost_bare = p.compute_cost(
            usage, "anthropic.claude-3-5-sonnet-20241022-v2:0"
        )
        self.assertEqual(cost_prefixed, cost_bare)
        # 3 input + 15 output = 18 per Mtok
        self.assertEqual(cost_prefixed, 18.0)
