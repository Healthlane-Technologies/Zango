import os

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack, lint
from zango.apps.shared.app_templates.services.spec.validate import validate_text

from .tests import AppTemplatesTestBase


SLUG = "adverse-event-intake"


class AdverseEventIntakePackTests(AppTemplatesTestBase):
    """The lean "Adverse Event Intake" pack borrows from the generic one."""

    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "zango_app", publish_now=True)
        self.version, _ = import_pack(
            PACKS_DIR / "adverse_event_intake", publish_now=True
        )
        catalogue.clear_caches()
        self.template = catalogue.get_template(SLUG)

    def test_the_pack_lints_and_borrows_from_the_generic_template(self):
        errors = [i for i in lint(self.version) if i["level"] == "error"]
        self.assertEqual(errors, [])
        self.assertTrue(self.template.borrowed_from.startswith("zango-app@"))
        self.assertTrue(self.template.json_schema)
        self.assertTrue(os.path.exists(self.template.file_path("drafting")))
        self.assertEqual(
            [r["id"] for r in self.version.references], ["ae_intake"]
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
                    print(name, issue["level"], issue["path"], issue["message"])
                self.assertEqual(
                    [i for i in issues if i["level"] == "error"], []
                )
