"""The requirement conversation is with a non-technical business user.

Three things are easy to break here and none of them fails loudly:

1. The analyst drifting back into developer vocabulary. The skill is the only
   thing holding the line, so the ban list is asserted rather than trusted.
2. The spec template and `_roles_from_text` drifting apart. Roles are
   pre-created from the spec before a build; if the heading stops matching, or
   role names stop being bold list items, role creation silently yields
   nothing and the built app has no working roles.
3. The template offer going missing. A user who is never told that the thing
   they asked for already exists pays for a from-scratch build of software
   Zelthy maintains — and nothing anywhere reports that it did not happen.
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


class TemplateOfferTests(unittest.TestCase):
    """The analyst must offer a ready-made template when one fits.

    This is the most expensive thing in the skill to lose: the failure mode is
    an ordinary-looking interview that quietly rebuilds an existing product.
    """

    def setUp(self):
        self.body = SKILL.read_text()

    def test_the_offer_is_made_on_the_first_reply(self):
        self.assertIn("is there a template for this?", self.body.lower())
        self.assertRegex(self.body, r"[Ff]irst reply")

    def test_the_choice_is_declared_in_a_fence_the_platform_reads(self):
        from zango.apps.agent_mode.requirements import extract_template

        # The block in the skill is the one the model copies, so it has to
        # survive the parser that consumes it.
        match = re.search(r"```zango-template\n(.*?)```", self.body, re.S)
        self.assertIsNotNone(match, "the skill no longer shows a zango-template fence")
        self.assertEqual(
            extract_template(f"```zango-template\n{match.group(1)}```"), "psp"
        )

    def test_the_pack_is_not_read_before_the_user_agrees(self):
        # Reading a template the user then declines is pure waste, and the
        # digest in the run context exists precisely so it is not needed.
        self.assertIn("Read nothing until they say yes", self.body)

    def test_the_offer_is_made_once(self):
        self.assertIn("Offer once", self.body)

    def test_a_template_that_does_not_fit_is_not_offered(self):
        self.assertIn("Do not offer a template that does not fit", self.body)

    def test_the_draft_fence_is_distinguished_from_the_finished_one(self):
        self.assertIn("zango-spec-draft", self.body)
        self.assertIn("Never use it for a draft", self.body)


class TemplateCatalogueInPromptTests(unittest.TestCase):
    """The offer is only possible if the first turn is told what exists."""

    def test_the_opening_prompt_carries_the_catalogue(self):
        from zango.apps.agent_mode.app_templates import catalogue_digest
        from zango.apps.agent_mode.requirements import compose_analyst_prompt

        class Requirement:
            session_id = ""

        class Ctx:
            app_name = "clinic"
            workspace_path = "/w"
            packages = []
            modules = []
            roles = []

        text = compose_analyst_prompt(Requirement(), Ctx(), "a patient support program")
        self.assertIn("Templates available for this ask", text)
        self.assertIn("slug: psp", text)
        self.assertIn("zango-template", text)
        self.assertIn(catalogue_digest(), text)

    def test_a_resumed_turn_is_just_the_reply(self):
        # The session already holds the catalogue; repeating it every turn
        # would pay for it again on every single answer.
        from zango.apps.agent_mode.requirements import compose_analyst_prompt

        class Requirement:
            session_id = "abc123"

        self.assertEqual(
            compose_analyst_prompt(Requirement(), None, "  yes please  "), "yes please"
        )


class AnalystTemplateSystemPromptTests(unittest.TestCase):
    """The skill can be ignored; the system prompt append is the harder layer."""

    def test_append_tells_the_agent_to_offer_and_declare(self):
        import inspect

        from zango.apps.agent_mode import requirements

        source = inspect.getsource(requirements.build_analyst_options)
        self.assertIn("zango-template", source)
        self.assertIn("zango-spec-draft", source)
