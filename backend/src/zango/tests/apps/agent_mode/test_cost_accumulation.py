"""Cost accumulation across conversational turns.

Regression: the SDK reports `total_cost_usd` as a float, the column
round-trips as Decimal, and `Decimal + float` raises. Turn 1 worked (None ->
0 + float) and turn 2 blew up — and because the failure was outside the
task's try/except, the conversation stayed stuck "thinking" forever.
"""

import unittest

from decimal import Decimal


def accumulate(existing, cost):
    """Mirrors the accumulation in agent_requirement_turn."""
    if cost is None:
        return existing
    return (existing or Decimal("0")) + Decimal(str(cost))


class CostAccumulationTests(unittest.TestCase):
    def test_first_turn_from_none(self):
        self.assertEqual(accumulate(None, 0.224572), Decimal("0.224572"))

    def test_second_turn_adds_float_to_decimal(self):
        # The exact case that raised TypeError in production.
        after_first = Decimal("0.224572")
        self.assertEqual(accumulate(after_first, 0.181), Decimal("0.405572"))

    def test_many_turns_stay_exact(self):
        total = None
        for _ in range(10):
            total = accumulate(total, 0.1)
        # Decimal(str(...)) avoids binary float drift; 0.1*10 would not be 1.0.
        self.assertEqual(total, Decimal("1.0"))

    def test_none_cost_is_ignored(self):
        self.assertEqual(accumulate(Decimal("1.5"), None), Decimal("1.5"))

    def test_naive_addition_would_still_raise(self):
        # Guards the assumption this fix rests on.
        with self.assertRaises(TypeError):
            Decimal("0.2") + 0.1


if __name__ == "__main__":
    unittest.main()
