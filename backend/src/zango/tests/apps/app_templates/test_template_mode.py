"""Template mode in the catalogue (T0) and the requirement it opens (T1).

A "direct" template stores its starting prototype with its YAML; a new app on it opens on that
preview with no brief, the welcome as its first message, ready to Commit at revision 1.
The ported packs are drawn by the kit (Playwright); without a browser those tests are skipped.
"""

import json
import shutil
import tempfile
import unittest

from pathlib import Path

from zango.apps.shared.app_templates.models import LaunchMode
from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import (
    export_pack,
    import_pack,
    lint,
    read_pack,
)
from zango.apps.shared.app_templates.services.paths import content_sha

from .tests import AppTemplatesTestBase


def _browser() -> bool:
    from zango.apps.agent_mode.preview_probe import playwright_available

    import sys

    return playwright_available(sys.executable)


DIRECT_PACKS = {"voucher_coupon": "voucher-coupon", "consent_management": "consent-management"}


def _copy_pack(folder: str, **manifest) -> Path:
    tmp = Path(tempfile.mkdtemp())
    dest = tmp / folder
    shutil.copytree(PACKS_DIR / folder, dest)
    path = dest / "template.json"
    data = json.loads(path.read_text())
    data.update(manifest)
    path.write_text(json.dumps(data))
    return dest


class LaunchFieldTests(AppTemplatesTestBase):
    """launch / welcome / prototype on the version, without drawing anything."""

    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "zango_app", publish_now=True)

    def _errors(self, version):
        return [i["message"] for i in lint(version) if i["level"] == "error"]

    def test_a_shipped_prototype_is_read_and_hashed(self):
        from zango.apps.agent_mode.prototype import parts_hash

        pack = _copy_pack("voucher_coupon")
        (pack / "prototype" / "screens").mkdir(parents=True)
        manifest = {"screens": [{"id": "home", "maps": "/pages/@dashboard"}], "roles": {}}
        (pack / "prototype" / "manifest.json").write_text(json.dumps(manifest))
        (pack / "prototype" / "screens" / "home.js").write_text("ZAS.screen('home', () => 'hi');")
        parsed = read_pack(pack)
        self.assertEqual(sorted(parsed.prototype), ["manifest.json", "screens/home.js"])
        version, _ = import_pack(pack)
        self.assertEqual(version.launch, LaunchMode.DIRECT)
        self.assertEqual(version.prototype_hash, parts_hash(version.prototype_parts))
        self.assertEqual(self._errors(version), [])
        # a shipped prototype is part of the pack: it goes out with an export
        self.assertIn(b"prototype/screens/home.js", export_pack(version))

    def test_direct_needs_a_welcome_message_and_a_prototype(self):
        pack = _copy_pack("voucher_coupon", welcome={"suggestions": ["x"]})
        version, _ = import_pack(pack)
        version.prototype_parts = {}
        version.prototype_hash = ""
        errors = self._errors(version)
        self.assertTrue(any("welcome.message" in e for e in errors), errors)
        self.assertTrue(any("no starting prototype" in e for e in errors), errors)

    def test_bad_launch_and_welcome_are_refused(self):
        version, _ = import_pack(_copy_pack("voucher_coupon", launch="sideways"))
        self.assertTrue(any("launch must be" in e for e in self._errors(version)))
        version.launch = LaunchMode.BRIEF
        version.welcome = {"message": "hi", "suggestions": ["a"] * 7}
        self.assertTrue(any("more than 6" in e for e in self._errors(version)))

    def test_a_brief_template_needs_none_of_it(self):
        version, _ = import_pack(_copy_pack("voucher_coupon", launch="brief", welcome={}))
        self.assertEqual(version.prototype_parts, {})
        self.assertEqual(self._errors(version), [])

    def test_a_drawn_prototype_is_not_part_of_the_pack_identity(self):
        version, _ = import_pack(_copy_pack("voucher_coupon", launch="brief"))
        before = content_sha(version, include_workspace=False)
        version.prototype_parts = {"manifest.json": json.dumps({"source": "kit", "screens": []})}
        version.prototype_hash = "x"
        self.assertEqual(content_sha(version, include_workspace=False), before)
        version.prototype_parts = {"manifest.json": json.dumps({"screens": []})}
        self.assertNotEqual(content_sha(version, include_workspace=False), before)


@unittest.skipUnless(_browser(), "Playwright is not installed")
class DirectPackTests(AppTemplatesTestBase):
    """The ported packs, drawn by the kit at import and checked at publish."""

    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "zango_app", publish_now=True)

    def test_each_pack_stores_a_prototype_of_every_page_for_every_role(self):
        from zango.apps.agent_mode.prototype import static_problems
        from zango.apps.shared.app_templates.services.spec import yamlio

        for folder, slug in DIRECT_PACKS.items():
            with self.subTest(folder):
                version, _ = import_pack(PACKS_DIR / folder, publish_now=True)
                self.assertEqual(version.status, "published")
                self.assertTrue(version.is_direct)
                parts = version.prototype_parts
                self.assertEqual(static_problems(parts), [])
                manifest = json.loads(parts["manifest.json"])
                # the prototype is the kit page itself: its markup, styles and scripts, the YAML it
                # draws, and a bridge to the preview
                self.assertEqual(manifest["source"], "imported")
                self.assertTrue(manifest["kit"])
                for part in ("body.html", "imported/styles.css", "imported/script-zy-spec.js", "imported/script-zz-bridge.js"):
                    self.assertIn(part, parts)
                doc = yamlio.load(version.starter_yaml)
                self.assertEqual(
                    sorted(manifest["roles"].values()), sorted(r["name"] for r in doc["roles"])
                )
                for s in manifest["screens"]:
                    self.assertTrue(s["maps"].startswith("/pages/@"))
                    if s.get("record"):
                        self.assertTrue(s.get("sample") not in (None, ""))
                # importing the same pack again is a no-op
                again, created = import_pack(PACKS_DIR / folder, publish_now=True)
                self.assertFalse(created)
                self.assertEqual(again.pk, version.pk)

    def test_a_requirement_opened_on_it_is_ready_to_commit(self):
        """T1: the direct path seeds the requirement; nothing is asked of the analyst."""
        import yaml

        from zango.apps.agent_mode.models import AgentRequirement, RequirementStatus
        from zango.apps.agent_mode.template_mode import (
            seed_direct,
            suggestions,
            welcome_text,
        )

        import_pack(PACKS_DIR / "voucher_coupon", publish_now=True)
        catalogue.clear_caches()
        template = catalogue.get_template("voucher-coupon")
        self.assertTrue(template.is_direct)
        requirement = AgentRequirement(title="Vouchers")
        seed_direct(requirement, template)
        self.assertEqual(requirement.initial_prompt, "")
        self.assertEqual(requirement.mode, "template")
        self.assertEqual(requirement.preview_mode, "open")
        self.assertEqual(requirement.status, RequirementStatus.READY)
        self.assertFalse(requirement.is_thinking)
        self.assertTrue(requirement.spec_is_draft)
        self.assertEqual(requirement.draft_revision, 1)
        self.assertEqual(requirement.prototype_parts, template.prototype_parts)
        self.assertEqual(requirement.prototype_hash, template.prototype_hash)
        doc = yaml.safe_load(requirement.spec_markdown)
        self.assertEqual(doc["app"]["design"]["source"], "prototype")
        self.assertEqual(
            len(doc["prototype"]["screens"]),
            len(json.loads(template.prototype_parts["manifest.json"])["screens"]),
        )
        # a kit-page prototype draws the requirement's YAML: it follows every change to it
        from zango.apps.agent_mode.prototype_kit import SPEC_PART

        self.assertIn("prototype:", requirement.prototype_parts[SPEC_PART])
        requirement.spec_markdown += "\n# changed in chat\n"
        self.assertTrue(requirement.sync_kit_spec())
        self.assertIn("changed in chat", requirement.prototype_parts[SPEC_PART])
        self.assertFalse(requirement.sync_kit_spec())
        self.assertEqual(
            [i for i in requirement.validation_issues if i.get("level") == "error"], []
        )
        self.assertIn("Voucher & Coupon Management", welcome_text(template))
        self.assertEqual(len(suggestions(template)), 4)

    def test_the_starting_prototype_passes_commits_checks(self):
        from zango.apps.agent_mode.prototype_kit import starting_prototype_issues

        for folder, slug in DIRECT_PACKS.items():
            with self.subTest(folder):
                version, _ = import_pack(PACKS_DIR / folder, publish_now=True)
                self.assertEqual(
                    starting_prototype_issues(version.starter_yaml, version.prototype_parts), []
                )
