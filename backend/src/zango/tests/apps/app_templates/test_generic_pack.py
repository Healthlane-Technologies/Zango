import copy

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack, lint, read_pack
from zango.apps.shared.app_templates.services.spec import rules, yamlio
from zango.apps.shared.app_templates.services.spec.validate import validate_text

from .tests import AppTemplatesTestBase


PACK = PACKS_DIR / "zango_app"


class GenericPackTests(AppTemplatesTestBase):
    """The bundled "Custom Zango app" pack: Zango app spec v1 + App Studio."""

    def setUp(self):
        super().setUp()
        self.version, _ = import_pack(PACK, publish_now=True)
        catalogue.clear_caches()
        self.template = catalogue.get_template("zango-app")

    def test_the_pack_reads_lints_and_publishes(self):
        pack = read_pack(PACK)
        self.assertEqual(pack.manifest["slug"], "zango-app")
        self.assertEqual(pack.manifest["spec_dialect"], "zango-app/1")
        self.assertIn("builder_html", pack.documents)
        self.assertIn("builder_adapter", pack.documents)
        problems = [i for i in lint(self.version) if i["level"] == "error"]
        self.assertEqual(problems, [])
        warnings = [i["message"] for i in lint(self.version) if i["level"] == "warning"]
        self.assertEqual(warnings, ["The template has no build skill."])
        self.assertTrue(self.version.has_builder)
        self.assertEqual(self.version.spec_root, "app_spec")
        self.assertEqual([r["id"] for r in self.version.references], ["vendor_hub"])
        self.assertTrue(self.version.drafting_md.startswith("# Drafting"))

    def test_the_preview_page_works_offline(self):
        html = self.version.builder_html
        self.assertNotIn('src="https://', html)  # js-yaml and lucide are inlined
        self.assertIn("jsyaml", html)
        self.assertIn("lucide", html)
        self.assertIn("type: 'ready'", self.version.builder_adapter)
        self.assertNotIn("type: 'change'", self.version.builder_adapter)

    def test_starter_example_and_reference_are_clean(self):
        for name, text in (
            ("starter", self.template.starter_yaml),
            ("example", self.template.example_yaml),
            ("reference", self.version.references[0]["yaml"]),
        ):
            with self.subTest(name):
                doc, issues = validate_text(text, self.template, strict=True)
                self.assertIsNotNone(doc)
                self.assertEqual(issues, [])

    def _issues(self, doc):
        return {i["rule"] for i in rules.evaluate(doc, self.template.rules)}

    def test_rules_catch_broken_references(self):
        base = yamlio.load(self.template.example_yaml)
        self.assertEqual(self._issues(base), set())

        doc = copy.deepcopy(base)
        doc["roles"][0]["menu"][0]["page"] = "nowhere"
        doc["roles"][0]["landing"] = "nowhere"
        doc["pages"][0]["entity"] = "ghost"
        vendor = doc["modules"][1]["entities"][0]
        vendor["workflow"]["transitions"][0]["roles"] = ["Nobody"]
        vendor["workflow"]["transitions"][0]["to"] = "limbo"
        vendor["form"]["create"]["sections"][0]["fields"][0] = "legal_nam"
        vendor["fields"][2]["vendor_type"]["choices"] = "no_such_set"
        vendor["fields"][3]["category"].pop("to")
        doc["detail_views"][0]["tabs"][1]["entity"] = "ghost"
        doc["roles"].append(copy.deepcopy(doc["roles"][0]))
        self.assertTrue(
            {
                "menu_page_known",
                "landing_page_known",
                "page_entity_known",
                "transition_role_known",
                "transition_status_known",
                "form_section_field_known",
                "choice_set_known",
                "link_field_target",
                "tab_entity_known",
                "role_name_unique",
            }
            <= self._issues(doc)
        )

    def test_structural_mistakes_are_errors(self):
        doc = yamlio.load(self.template.starter_yaml)
        entity = doc["modules"][0]["entities"][0]
        entity["fields"][0]["name"]["type"] = "string"  # not a field type
        entity["kind"] = "table"
        entity["feilds"] = []  # a typo of a fixed key
        doc["pages"][0]["type"] = "list"
        text = yamlio.dump(doc)
        _, issues = validate_text(text, self.template)
        structural = {i["path"] for i in issues if i.get("structural")}
        self.assertIn("/modules/0/entities/0/fields/0/name/type", structural)
        self.assertIn("/modules/0/entities/0/kind", structural)
        self.assertIn("/pages/0/type", structural)
        self.assertTrue(any(p.startswith("/modules/0/entities/0") for p in structural))

    def test_missing_pieces_are_warnings_while_drafting(self):
        doc = yamlio.load(self.template.starter_yaml)
        del doc["modules"][0]["entities"][0]["access"]
        _, issues = validate_text(yamlio.dump(doc), self.template)
        missing = [i for i in issues if i["code"] == "schema:required"]
        self.assertEqual([i["level"] for i in missing], ["warning"])
        _, strict = validate_text(yamlio.dump(doc), self.template, strict=True)
        self.assertTrue(any(i["level"] == "error" for i in strict))
