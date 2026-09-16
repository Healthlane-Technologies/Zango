"""The requirement conversation is with a non-technical business user.

Two things are easy to break here and neither fails loudly:

1. The analyst drifting back into developer vocabulary. The skill is the only
   thing holding the line, so the ban list is asserted rather than trusted.
2. The spec template and `_roles_from_text` drifting apart. Roles are
   pre-created from the spec before a build; if the heading stops matching, or
   role names stop being bold list items, role creation silently yields
   nothing and the built app has no working roles.
"""

import re
import unittest

from pathlib import Path

import zango


SKILL = (
    Path(zango.__file__).resolve().parent
    / "apps/agent_mode/skill_plugin/skills/zango-requirements-analyst/SKILL.md"
)

# Words the analyst must never say to the user. Checked against the parts of
# the skill that model its speech, not the internal-reasoning section.
BANNED_IN_SPEECH = [
    "CRUD",
    "DynamicModelBase",
    "ZForeignKey",
    "ManyToManyField",
    "CrudHandler",
    "policies.json",
    "async task",
]


def _spec_template() -> str:
    body = SKILL.read_text()
    match = re.search(r"```zango-spec\n(.*?)```", body, re.S)
    assert match, "the skill no longer contains a zango-spec template"
    return match.group(1)


class SpecTemplateContractTests(unittest.TestCase):
    """The template is the model the analyst copies, so it must satisfy the
    parser that consumes real specs."""

    def test_roles_are_still_parseable_from_the_template(self):
        from zango.apps.agent_mode.tasks import _roles_from_text

        roles = _roles_from_text(_spec_template())
        self.assertEqual(
            roles,
            ["Receptionist", "Clinician"],
            "role pre-creation reads bold list items under a heading matching "
            "/roles?/ — the template no longer satisfies it",
        )

    def test_roles_heading_keeps_the_keyword(self):
        headings = re.findall(r"^### (.+)$", _spec_template(), re.M)
        self.assertTrue(
            any(re.search(r"roles?\b", h, re.I) for h in headings),
            f"no heading matches /roles?/ — headings are {headings}",
        )

    def test_template_is_in_plain_language(self):
        template = _spec_template()
        for word in ("Entities", "Lifecycles", "Background work", "FK ", "workflow package"):
            self.assertNotIn(
                word,
                template,
                f"the user reads and approves this spec; {word!r} is developer "
                f"vocabulary",
            )


class AnalystToneTests(unittest.TestCase):
    def test_skill_names_its_audience(self):
        body = SKILL.read_text().lower()
        self.assertIn("business user", body)
        self.assertIn("not a developer", body)

    def test_skill_caps_question_count_and_length(self):
        body = SKILL.read_text()
        self.assertIn("Three to four", body)
        self.assertRegex(body, r"[Oo]ne or two lines")

    def test_skill_carries_an_explicit_ban_list(self):
        body = SKILL.read_text()
        self.assertIn("Never use these words with the user", body)
        # The ban list must actually enumerate the offenders.
        for word in ("entity", "schema", "React", "CRUD", "MVP"):
            self.assertIn(word, body)

    def test_user_facing_examples_avoid_jargon(self):
        """Every quoted example question must be plain."""
        body = SKILL.read_text()
        examples = re.findall(r'\*"([^"]{10,400})"\*', body)
        self.assertGreaterEqual(len(examples), 4, "expected quoted examples")
        for example in examples:
            for word in BANNED_IN_SPEECH:
                self.assertNotIn(
                    word.lower(),
                    example.lower(),
                    f"example question uses {word!r}: {example!r}",
                )


class AnalystSystemPromptTests(unittest.TestCase):
    """The skill can be ignored; the system prompt append is the harder layer."""

    def test_append_states_the_audience_and_the_limits(self):
        import inspect

        from zango.apps.agent_mode import requirements

        source = inspect.getsource(requirements.build_analyst_options)
        self.assertIn("NON-TECHNICAL BUSINESS USER", source)
        self.assertIn("three or four", source)
        self.assertIn("Never use technical vocabulary", source)
