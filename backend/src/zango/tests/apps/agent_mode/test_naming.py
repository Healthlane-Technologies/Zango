"""The agent names the app, and that name becomes a Postgres schema.

Nothing downstream re-validates it: ``TenantModel.create`` raises on a bad
name and the launch is already in flight by then, with the user watching a
spinner. So every path out of the naming step — model reply, malformed reply,
no reply at all — has to produce a name that ``SQL_IDENTIFIER_RE`` accepts.
"""

import re
import unittest

from zango.apps.agent_mode.naming import (
    MAX_NAME_LEN,
    MIN_NAME_LEN,
    _parse,
    label_from_name,
    sanitize_name,
    slug_from_prompt,
)
from zango.apps.shared.tenancy.models import (
    SQL_IDENTIFIER_RE,
    SQL_SCHEMA_NAME_RESERVED_RE,
)


def _is_legal(name: str) -> bool:
    return bool(SQL_IDENTIFIER_RE.match(name)) and not SQL_SCHEMA_NAME_RESERVED_RE.match(
        name
    )


class SanitizeTests(unittest.TestCase):
    def test_keeps_a_good_name(self):
        self.assertEqual(sanitize_name("clinic_visits"), "clinic_visits")

    def test_normalises_case_and_separators(self):
        self.assertEqual(sanitize_name("Clinic Visits"), "clinic_visits")
        self.assertEqual(sanitize_name("clinic-visits"), "clinic_visits")
        self.assertEqual(sanitize_name("clinic.visits"), "clinic_visits")

    def test_strips_characters_a_schema_name_cannot_hold(self):
        self.assertEqual(sanitize_name("  Loan Approvals!!  "), "loan_approvals")

    def test_rejects_a_leading_digit_rather_than_keeping_it(self):
        # "2fast" would be a syntax error as a schema name.
        self.assertEqual(sanitize_name("2fast"), "")

    def test_rejects_names_below_the_minimum(self):
        self.assertEqual(sanitize_name("abc"), "")
        self.assertEqual(sanitize_name("abcde"), "abcde")

    def test_rejects_reserved_schema_names(self):
        self.assertEqual(sanitize_name("public"), "")
        self.assertEqual(sanitize_name("PostgreS"), "")

    def test_truncates_to_the_column_width(self):
        name = sanitize_name("a" * 80)
        self.assertEqual(len(name), MAX_NAME_LEN)

    def test_every_accepted_name_is_a_legal_tenant_name(self):
        for raw in (
            "clinic_visits",
            "Clinic Visits",
            "CRM-app",
            "field service jobs",
            "a" * 80,
            "loan__approvals__2026",
        ):
            name = sanitize_name(raw)
            if name:
                self.assertTrue(_is_legal(name), f"{raw!r} -> {name!r}")


class FallbackSlugTests(unittest.TestCase):
    """No key, no `anthropic`, a refusal — an app still has to get created."""

    def test_picks_the_words_that_carry_meaning(self):
        self.assertEqual(
            slug_from_prompt("I want to track patient appointments for my clinic"),
            "patient_appointments_clinic",
        )

    def test_drops_filler_words(self):
        self.assertEqual(
            slug_from_prompt("a simple app to manage loan approvals"),
            "manage_loan_approvals",
        )

    def test_always_returns_something_legal(self):
        for prompt in ("", "build me an app", "CRM", "!!!", "a " * 200):
            name = slug_from_prompt(prompt)
            self.assertTrue(_is_legal(name), f"{prompt[:20]!r} -> {name!r}")
            self.assertGreaterEqual(len(name), MIN_NAME_LEN)

    def test_never_exceeds_the_column(self):
        long_ask = "reconciliation dashboard for distributor settlement disputes"
        self.assertLessEqual(len(slug_from_prompt(long_ask)), MAX_NAME_LEN)


class LabelTests(unittest.TestCase):
    def test_reads_back_as_words(self):
        self.assertEqual(label_from_name("patient_appointments"), "Patient Appointments")

    def test_empty_name_is_not_an_error(self):
        self.assertEqual(label_from_name(""), "")


class ReplyParsingTests(unittest.TestCase):
    """The model is asked for bare JSON; it does not always comply."""

    def test_reads_a_plain_object(self):
        self.assertEqual(_parse('{"name": "clinic_visits"}')["name"], "clinic_visits")

    def test_reads_through_a_code_fence(self):
        text = 'Here you go:\n```json\n{"name": "clinic_visits"}\n```'
        self.assertEqual(_parse(text)["name"], "clinic_visits")

    def test_malformed_json_is_empty_not_an_exception(self):
        self.assertEqual(_parse("{not json}"), {})
        self.assertEqual(_parse(""), {})
        self.assertEqual(_parse("no object here"), {})

    def test_a_json_list_is_not_accepted_as_an_identity(self):
        self.assertEqual(_parse("[1, 2, 3]"), {})


class ContractTests(unittest.TestCase):
    def test_bounds_match_the_tenant_name_rule(self):
        # The rule lives in shared.tenancy; naming.py restates the bounds, so
        # a change there must not quietly invalidate every name chosen here.
        self.assertTrue(re.match(r"^\^\[_a-zA-Z\]", SQL_IDENTIFIER_RE.pattern))
        self.assertTrue(_is_legal("a" * MIN_NAME_LEN))
        self.assertTrue(_is_legal("a" * MAX_NAME_LEN))
        self.assertFalse(_is_legal("a" * (MIN_NAME_LEN - 1)))


if __name__ == "__main__":
    unittest.main()
