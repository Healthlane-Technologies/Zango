import os

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import LintFailed, import_pack, lint
from zango.apps.shared.app_templates.services.spec.validate import validate_text

from .tests import AppTemplatesTestBase


PACK = PACKS_DIR / "ordering_portal"


class OrderingPortalPackTests(AppTemplatesTestBase):
    """The bundled "Ordering Portal" pack: a lean zango-app/1 template."""

    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "zango_app", publish_now=True)
        try:
            self.version, _ = import_pack(PACK, publish_now=True)
        except LintFailed as exc:
            for issue in exc.issues:
                print("lint", issue["level"], issue.get("path"), issue["message"])
            raise
        catalogue.clear_caches()
        self.template = catalogue.get_template("ordering-portal")

    def test_the_pack_lints_and_borrows_from_the_generic_template(self):
        errors = [i for i in lint(self.version) if i["level"] == "error"]
        self.assertEqual(errors, [])
        self.assertTrue(self.template.borrowed_from.startswith("zango-app@"))
        self.assertTrue(self.template.json_schema)
        self.assertTrue(os.path.exists(self.template.file_path("drafting")))
        self.assertEqual([r["id"] for r in self.version.references], ["clinic_ordering"])

    def test_starter_example_and_reference_are_clean(self):
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
