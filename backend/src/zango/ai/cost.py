"""
Cost computation utilities for LLM invocations.
"""

from zango.ai.providers.base import LLMUsage


def compute_anthropic_cost(usage: LLMUsage, model_info: dict) -> float:
    """
    Compute cost for Anthropic models, handling prompt caching pricing.

    Anthropic prompt caching:
    - cache_creation_tokens: 1.25x input price
    - cache_read_tokens: 0.1x input price
    """
    input_rate = model_info.get("input_cost_per_mtok", 0)
    output_rate = model_info.get("output_cost_per_mtok", 0)

    input_cost = (usage.input_tokens / 1_000_000) * input_rate
    output_cost = (usage.output_tokens / 1_000_000) * output_rate
    cache_creation_cost = (usage.cache_creation_tokens / 1_000_000) * input_rate * 1.25
    cache_read_cost = (usage.cache_read_tokens / 1_000_000) * input_rate * 0.1

    return round(input_cost + output_cost + cache_creation_cost + cache_read_cost, 6)
