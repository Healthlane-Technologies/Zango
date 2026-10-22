"""Run totals across App Studio fix rounds.

Regression: a fix round resumes the build's session, and the resumed session's
ResultMessage reports cost, tokens and API time as running totals for the whole
session. `_merge_state` added them to the build's figures, so every round counted
the build again: a build whose session ended at $6.05 was recorded as $17.44.
The figures below are that run's three ResultMessages.
"""

import unittest


def _result(cost, turns, output_tokens, cache_read, api_ms, tools=None):
    return {
        "total_cost_usd": cost,
        "num_turns": turns,
        "input_tokens": 120,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read,
        "cache_creation_tokens": 350_000,
        "duration_api_ms": api_ms,
        "model_usage": {"claude-sonnet-5-5": {"costUSD": cost}},
        "tool_use_counts": tools or {},
    }


class FixRoundTotalsTests(unittest.TestCase):
    def setUp(self):
        from zango.apps.agent_mode.tasks import _merge_state

        self.merge = _merge_state
        self.state = _result(5.4971, 117, 125_354, 14_180_164, 1_000_000, {"Write": 45, "Bash": 40})
        self.state["session_id"] = "sess-1"

    def merge_rounds(self):
        self.merge(self.state, _result(5.8904, 7, 126_437, 15_959_426, 1_040_000, {"Bash": 2}))
        self.merge(self.state, _result(6.0489, 3, 127_379, 16_676_817, 1_060_000, {"Edit": 2}))

    def test_cost_is_the_sessions_final_total(self):
        self.merge_rounds()
        self.assertAlmostEqual(self.state["total_cost_usd"], 6.0489)

    def test_tokens_and_api_time_are_not_counted_twice(self):
        self.merge_rounds()
        self.assertEqual(self.state["output_tokens"], 127_379)
        self.assertEqual(self.state["cache_read_tokens"], 16_676_817)
        self.assertEqual(self.state["duration_api_ms"], 1_060_000)

    def test_turns_and_tool_counts_add_up(self):
        # Both are counted per query, so each round adds its own.
        self.merge_rounds()
        self.assertEqual(self.state["num_turns"], 127)
        self.assertEqual(self.state["tool_use_counts"], {"Write": 45, "Bash": 42, "Edit": 2})

    def test_model_usage_follows_the_latest_round(self):
        self.merge_rounds()
        self.assertEqual(self.state["model_usage"]["claude-sonnet-5-5"]["costUSD"], 6.0489)

    def test_a_round_without_a_result_keeps_the_totals(self):
        # The stream died before its ResultMessage: nothing to fold in.
        self.merge(self.state, {"tool_use_counts": {"Read": 1}})
        self.assertAlmostEqual(self.state["total_cost_usd"], 5.4971)
        self.assertEqual(self.state["num_turns"], 117)
        self.assertEqual(self.state["session_id"], "sess-1")

    def test_first_session_is_kept(self):
        self.merge(self.state, {"session_id": "sess-2"})
        self.assertEqual(self.state["session_id"], "sess-1")


if __name__ == "__main__":
    unittest.main()
