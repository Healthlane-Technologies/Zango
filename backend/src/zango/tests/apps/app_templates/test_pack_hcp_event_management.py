from pathlib import Path

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack, lint
from zango.apps.shared.app_templates.services.spec.validate import validate_text

from .tests import AppTemplatesTestBase


SLUG = "hcp-event-management"


class HcpEventManagementPackTests(AppTemplatesTestBase):
    """The lean "HCP Event Management" pack borrows everything else from zango-app."""

    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "zango_app", publish_now=True)
        self.version, _ = import_pack(PACKS_DIR / "hcp_event_management", publish_now=True)
        catalogue.clear_caches()
        self.view = catalogue.get_template(SLUG)

    def test_lints_and_borrows_from_the_generic_pack(self):
        errors = [i for i in lint(self.version) if i["level"] == "error"]
        self.assertEqual(errors, [])
        self.assertTrue(self.view.borrowed_from.startswith("zango-app@"))
        self.assertTrue(self.view.json_schema)
        self.assertTrue(Path(self.view.file_path("drafting")).is_file())
        self.assertEqual([r["id"] for r in self.version.references], ["onco_events_south"])

    def test_starter_example_and_reference_are_clean(self):
        for name, text in (
            ("starter", self.view.starter_yaml),
            ("example", self.view.example_yaml),
            ("reference", self.version.references[0]["yaml"]),
        ):
            with self.subTest(name):
                doc, issues = validate_text(text, self.view, strict=True)
                self.assertIsNotNone(doc)
                for issue in issues:
                    print(name, issue)
                self.assertEqual([i for i in issues if i["level"] == "error"], [])
