"""
Unit tests for zango.ai.cost — compute_anthropic_cost.

Pure arithmetic functions. No DB, no mocking required.
"""

from django.test import SimpleTestCase

from zango.ai.cost import compute_anthropic_cost
from zango.ai.providers.base import LLMUsage


STANDARD_RATES = {"input_cost_per_mtok": 3.0, "output_cost_per_mtok": 15.0}


class ComputeAnthropicCostTest(SimpleTestCase):
    """Tests for Anthropic-specific cost computation including prompt caching."""

    def test_zero_all_tokens_returns_zero(self):
        usage = LLMUsage(
            input_tokens=0, output_tokens=0,
            cache_creation_tokens=0, cache_read_tokens=0
        )
        self.assertEqual(compute_anthropic_cost(usage, STANDARD_RATES), 0.0)

    def test_standard_tokens_no_cache(self):
        # With no cache tokens: 1M input @ $3 + 1M output @ $15 = $18
        usage = LLMUsage(input_tokens=1_000_000, output_tokens=1_000_000)
        self.assertAlmostEqual(
            compute_anthropic_cost(usage, STANDARD_RATES),
            18.0,
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
