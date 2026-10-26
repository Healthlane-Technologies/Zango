"""Phase D of the preview-to-spec plan: what the YAML can now say, and how the build hears it.

- `app.ui` (radius, density): the look, as choices.
- `type: dashboard` with `blocks`: dashboards declared, not sketched.
- Contracts on custom work (`data`, `interactions`, `acceptance`, typed `trigger`): required
  before the spec is ready, and carried into the build's hole texts.
"""

import copy
import json
import subprocess
import sys
import tempfile
import unittest

from pathlib import Path

import yaml

from zango.apps.agent_mode.custom_work import contract_gaps, counts
from zango.apps.agent_mode.preview_probe import custom_screens, playwright_available
from zango.apps.agent_mode.spec_tools import SpecWorkbench, ToolRefused
from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir
from zango.apps.shared.app_templates.services.packs import import_pack
from zango.apps.shared.app_templates.services.spec.validate import validate_doc

from .tests import AppTemplatesTestBase


PACK = PACKS_DIR / "zango_app"
SPEC_CHECK = Path(studio_plugin_dir()) / "skills" / "zango-app-studio" / "scripts" / "spec_check.py"


class DeclaredUITestBase(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        self.version, _ = import_pack(PACK, publish_now=True)
        catalogue.clear_caches()
        self.template = catalogue.get_template("zango-app")
        self.doc = yaml.safe_load(self.template.example_yaml)

    def issues(self, doc, **kw):
        return validate_doc(doc, self.template, **kw)

    def errors_at(self, doc, fragment):
        return [i for i in self.issues(doc) if i["level"] == "error" and fragment in (i.get("path") or "") + i["message"]]

    def page(self, code, doc=None):
        return next(p for p in (doc or self.doc)["pages"] if p["code"] == code)

    def entity(self, code, doc):
        return next(e for m in doc["modules"] for e in m.get("entities") or [] if e["code"] == code)


class AppUITests(DeclaredUITestBase):
    def test_radius_and_density_are_choices(self):
        doc = copy.deepcopy(self.doc)
        doc["app"]["ui"] = {"radius": "soft", "density": "compact"}
        self.assertEqual([i for i in self.issues(doc) if i["level"] == "error"], [])
        doc["app"]["ui"] = {"radius": "round"}
        self.assertTrue(self.errors_at(doc, "radius"))

    def test_nothing_else_is_a_look_setting(self):
        doc = copy.deepcopy(self.doc)
        doc["app"]["ui"] = {"font": "serif"}
        self.assertTrue([i for i in self.issues(doc) if i["level"] == "error" and "/app/ui" in (i.get("path") or "")])


class DashboardTests(DeclaredUITestBase):
    def test_the_example_declares_a_clean_dashboard(self):
        page = self.page("finance_home")
        self.assertEqual(page["type"], "dashboard")
        self.assertEqual(self.issues(self.doc, strict=True) and [
            i for i in self.issues(self.doc, strict=True) if i["level"] == "error"], [])

    def test_a_dashboard_is_not_a_custom_screen(self):
        self.assertNotIn("/pages/@finance_home", custom_screens(self.doc))
        self.assertEqual(counts(self.doc)["dashboards"], 1)

    def test_blocks_only_on_dashboards(self):
        doc = copy.deepcopy(self.doc)
        self.page("invoices", doc)["blocks"] = [{"kpis": [{"label": "x", "value": {"count": "invoice"}}]}]
        self.assertTrue([i for i in self.issues(doc) if i["level"] == "error" and "/pages" in (i.get("path") or "")])

    def test_the_build_checker_catches_wrong_fields_in_blocks(self):
        doc = copy.deepcopy(self.doc)
        blocks = self.page("finance_home", doc)["blocks"]
        blocks[1]["grid"][1]["list"]["primary"] = "invoice_number"
        found = [i["message"] for i in self.issues(doc) if i["level"] == "error"]
        self.assertTrue(any("invoice_number" in m for m in found), found)


class ContractTests(DeclaredUITestBase):
    def test_the_example_has_every_contract(self):
        self.assertEqual(contract_gaps(self.doc), [])

    def test_ready_needs_acceptance_on_custom_screens_and_requirements(self):
        doc = copy.deepcopy(self.doc)
        self.page("dashboard", doc).pop("acceptance")
        self.entity("vendor", doc)["custom_requirements"][1].pop("trigger")
        bench = SpecWorkbench(yaml.safe_dump(doc, sort_keys=False), self.template, emit=lambda e: None)
        with self.assertRaises(ToolRefused) as refused:
            bench.mark_ready("done")
        text = str(refused.exception)
        self.assertIn("/pages/@dashboard: acceptance", text)
        self.assertIn("custom_requirements/1: trigger", text)

    def test_the_example_is_ready(self):
        bench = SpecWorkbench(self.template.example_yaml, self.template, emit=lambda e: None)
        self.assertIn("Marked ready", bench.mark_ready("done"))

    def test_a_trigger_names_a_real_transition(self):
        doc = copy.deepcopy(self.doc)
        self.entity("vendor", doc)["custom_requirements"][1]["trigger"]["transition"] = "approved"
        found = [i["message"] for i in self.issues(doc) if i["level"] == "error"]
        self.assertTrue(any("'approved' is not a transition of vendor" in m for m in found), found)


class BuildHearsItTests(DeclaredUITestBase):
    """spec_check.py: what the build agent reads in .zas/."""

    def run_check(self, doc):
        tmp = tempfile.mkdtemp()
        spec = Path(tmp) / "app_spec.yaml"
        spec.write_text(yaml.safe_dump(doc, sort_keys=False))
        proc = subprocess.run([sys.executable, str(SPEC_CHECK), str(spec), "--workspace", tmp, "--quiet"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        zas = Path(tmp) / ".zas"
        return json.loads((zas / "spec.ui.json").read_text()), (zas / "holes.md").read_text()

    def test_prototype_screens_are_themed_or_rebuilt(self):
        doc = copy.deepcopy(self.doc)
        doc["prototype"] = {"screens": [
            {"id": "vendors", "maps": "/pages/@vendors"},
            {"id": "vendor", "maps": "/detail_views/@vendor_360"},
            {"id": "po", "maps": "/detail_views/@po_360", "rebuild": True, "why": "the user wants the PO paper layout"},
            {"id": "orders", "maps": "/pages/@purchase_orders", "rebuild": True, "why": "a lane per buyer"},
            {"id": "home", "maps": "/pages/@dashboard"},
            {"id": "signin", "only": "prototype", "why": "platform sign-in"},
        ]}
        tmp = tempfile.mkdtemp()
        proto = Path(tmp) / ".zas" / "bundle" / "prototype"
        proto.mkdir(parents=True)
        ids = [s["id"] for s in doc["prototype"]["screens"]] + ["orphan"]
        (proto / "manifest.json").write_text(json.dumps({"screens": [{"id": i} for i in ids]}))
        (proto / "index.md").write_text("# Approved prototype\n")
        spec = Path(tmp) / "app_spec.yaml"
        spec.write_text(yaml.safe_dump(doc, sort_keys=False))
        proc = subprocess.run([sys.executable, str(SPEC_CHECK), str(spec), "--workspace", tmp, "--quiet"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        zas = Path(tmp) / ".zas"
        resolved = json.loads((zas / "spec.resolved.json").read_text())
        cls = {r["id"]: r["cls"] for r in resolved["prototype"]["screens"]}
        self.assertEqual(cls, {"vendors": "theme", "vendor": "theme", "po": "rebuild", "orders": "rebuild",
                               "home": "rebuild", "signin": "prototype-only"})
        holes = {h["where"]: h for h in resolved["holes"]}
        self.assertEqual(holes["detail_views.po_360"]["kind"], "rebuild_view")
        self.assertEqual(holes["pages.purchase_orders"]["slot"], "RebuildPurchaseOrders")
        self.assertIn("Approved look: `.zas/bundle/prototype/screens/home/`", holes["pages.dashboard"]["text"])
        self.assertEqual(holes["pages.purchase_orders"]["bundle"], ".zas/bundle/prototype/screens/orders/")
        self.assertNotIn("pages.vendors", holes)  # themed: no custom code
        ui = json.loads((zas / "spec.ui.json").read_text())
        self.assertEqual(ui["pages"]["purchase_orders"]["rebuild"], "RebuildPurchaseOrders")
        self.assertEqual(ui["detail_views"]["po_360"]["rebuild"], "RebuildPo360")
        self.assertNotIn("rebuild", ui["pages"]["vendors"])
        index = (proto / "index.md").read_text()
        self.assertIn("| `vendors` | /pages/@vendors | theme |", index)
        self.assertIn("| `orphan` | - | unmapped |", index)
        warned = [i["msg"] for i in resolved["issues"] if i["where"] == "prototype.screens"]
        self.assertTrue(any("orphan" in m for m in warned), warned)

    def test_a_forced_rebuild_needs_a_why(self):
        doc = copy.deepcopy(self.doc)
        doc["prototype"] = {"screens": [{"id": "vendors", "maps": "/pages/@vendors", "rebuild": True},
                                        {"id": "x", "maps": "/pages/@nope"}]}
        tmp = tempfile.mkdtemp()
        spec = Path(tmp) / "app_spec.yaml"
        spec.write_text(yaml.safe_dump(doc, sort_keys=False))
        subprocess.run([sys.executable, str(SPEC_CHECK), str(spec), "--workspace", tmp, "--quiet"],
                       capture_output=True, text=True)
        issues = (Path(tmp) / ".zas" / "issues.md").read_text()
        self.assertIn("rebuild: true needs a why", issues)
        self.assertIn("page 'nope' not in pages", issues)

    def test_app_design_themes_the_runtime(self):
        doc = copy.deepcopy(self.doc)
        doc["app"]["design"] = {
            "source": "prototype",
            "fonts": {"body": "Plus Jakarta Sans", "mono": "JetBrains Mono"},
            "tokens": {"brand": "#0F766E", "page": "#F3F6F6", "card": "#FFFFFF", "sunk": "#EAF0EF",
                       "border": "#DCE5E3", "radius": "12px", "ok": "#1F7A45", "ok-bg": "#E4F4EA",
                       "purple": "#6B3FC4", "bad": "red;}body{x:y"},
        }
        ui, _ = self.run_check(doc)
        app = ui["app"]
        self.assertEqual(app["brand"], "#0F766E")  # brand drives --brand and every ramp
        css = app["design"]["css"]
        main, pinned = css.split("html:root [data-zas-pinned]")
        self.assertIn("--z-ground: #F3F6F6;", main)
        self.assertIn("--z-r-card: 12px;", main)
        self.assertIn("--t-green-bd: color-mix(", main)
        self.assertIn("--p-purple: #6B3FC4;", main)
        # the package palettes that load after tokens.css must not win (FormRenderer Submit)
        self.assertIn("--color-brand-500: var(--brand);", main)
        self.assertNotIn("body{x:y", css)  # not a plain value: dropped
        self.assertIn('--z-font: "Plus Jakarta Sans"', main)
        # the gallery keeps the defaults for its goldens
        self.assertIn("--z-ground: #f7f8fa;", pinned)
        self.assertIn(":where(.zas, .zas *, .zas-login, .zas-login *)", css)
        self.assertEqual(
            app["design"]["font_url"],
            "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap",
        )
        # kit mode: nothing
        ui, _ = self.run_check(copy.deepcopy(self.doc))
        self.assertNotIn("design", ui["app"])

    def test_ui_dashboard_and_contracts_reach_the_build(self):
        doc = copy.deepcopy(self.doc)
        doc["app"]["ui"] = {"radius": "sharp", "density": "compact"}
        ui, holes = self.run_check(doc)
        self.assertEqual(ui["app"]["ui"], {"radius": "sharp", "density": "compact"})
        self.assertEqual(ui["pages"]["finance_home"]["type"], "custom")
        self.assertEqual(ui["pages"]["finance_home"]["export"], "DashboardFinanceHome")
        row = next(line for line in holes.splitlines() if "`pages.finance_home`" in line)
        self.assertIn('"Amount to pay" = sum of invoice.amount where status == approved', row)
        self.assertIn("bar chart \"Invoices by status\": invoice, grouped by status, count", row)
        row = next(line for line in holes.splitlines() if "Approval email" in line)
        self.assertIn("Trigger: transition approve.", row)
        self.assertIn("Acceptance (test each): (1) Approving a vendor sends one email", row)
        row = next(line for line in holes.splitlines() if "`pages.dashboard`" in line)
        self.assertIn("Interactions: kpi_click -> opens the matching list page; row_click -> opens po_360.", row)


@unittest.skipUnless(playwright_available(), "Playwright is not installed")
class DashboardPreviewTests(DeclaredUITestBase):
    """The preview draws a declared dashboard from the demo data, and applies app.ui."""

    def test_the_finance_dashboard_draws_its_blocks(self):
        import re

        from playwright.sync_api import sync_playwright

        from zango.apps.shared.app_templates.services.builder import compose

        doc = copy.deepcopy(self.doc)
        doc["app"]["ui"] = {"radius": "soft"}
        text = yaml.safe_dump(doc, sort_keys=False)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page()
                page.route("**/*", lambda r: r.abort())
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.set_content(compose(self.version))
                out = page.evaluate("""y => {
                    window.zangoLoad(y);
                    ZAS_GOTO({ role: 'Finance', page: 'finance_home' });
                    const c = document.querySelector('.z-content');
                    return { text: c.innerText, radius: getComputedStyle(document.querySelector('.d-panel')).borderTopLeftRadius,
                             tiles: c.querySelectorAll('.d-stat').length, bars: c.querySelectorAll('.ui-bar').length,
                             paths: [...c.querySelectorAll('[data-zas-path]')].map(e => e.dataset.zasPath) };
                }""", text)
                browser.close()
        except Exception as exc:  # noqa: BLE001 - Chromium itself not installed
            if re.search(r"Executable doesn't exist|playwright install", str(exc)):
                self.skipTest(str(exc))
            raise
        self.assertEqual(errors, [])
        self.assertIn("Finance overview", out["text"])
        self.assertIn("Invoices to pay", out["text"])
        self.assertIn("Due soonest", out["text"])
        self.assertEqual(out["tiles"], 3)
        self.assertEqual(out["bars"], 4)  # one per invoice status
        self.assertEqual(out["radius"], "16px")
        self.assertIn("/pages/@finance_home/blocks/1/grid/1", out["paths"])
