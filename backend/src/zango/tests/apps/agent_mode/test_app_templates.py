"""The app template catalogue, as Agent Mode sees it.

A template that fails to load does not raise anywhere — it is simply never
offered, and the user pays for a from-scratch build of software Zelthy already
maintains. These assertions are the only thing that notices.

Templates live in the database; the bundled PSP pack is seeded by migrate, so
the test database has it.
"""

import unittest

from pathlib import Path

from zango.apps.agent_mode.app_templates import (
    catalogue_digest,
    get_template,
    load_templates,
    spec_format_for,
    templates_dir,
)
from zango.apps.shared.app_templates.seed import PACKS_DIR


# What a template's interview needs on disk before the analyst can run it.
REQUIRED_FILES = ("interview", "schema")


class CatalogueTests(unittest.TestCase):
    def test_the_psp_pack_ships_with_zango(self):
        self.assertTrue((PACKS_DIR / "psp" / "template.json").is_file())

    def test_packs_are_materialised_where_the_analyst_can_read_them(self):
        psp = get_template("psp")
        self.assertIsNotNone(psp, "the PSP template was not seeded")
        self.assertTrue(Path(psp.path).is_relative_to(Path(templates_dir())))

    def test_psp_template_loads(self):
        psp = get_template("psp")
        self.assertIsNotNone(psp, "the PSP template did not load")
        self.assertEqual(psp.name, "Patient Support Program")
        self.assertEqual(psp.spec_format, "yaml")
        self.assertTrue(psp.is_yaml)

    def test_every_pack_has_what_the_interview_needs(self):
        templates = load_templates()
        self.assertTrue(templates, "no templates loaded at all")
        for slug, template in templates.items():
            for key in REQUIRED_FILES:
                path = template.file_path(key)
                self.assertTrue(path, f"{slug} declares no {key}")
                self.assertTrue(Path(path).is_file(), f"{slug}: missing {path}")

    def test_every_template_build_skill_is_on_disk(self):
        # A template without its own build skill is built with the platform's
        # generic one (prompt.QUALIFIED_SKILL).
        for slug, template in load_templates().items():
            if not template.build_skill_name:
                continue
            skill = (
                Path(template.build_plugin_dir)
                / "skills"
                / template.build_skill_name
                / "SKILL.md"
            )
            self.assertTrue(skill.is_file(), f"{slug}: missing {skill}")

    def test_unknown_slug_is_not_a_template(self):
        self.assertIsNone(get_template("no-such-template"))
        self.assertIsNone(get_template(""))
        self.assertIsNone(get_template(None))
        self.assertEqual(spec_format_for("no-such-template"), "markdown")
        self.assertEqual(spec_format_for("psp"), "yaml")

    def test_lookup_is_forgiving_about_case_and_padding(self):
        self.assertIsNotNone(get_template("  PSP "))


class DigestTests(unittest.TestCase):
    """What the analyst is told before it decides whether to offer."""

    def setUp(self):
        self.digest = catalogue_digest()

    def test_names_the_template_and_its_slug(self):
        self.assertIn("Patient Support Program", self.digest)
        self.assertIn("slug: psp", self.digest)

    def test_says_when_to_offer_it(self):
        self.assertIn("Offer it when:", self.digest)
        self.assertIn("patient", self.digest.lower())

    def test_points_at_the_pack_without_quoting_it(self):
        # The digest exists so a declined offer costs a few hundred tokens
        # rather than a file read; carrying the interview inline would defeat
        # the whole arrangement.
        psp = get_template("psp")
        self.assertIn(psp.path, self.digest)
        interview = Path(psp.file_path("interview")).read_text(encoding="utf-8")
        self.assertNotIn(interview[:200], self.digest)

    def test_states_the_spec_format(self):
        self.assertIn("spec format: yaml", self.digest)
