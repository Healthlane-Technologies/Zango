"""Questions come back as options the user clicks, not prose they type.

The payload is model output rendered straight into the panel, so the parser is
the only thing standing between a bad turn and a broken chat. Everything here
pins the same rule: a malformed block degrades to "no options offered" — the
chat box is always still there — and never raises or emits something the panel
cannot render.
"""

import json
import unittest

from pathlib import Path

import zango

from zango.apps.agent_mode.requirements import (
    MAX_OPTIONS,
    MAX_QUESTIONS,
    extract_questions,
    extract_spec,
    strip_fences,
)


SKILL = (
    Path(zango.__file__).resolve().parent
    / "apps/agent_mode/skill_plugin/skills/zango-requirements-analyst/SKILL.md"
)


def fence(payload) -> str:
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return f"A few questions:\n\n```zango-questions\n{body}\n```"


VALID = [
    {
        "id": "stages",
        "question": "Does a tender move through stages?",
        "type": "single",
        "options": ["New → Bidding → Won or Lost", "Just a list"],
        "selected": ["New → Bidding → Won or Lost"],
        "allow_other": True,
    }
]


class ExtractTests(unittest.TestCase):
    def test_reads_a_well_formed_block(self):
        questions = extract_questions(fence(VALID))
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["id"], "stages")
        self.assertEqual(questions[0]["type"], "single")
        self.assertEqual(questions[0]["selected"], ["New → Bidding → Won or Lost"])

    def test_no_fence_is_no_questions(self):
        self.assertEqual(extract_questions("1. Who approves a bid?"), [])
        self.assertEqual(extract_questions(""), [])
        self.assertEqual(extract_questions(None), [])

    def test_malformed_json_degrades_rather_than_raising(self):
        self.assertEqual(extract_questions(fence("{not json")), [])
        self.assertEqual(extract_questions(fence('{"question": "x"}')), [])

    def test_the_last_block_wins(self):
        # Same rule extract_spec follows: a revised block supersedes.
        text = fence(VALID) + "\n" + fence(
            [{"question": "Later?", "options": ["Yes", "No"]}]
        )
        self.assertEqual(extract_questions(text)[0]["question"], "Later?")


class NormalisationTests(unittest.TestCase):
    def test_a_question_needs_at_least_two_options(self):
        # One option is not a choice — there would be nothing to decide.
        self.assertEqual(
            extract_questions(fence([{"question": "Stages?", "options": ["Yes"]}])), []
        )

    def test_a_question_without_text_is_dropped(self):
        self.assertEqual(
            extract_questions(fence([{"question": "  ", "options": ["a", "b"]}])), []
        )

    def test_one_bad_question_does_not_lose_the_good_ones(self):
        payload = [
            {"question": "Stages?", "options": ["Yes", "No"]},
            "not an object",
            {"question": "Approval?", "options": ["Manager", "Nobody"]},
        ]
        self.assertEqual(len(extract_questions(fence(payload))), 2)

    def test_unknown_type_falls_back_to_single_choice(self):
        payload = [{"question": "Q?", "type": "dropdown", "options": ["a", "b"]}]
        self.assertEqual(extract_questions(fence(payload))[0]["type"], "single")

    def test_single_choice_keeps_only_one_default(self):
        payload = [
            {
                "question": "Q?",
                "type": "single",
                "options": ["a", "b", "c"],
                "selected": ["a", "b"],
            }
        ]
        self.assertEqual(extract_questions(fence(payload))[0]["selected"], ["a"])

    def test_a_default_that_is_not_an_option_is_dropped(self):
        # Otherwise the panel would render a tick against nothing.
        payload = [{"question": "Q?", "options": ["a", "b"], "selected": ["z"]}]
        self.assertEqual(extract_questions(fence(payload))[0]["selected"], [])

    def test_duplicate_options_are_collapsed(self):
        payload = [{"question": "Q?", "options": ["a", "a", "b"]}]
        self.assertEqual(extract_questions(fence(payload))[0]["options"], ["a", "b"])

    def test_counts_are_capped(self):
        payload = [
            {"question": f"Q{i}?", "options": [f"o{j}" for j in range(20)]}
            for i in range(20)
        ]
        questions = extract_questions(fence(payload))
        self.assertEqual(len(questions), MAX_QUESTIONS)
        self.assertEqual(len(questions[0]["options"]), MAX_OPTIONS)

    def test_allow_other_defaults_to_true(self):
        payload = [{"question": "Q?", "options": ["a", "b"]}]
        self.assertTrue(extract_questions(fence(payload))[0]["allow_other"])

    def test_a_missing_id_is_generated(self):
        payload = [{"question": "Q?", "options": ["a", "b"]}]
        self.assertEqual(extract_questions(fence(payload))[0]["id"], "q1")

    def test_every_question_has_the_keys_the_panel_reads(self):
        for question in extract_questions(fence(VALID)):
            for key in ("id", "question", "type", "options", "selected", "allow_other"):
                self.assertIn(key, question)


class StripFencesTests(unittest.TestCase):
    """The blocks render as their own UI; repeating them as chat text is noise."""

    def test_removes_the_questions_block(self):
        chat = strip_fences(fence(VALID))
        self.assertEqual(chat, "A few questions:")
        self.assertNotIn("zango-questions", chat)

    def test_still_removes_the_spec_block(self):
        text = "Ready for review.\n\n```zango-spec\n## App\n```"
        self.assertEqual(strip_fences(text), "Ready for review.")

    def test_removes_both_in_one_reply(self):
        text = fence(VALID) + "\n\n```zango-spec\n## App\n```"
        chat = strip_fences(text)
        self.assertNotIn("zango-questions", chat)
        self.assertNotIn("zango-spec", chat)

    def test_leaves_an_ordinary_reply_alone(self):
        self.assertEqual(strip_fences("Just a sentence."), "Just a sentence.")

    def test_a_questions_block_is_not_mistaken_for_a_spec(self):
        self.assertEqual(extract_spec(fence(VALID)), "")


class SkillContractTests(unittest.TestCase):
    """The parser and the skill are two halves of one contract."""

    def test_the_skill_documents_the_fence_the_parser_reads(self):
        body = SKILL.read_text()
        self.assertIn("```zango-questions", body)

    def test_the_skill_example_parses(self):
        body = SKILL.read_text()
        questions = extract_questions(body)
        self.assertTrue(questions, "the skill's own example must parse")
        for question in questions:
            self.assertGreaterEqual(len(question["options"]), 2)
            # A default is what makes a turn answerable in one click.
            self.assertTrue(question["selected"], question["question"])


if __name__ == "__main__":
    unittest.main()
