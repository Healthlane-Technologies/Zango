"""
Unit tests for ProviderClient (zango.ai.client).

The raw provider and AppLLMInvocation are mocked. Only ProviderClient's own
logic — model resolution, cost attachment, invocation logging, error mapping,
message serialization — is exercised.
"""

from unittest.mock import MagicMock, call, patch

from django.test import SimpleTestCase

from zango.ai.client import ProviderClient
from zango.ai.exceptions import (
    BudgetExceeded,
    LLMAPIError,
    LLMTimeoutError,
    ModelNotAvailable,
    RateLimitExceeded,
)
from zango.ai.providers.base import LLMMessage, LLMResponse, LLMToolDef, LLMUsage

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_raw_response(content="Hello", cost=0.0):
    return LLMResponse(
        content=content,
        tool_calls=[],
        stop_reason="end_turn",
        usage=LLMUsage(input_tokens=100, output_tokens=50),
        model="claude-sonnet-4-20250514",
        raw_response=None,
        latency_ms=100,
        cost_usd=cost,
    )


def _make_app_provider(slug="anthropic", default_model="claude-sonnet-4-20250514"):
    p = MagicMock()
    p.name = "test-provider"
    p.provider_slug = slug
    p.default_model = default_model
    # No enabled_models restrictions by default
    p.enabled_models.exists.return_value = False
    raw = MagicMock()
    raw.complete.return_value = _make_raw_response()
    raw.compute_cost.return_value = 0.005
    p.get_client.return_value = raw
    return p


# Patch at the import site used inside client.py:
#   from zango.apps.ai.models import AppLLMInvocation
_INV_PATH = "zango.apps.ai.models.AppLLMInvocation"


# ─── 5a. Model resolution and access control ─────────────────────────────────

class ModelResolutionTest(SimpleTestCase):

    @patch(_INV_PATH)
    def test_none_model_uses_provider_default(self, mock_inv):
        mock_inv.objects.create.return_value = MagicMock(pk=1)
        app_provider = _make_app_provider()

        ProviderClient(app_provider).complete(
            messages=[LLMMessage(role="user", content="hi")],
            model=None,
        )

        raw = app_provider.get_client.return_value
        self.assertEqual(raw.complete.call_args.kwargs["model"], "claude-sonnet-4-20250514")

    @patch(_INV_PATH)
    def test_explicit_model_passed_through(self, mock_inv):
        mock_inv.objects.create.return_value = MagicMock(pk=1)
        app_provider = _make_app_provider()

        ProviderClient(app_provider).complete(
            messages=[LLMMessage(role="user", content="hi")],
            model="gpt-4o",
        )

        raw = app_provider.get_client.return_value
        self.assertEqual(raw.complete.call_args.kwargs["model"], "gpt-4o")

    def test_no_enabled_models_records_any_model_allowed(self):
        app_provider = _make_app_provider()
        app_provider.enabled_models.exists.return_value = False

        with patch(_INV_PATH) as mock_inv:
            mock_inv.objects.create.return_value = MagicMock(pk=1)
            # Should not raise ModelNotAvailable
            ProviderClient(app_provider).complete(
                messages=[LLMMessage(role="user", content="hi")],
                model="any-model",
            )

    def test_model_in_enabled_list_allowed(self):
        app_provider = _make_app_provider()
        app_provider.enabled_models.exists.return_value = True
        app_provider.enabled_models.filter.return_value.exists.return_value = True

        with patch(_INV_PATH) as mock_inv:
            mock_inv.objects.create.return_value = MagicMock(pk=1)
            ProviderClient(app_provider).complete(
                messages=[LLMMessage(role="user", content="hi")],
                model="claude-sonnet-4-20250514",
            )  # no exception

    def test_model_not_in_enabled_list_raises_before_api_call(self):
        app_provider = _make_app_provider()
        app_provider.enabled_models.exists.return_value = True
        app_provider.enabled_models.filter.return_value.exists.return_value = False

        with self.assertRaises(ModelNotAvailable):
            ProviderClient(app_provider).complete(
                messages=[LLMMessage(role="user", content="hi")],
                model="gpt-4o",
            )

        app_provider.get_client.return_value.complete.assert_not_called()


# ─── 5b. Success path ─────────────────────────────────────────────────────────

class SuccessPathTest(SimpleTestCase):

    @patch(_INV_PATH)
    def test_cost_attached_from_compute_cost(self, mock_inv):
        mock_inv.objects.create.return_value = MagicMock(pk=1)
        app_provider = _make_app_provider()
        app_provider.get_client.return_value.compute_cost.return_value = 0.007

        response = ProviderClient(app_provider).complete(
            messages=[LLMMessage(role="user", content="hi")]
        )

        self.assertAlmostEqual(response.cost_usd, 0.007)

    @patch(_INV_PATH)
    def test_invocation_id_attached_from_created_pk(self, mock_inv):
        mock_inv_instance = MagicMock()
        mock_inv_instance.pk = 99
        mock_inv.objects.create.return_value = mock_inv_instance

        response = ProviderClient(_make_app_provider()).complete(
            messages=[LLMMessage(role="user", content="hi")]
        )

        self.assertEqual(response.invocation_id, 99)

    @patch(_INV_PATH)
    def test_record_usage_called_on_provider(self, mock_inv):
        mock_inv.objects.create.return_value = MagicMock(pk=1)
        app_provider = _make_app_provider()

        ProviderClient(app_provider).complete(
            messages=[LLMMessage(role="user", content="hi")]
        )

        app_provider.record_usage.assert_called_once()

    @patch(_INV_PATH)
    def test_invocation_log_failure_does_not_crash_caller(self, mock_inv):
        mock_inv.objects.create.side_effect = Exception("DB write failed")
        app_provider = _make_app_provider()

        # Should not raise — invocation logging is best-effort
        response = ProviderClient(app_provider).complete(
            messages=[LLMMessage(role="user", content="hi")]
        )

        self.assertEqual(response.content, "Hello")
        self.assertIsNone(response.invocation_id)


# ─── 5c. Error paths and status mapping ──────────────────────────────────────

class ErrorPathTest(SimpleTestCase):

    def _assert_error_status(self, exc_instance, expected_status):
        app_provider = _make_app_provider()
        app_provider.get_client.return_value.complete.side_effect = exc_instance

        with patch(_INV_PATH) as mock_inv:
            mock_inv.objects.create.return_value = MagicMock(pk=1)
            with self.assertRaises(type(exc_instance)):
                ProviderClient(app_provider).complete(
                    messages=[LLMMessage(role="user", content="hi")]
                )

            create_kwargs = mock_inv.objects.create.call_args.kwargs
            self.assertEqual(create_kwargs["status"], expected_status)

    def test_rate_limit_maps_to_rate_limited_status(self):
        self._assert_error_status(
            RateLimitExceeded("too many requests"), "rate_limited"
        )

    def test_timeout_maps_to_timeout_status(self):
        self._assert_error_status(LLMTimeoutError("timed out"), "timeout")

    def test_budget_exceeded_maps_to_budget_exceeded_status(self):
        self._assert_error_status(
            BudgetExceeded("test-provider", 100), "budget_exceeded"
        )

    def test_generic_exception_wrapped_in_llm_api_error(self):
        app_provider = _make_app_provider()
        app_provider.get_client.return_value.complete.side_effect = RuntimeError("boom")

        with patch(_INV_PATH) as mock_inv:
            mock_inv.objects.create.return_value = MagicMock(pk=1)
            with self.assertRaises(LLMAPIError):
                ProviderClient(app_provider).complete(
                    messages=[LLMMessage(role="user", content="hi")]
                )

    def test_error_path_still_writes_invocation_log(self):
        app_provider = _make_app_provider()
        app_provider.get_client.return_value.complete.side_effect = RateLimitExceeded("x")

        with patch(_INV_PATH) as mock_inv:
            mock_inv.objects.create.return_value = MagicMock(pk=1)
            with self.assertRaises(RateLimitExceeded):
                ProviderClient(app_provider).complete(
                    messages=[LLMMessage(role="user", content="hi")]
                )

            mock_inv.objects.create.assert_called_once()

    def test_error_path_re_raises_to_caller(self):
        app_provider = _make_app_provider()
        app_provider.get_client.return_value.complete.side_effect = BudgetExceeded("p", 50)

        with patch(_INV_PATH) as mock_inv:
            mock_inv.objects.create.return_value = MagicMock(pk=1)
            with self.assertRaises(BudgetExceeded):
                ProviderClient(app_provider).complete(
                    messages=[LLMMessage(role="user", content="hi")]
                )


# ─── 5d. Message + tool serialization (for logging) ──────────────────────────

class SerializationTest(SimpleTestCase):

    def _client(self):
        return ProviderClient(_make_app_provider())

    def test_llm_message_serialized_to_dict(self):
        client = self._client()
        msg = LLMMessage(role="user", content="hello")
        result = client._serialize_messages([msg])
        self.assertEqual(result, [{"role": "user", "content": "hello"}])

    def test_llm_message_with_tool_calls_included(self):
        client = self._client()
        msg = LLMMessage(role="assistant", content=None,
                         tool_calls=[{"id": "tc1", "name": "my_tool"}])
        result = client._serialize_messages([msg])
        self.assertIn("tool_calls", result[0])

    def test_llm_message_with_tool_call_id_included(self):
        client = self._client()
        msg = LLMMessage(role="tool", content="result", tool_call_id="tc1")
        result = client._serialize_messages([msg])
        self.assertIn("tool_call_id", result[0])

    def test_llm_tool_def_serialized_to_dict(self):
        client = self._client()
        tool = LLMToolDef(
            name="get_scores",
            description="Get scores",
            input_schema={"type": "object", "properties": {}}
        )
        result = client._serialize_tools([tool])
        self.assertEqual(result[0]["name"], "get_scores")
        self.assertEqual(result[0]["description"], "Get scores")
        self.assertIn("input_schema", result[0])

    def test_tools_none_serialized_as_none(self):
        client = self._client()
        self.assertIsNone(client._serialize_tools(None))

    def test_tools_empty_list_serialized_as_none(self):
        client = self._client()
        self.assertIsNone(client._serialize_tools([]))
