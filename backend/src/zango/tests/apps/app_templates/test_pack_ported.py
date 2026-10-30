import json

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue, porting
from zango.apps.shared.app_templates.services.packs import import_pack, lint
from zango.apps.shared.app_templates.services.spec.validate import validate_text

from .tests import AppTemplatesTestBase


PORTED = {
    "voucher_coupon": "voucher-coupon",
    "consent_management": "consent-management",
}


class PortedPackTests(AppTemplatesTestBase):
    """Packs ported from the Zelthy catalogue (services/porting.py) import and lint clean."""

    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "zango_app", publish_now=True)

    def test_each_pack_imports_lints_and_its_starter_is_valid(self):
        for folder, slug in PORTED.items():
            with self.subTest(folder):
                version, _ = import_pack(PACKS_DIR / folder, publish_now=True)
                catalogue.clear_caches()
                self.assertEqual(
                    [i for i in lint(version) if i["level"] == "error"], []
                )
                template = catalogue.get_template(slug)
                doc, issues = validate_text(template.starter_yaml, template, strict=True)
                self.assertIsNotNone(doc)
                self.assertEqual([i for i in issues if i["level"] == "error"], [])
                # The starter doubles as the example.
                self.assertEqual(template.starter_yaml, template.example_yaml)

    def test_each_pack_is_ready_for_template_mode(self):
        for folder in PORTED:
            with self.subTest(folder):
                pack = PACKS_DIR / folder
                manifest = json.loads((pack / "template.json").read_text())
                self.assertEqual(manifest["launch"], "direct")
                self.assertTrue(manifest["welcome"]["suggestions"])
                self.assertIn(manifest["icon"], porting.CONSOLE_ICONS)
                self.assertEqual(porting.schema_issues(pack), [])
                self.assertEqual(porting.manifest_issues(pack), [])


class PortingHelperTests(AppTemplatesTestBase):
    ENTRY = {
        "id": "x",
        "name": "Voucher & Coupon Management",
        "category": "Patient Services",
        "icon": "ticket",
        "description": "Issue and redeem vouchers.",
        "packages": ["workflow"],
        "roles": ["Program manager", "Pharmacy"],
        "workflows": ["Voucher issue"],
        "data_objects": ["Voucher"],
        "integrations": [],
        "compliance": [],
        "agents": [{"id": "recon", "name": "Reconciliation"}],
        "app_name": "Vouchers",
    }

    def test_slug_and_role_names(self):
        self.assertEqual(porting.slug_for("Voucher & Coupon Management"), "voucher-coupon-management")
        self.assertEqual(porting.role_name("Program manager"), "Program Manager")

    def test_manifest_keeps_only_icons_the_console_draws(self):
        m = porting.manifest_for(self.ENTRY, "vouchers", {"workflow": "Statuses"})
        self.assertEqual(m["icon"], "")
        self.assertEqual(m["example"], "starter.yaml")
        self.assertEqual(m["catalogue"]["roles"][0]["name"], "Program Manager")
        self.assertEqual(m["catalogue"]["packages"][0]["description"], "Statuses")
        self.assertEqual(m["catalogue"]["recommended_agents"], ["recon"])

    def test_the_skeleton_is_not_a_finished_starter(self):
        text = porting.starter_skeleton(self.ENTRY)
        self.assertIn("PORTING CHECKLIST", text)
        self.assertIn("name: Program Manager", text)
