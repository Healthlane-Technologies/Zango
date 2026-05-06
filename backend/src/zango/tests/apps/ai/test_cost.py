"""
Unit tests for zango.ai.cost — compute_cost and compute_anthropic_cost.

Pure arithmetic functions. No DB, no mocking required.
"""

from django.test import SimpleTestCase

from zango.ai.cost import compute_anthropic_cost, compute_cost
from zango.ai.providers.base import LLMUsage


STANDARD_RATES = {"input_cost_per_mtok": 3.0, "output_cost_per_mtok": 15.0}


class ComputeCostTest(SimpleTestCase):
    """Tests for the standard (non-Anthropic) cost computation."""

    def test_zero_tokens_returns_zero(self):
        usage = LLMUsage(input_tokens=0, output_tokens=0)
        self.assertEqual(compute_cost(usage, STANDARD_RATES), 0.0)

    def test_input_and_output_combined(self):
        # 1M input @ $3 + 1M output @ $15 = $18
        usage = LLMUsage(input_tokens=1_000_000, output_tokens=1_000_000)
        self.assertEqual(compute_cost(usage, STANDARD_RATES), 18.0)

    def test_input_only(self):
        # 1M input @ $3 = $3, output contributes nothing
        usage = LLMUsage(input_tokens=1_000_000, output_tokens=0)
        self.assertAlmostEqual(compute_cost(usage, STANDARD_RATES), 3.0, places=6)

    def test_output_only(self):
        # 1M output @ $15 = $15, input contributes nothing
        usage = LLMUsage(input_tokens=0, output_tokens=1_000_000)
        self.assertAlmostEqual(compute_cost(usage, STANDARD_RATES), 15.0, places=6)

    def test_result_rounded_to_6_decimal_places(self):
        # 1 token @ $3/M = $0.000003 — should not have noise beyond 6dp
        usage = LLMUsage(input_tokens=1, output_tokens=0)
        result = compute_cost(usage, STANDARD_RATES)
        self.assertEqual(result, round(result, 6))

    def test_missing_input_rate_defaults_to_zero(self):
        # Only output rate present — no KeyError, input contributes $0
        rates = {"output_cost_per_mtok": 15.0}
        usage = LLMUsage(input_tokens=1_000_000, output_tokens=1_000_000)
        self.assertAlmostEqual(compute_cost(usage, rates), 15.0, places=6)

    def test_missing_output_rate_defaults_to_zero(self):
        # Only input rate present — no KeyError, output contributes $0
        rates = {"input_cost_per_mtok": 3.0}
        usage = LLMUsage(input_tokens=1_000_000, output_tokens=1_000_000)
        self.assertAlmostEqual(compute_cost(usage, rates), 3.0, places=6)

    def test_empty_rates_returns_zero(self):
        usage = LLMUsage(input_tokens=1_000_000, output_tokens=1_000_000)
        self.assertEqual(compute_cost(usage, {}), 0.0)


class ComputeAnthropicCostTest(SimpleTestCase):
    """Tests for Anthropic-specific cost computation including prompt caching."""

    def test_zero_all_tokens_returns_zero(self):
        usage = LLMUsage(
            input_tokens=0, output_tokens=0,
            cache_creation_tokens=0, cache_read_tokens=0
        )
        self.assertEqual(compute_anthropic_cost(usage, STANDARD_RATES), 0.0)

    def test_standard_tokens_same_as_compute_cost(self):
        # With no cache tokens, Anthropic cost == standard cost
        usage = LLMUsage(input_tokens=1_000_000, output_tokens=1_000_000)
        self.assertAlmostEqual(
            compute_anthropic_cost(usage, STANDARD_RATES),
            compute_cost(usage, STANDARD_RATES),
            places=6
        )

    def test_cache_read_discount(self):
        # cache_read_tokens cost 0.1× input rate
        # 1M cache_read @ $3 × 0.1 = $0.30
        usage = LLMUsage(input_tokens=0, output_tokens=0, cache_read_tokens=1_000_000)
        self.assertAlmostEqual(
            compute_anthropic_cost(usage, STANDARD_RATES), 0.3, places=6
        )

    def test_cache_creation_surcharge(self):
        # cache_creation_tokens cost 1.25× input rate
        # 1M cache_create @ $3 × 1.25 = $3.75
        usage = LLMUsage(input_tokens=0, output_tokens=0, cache_creation_tokens=1_000_000)
        self.assertAlmostEqual(
            compute_anthropic_cost(usage, STANDARD_RATES), 3.75, places=6
        )

    def test_all_four_token_types_combined(self):
        # input: 1M @ $3 = $3
        # output: 1M @ $15 = $15
        # cache_create: 1M @ $3×1.25 = $3.75
        # cache_read: 1M @ $3×0.1 = $0.30
        # total = $22.05
        usage = LLMUsage(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            cache_creation_tokens=1_000_000,
            cache_read_tokens=1_000_000,
        )
        self.assertAlmostEqual(
            compute_anthropic_cost(usage, STANDARD_RATES), 22.05, places=6
        )

    def test_zero_cache_tokens_do_not_inflate_cost(self):
        # Explicitly passing zero cache tokens must not add anything
        usage = LLMUsage(
            input_tokens=500_000,
            output_tokens=500_000,
            cache_creation_tokens=0,
            cache_read_tokens=0,
        )
        expected = (0.5 * 3.0) + (0.5 * 15.0)  # $1.50 + $7.50 = $9.00
        self.assertAlmostEqual(
            compute_anthropic_cost(usage, STANDARD_RATES), expected, places=6
        )

    def test_result_rounded_to_6_decimal_places(self):
        usage = LLMUsage(input_tokens=1, output_tokens=1,
                         cache_creation_tokens=1, cache_read_tokens=1)
        result = compute_anthropic_cost(usage, STANDARD_RATES)
        self.assertEqual(result, round(result, 6))
