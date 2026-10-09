from pathlib import Path

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack, lint
from zango.apps.shared.app_templates.services.spec.validate import validate_text

from .tests import AppTemplatesTestBase


PACK = PACKS_DIR / "medical_information_requests"


class MedicalInformationRequestsPackTests(AppTemplatesTestBase):
    """The bundled "Medical Information Requests" pack: a lean zango-app/1 template."""

    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "zango_app", publish_now=True)
        self.version, _ = import_pack(PACK, publish_now=True)
        catalogue.clear_caches()
        self.template = catalogue.get_template("medical-information-requests")

    def test_the_pack_lints_and_borrows_from_the_generic_template(self):
        issues = lint(self.version)
        self.assertEqual([i for i in issues if i["level"] == "error"], [])
        print("lint warnings:", [i["message"] for i in issues if i["level"] == "warning"])
        self.assertTrue(self.template.borrowed_from.startswith("zango-app@"))
        self.assertTrue(self.template.json_schema)
        self.assertTrue(Path(self.template.file_path("drafting")).is_file())
        self.assertEqual([r["id"] for r in self.version.references], ["medinfo_desk"])

    def test_starter_example_and_reference_are_clean(self):
        for name, text in (
            ("starter", self.template.starter_yaml),
            ("example", self.template.example_yaml),
            ("reference", self.version.references[0]["yaml"]),
        ):
            with self.subTest(name):
                doc, issues = validate_text(text, self.template, strict=True)
                self.assertIsNotNone(doc)
                self.assertEqual([i for i in issues if i["level"] == "error"], [])
                warnings = [i for i in issues if i["level"] == "warning"]
                if warnings:
                    print(name, "warnings:", [(i["path"], i["message"]) for i in warnings])
