import os

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack, lint
from zango.apps.shared.app_templates.services.spec.validate import validate_text

from .tests import AppTemplatesTestBase


SLUG = "partner-portal"


class PartnerPortalPackTests(AppTemplatesTestBase):
    """The lean Partner Portal pack borrows from the generic one."""

    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "zango_app", publish_now=True)
        self.version, _ = import_pack(PACKS_DIR / "partner_portal", publish_now=True)
        catalogue.clear_caches()
        self.template = catalogue.get_template(SLUG)

    def test_lints_and_borrows_from_the_generic_pack(self):
        issues = lint(self.version)
        for issue in issues:
            print("LINT", issue["level"], issue["message"])
        self.assertEqual([i for i in issues if i["level"] == "error"], [])
        self.assertIsNotNone(self.template)
        self.assertTrue(self.template.borrowed_from.startswith("zango-app@"))
        self.assertTrue(self.template.json_schema)
        drafting = self.template.file_path("drafting")
        self.assertTrue(drafting and os.path.exists(drafting))
        self.assertEqual(
            [r["id"] for r in self.version.references], ["agency_vendor_portal"]
        )

    def test_starter_example_and_reference_are_valid(self):
        for name, text in (
            ("starter", self.template.starter_yaml),
            ("example", self.template.example_yaml),
            ("reference", self.version.references[0]["yaml"]),
        ):
            with self.subTest(name):
                doc, issues = validate_text(text, self.template, strict=True)
                self.assertIsNotNone(doc)
                for issue in issues:
                    print(name, issue["level"], issue.get("path"), issue["message"])
                self.assertEqual([i for i in issues if i["level"] == "error"], [])
