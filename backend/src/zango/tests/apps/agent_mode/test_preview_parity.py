"""Preview parity and the one look (spec-to-build F4).

zas_test.design's `parity` group compares each built custom screen's kit tree with the one the user
approved (.zas/bundle/); its failures go to the fix rounds, then stay in the report as gaps. After
the checks, the agent gets one look: each built screen next to the approved screenshot.
"""

import json
import sys
import tempfile
import unittest

from pathlib import Path

from zango.apps.agent_mode.studio_build import LayerResult, StudioBuild
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir


SCRIPTS = Path(studio_plugin_dir()) / "skills" / "zango-app-studio" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from zas_test import design, report  # noqa: E402


APPROVED = [
    {"kit": "kpis", "items": ["Open POs", "Overdue"]},
    {"kit": "bars", "title": "Open by status"},
    {"kit": "table", "title": "Latest POs", "items": ["PO", "Vendor", "Amount"]},
    {"kit": "panel", "title": "Onboarding", "children": [{"kit": "progress"}]},
]


class ParityDiffTests(unittest.TestCase):
    def test_the_same_tree_has_no_differences(self):
        self.assertEqual(design.parity_diff(APPROVED, json.loads(json.dumps(APPROVED))), [])

    def test_a_missing_block_and_an_extra_one_are_named(self):
        built = [APPROVED[0], {"kit": "list", "title": "Due soonest"}, APPROVED[2], APPROVED[3]]
        self.assertEqual(design.parity_diff(APPROVED, built),
                         ['missing bars "Open by status"', 'not in the approved screen: list "Due soonest"'])

    def test_labels_and_columns_are_compared(self):
        built = json.loads(json.dumps(APPROVED))
        built[0]["items"] = ["Open POs"]
        built[2]["items"] = ["PO", "Amount", "Vendor"]
        probs = design.parity_diff(APPROVED, built)
        self.assertIn("kpis: labels missing ['Overdue']", probs)
        self.assertIn('table "Latest POs": columns out of order [\'PO\', \'Amount\', \'Vendor\'] (approved [\'PO\', \'Vendor\', \'Amount\'])', probs)

    def test_nesting_counts(self):
        built = json.loads(json.dumps(APPROVED))
        built[3]["children"] = []
        self.assertEqual(design.parity_diff(APPROVED, built), ["missing progress"])

    def test_a_renamed_title_is_a_missing_and_an_extra_block(self):
        built = json.loads(json.dumps(APPROVED))
        built[1]["title"] = "By status"
        self.assertEqual(design.parity_diff(APPROVED, built),
                         ['missing bars "Open by status"', 'not in the approved screen: bars "By status"'])


class OpenShellLintTests(unittest.TestCase):
    """Open mode builds the shell as src/custom/Shell.tsx on makeShell (references/open-mode.md)."""

    def ws(self, tmp, shell=None, app=None, open_mode=True):
        root = Path(tmp)
        if open_mode:
            (root / ".zas" / "bundle" / "prototype").mkdir(parents=True)
            (root / ".zas" / "bundle" / "prototype" / "manifest.json").write_text("{}")
        (root / "frontend" / "src" / "custom").mkdir(parents=True)
        if shell is not None:
            (root / "frontend" / "src" / "custom" / "Shell.tsx").write_text(shell)
        if app is not None:
            (root / "frontend" / "src" / "App.tsx").write_text(app)
        return str(root)

    def test_kit_mode_has_nothing_to_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(design.open_shell_problems(self.ws(tmp, open_mode=False)), [])

    def test_open_mode_needs_the_shell_and_its_wiring(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIn("no frontend/src/custom/Shell.tsx", design.open_shell_problems(self.ws(tmp))[0])
        with tempfile.TemporaryDirectory() as tmp:
            probs = design.open_shell_problems(self.ws(tmp, shell="export default () => null;", app="<ZApp />"))
            self.assertEqual(len(probs), 2)
        with tempfile.TemporaryDirectory() as tmp:
            ok = self.ws(tmp, shell='export default makeShell({ tone: "dark" });',
                         app="<ZApp customComponents={{ Layout: Shell }} />")
            self.assertEqual(design.open_shell_problems(ok), [])


class OpenScreensLintTests(unittest.TestCase):
    """Open mode: themed pages stay the runtime's, and their stylesheets use tokens only."""

    M = {"pages": {"vendors": {"type": "crud"}, "orders": {"type": "crud"}},
         "prototype": {"screens": [{"id": "v", "page": "vendors", "kind": "page", "cls": "theme"},
                                   {"id": "o", "page": "orders", "kind": "page", "cls": "rebuild"}]}}

    def dx(self, tmp, index):
        import types

        root = Path(tmp) / "frontend" / "src" / "custom"
        (root / "pages").mkdir(parents=True)
        (root / "screens").mkdir()
        (root / "pages" / "index.ts").write_text(index)
        return types.SimpleNamespace(ws=tmp, M=self.M), root

    def test_a_themed_page_stays_the_runtime_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            Dx, _ = self.dx(tmp, 'export const Page_vendors = makeListPage("vendors");\n'
                                 'export const Page_orders = makeListPage("orders");\n')
            self.assertEqual(design.themed_page_problems(Dx), [])
        with tempfile.TemporaryDirectory() as tmp:
            Dx, _ = self.dx(tmp, 'export const Page_vendors = VendorsByHand;\n')
            self.assertIn("Page_vendors is themed", design.themed_page_problems(Dx)[0])

    def test_a_screen_stylesheet_is_scoped_and_token_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            Dx, root = self.dx(tmp, "")
            ok = root / "screens" / "vendors.css"
            ok.write_text('[data-zas-key="vendors"] .zas-tb { gap: var(--z-gap); background: var(--p-accent-soft); }')
            self.assertEqual(design.screen_css_problems(Dx, str(ok), "vendors.css"), [])
            bad = root / "screens" / "vendors.css"
            bad.write_text('.zas-t th, [data-zas-key="vendors"] td { color: #333; background: url(x.png); }')
            probs = design.screen_css_problems(Dx, str(bad), "vendors.css")
            self.assertEqual(len(probs), 3, probs)
            other = root / "screens" / "orders.css"
            other.write_text('[data-zas-key="orders"] td { gap: 0; }')
            self.assertIn("only for a themed page", design.screen_css_problems(Dx, str(other), "orders.css")[0])


class OpenDesignLintTests(unittest.TestCase):
    """Open mode: src/custom spells the prototype's colours as tokens and its fonts from app.design."""

    M = {"app": {"design": {"fonts": {"body": "Plus Jakarta Sans", "mono": "JetBrains Mono"},
                            "tokens": {"brand": "#0F766E", "page": "#F3F6F6", "coral": "#E0693F"}}},
         "pages": {}, "holes": []}

    def lint(self, slot, open_mode=True):
        import types

        with tempfile.TemporaryDirectory() as tmp:
            if open_mode:
                (Path(tmp) / ".zas" / "bundle" / "prototype").mkdir(parents=True)
                (Path(tmp) / ".zas" / "bundle" / "prototype" / "manifest.json").write_text("{}")
                (Path(tmp) / "frontend" / "src").mkdir(parents=True)
                (Path(tmp) / "frontend" / "src" / "App.tsx").write_text("<ZApp customComponents={{ Layout: Shell }} />")
            custom = Path(tmp) / "frontend" / "src" / "custom"
            (custom / "slots").mkdir(parents=True)
            (custom / "Shell.tsx").write_text("export default makeShell({});")
            (custom / "slots" / "Home.tsx").write_text(slot)
            got = {}
            Dx = types.SimpleNamespace(ws=tmp, M=self.M, check=lambda rid, title, where, fn, *a: got.update(r=fn()))
            design.g_lint(Dx)
            return got["r"]

    def test_tokens_and_listed_fonts_pass(self):
        ok, why = self.lint('<div style={{ color: "var(--z-text)", background: "var(--p-coral)", '
                            'fontFamily: "Plus Jakarta Sans, sans-serif" }} />')
        self.assertTrue(ok, why)

    def test_literals_name_their_token_and_fonts_come_from_app_design(self):
        ok, why = self.lint('<div style={{ color: "#0f766e", background: "#E0693F", borderColor: c, '
                            'fontFamily: "Comic Sans MS" }}>{"#123456"}</div>')
        self.assertFalse(ok)
        self.assertIn("app.design's `brand`, write var(--brand)", why)
        self.assertIn("app.design's `coral`, write var(--p-coral)", why)
        self.assertIn("colour `#123456` (use a token", why)
        self.assertIn("inline `borderColor` must be a token", why)
        self.assertIn("font `Comic Sans MS` is not in app.design.fonts", why)

    def test_kit_mode_is_unchanged(self):
        ok, why = self.lint('<div style={{ color: "var(--z-text)" }} />', open_mode=False)
        self.assertFalse(ok)
        self.assertIn("inline `color` style", why)


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.Dx = type("Dx", (), {})()
        self.Dx.M = {"pages": {"workload": {"route": "/app/workload"}},
                     "detail_views": {"vendor_360": {"hero": "vendor"}}}

    def test_a_page_opens_its_route(self):
        hole = {"kind": "custom_page", "where": "pages.workload", "function": "Workload"}
        self.assertEqual(design.parity_target(self.Dx, hole), ("/app/workload", None, '[data-zas="page"]', None))

    def test_a_panel_is_its_hooks_key_on_the_hero(self):
        hole = {"kind": "custom_panel", "where": "detail_views.vendor_360.sidebar[1]", "function": "vendor_360__custom__sidebar_2"}
        self.assertEqual(design.parity_target(self.Dx, hole),
                         (None, None, '[data-zas="panel"][data-zas-key="sidebar_2"]', "vendor"))

    def test_a_tab_or_a_section_in_one_opens_the_tab_first(self):
        hole = {"kind": "custom_panel", "where": "detail_views.vendor_360.tabs.risk.sections[0]", "function": "vendor_360__custom__risk_1"}
        self.assertEqual(design.parity_target(self.Dx, hole)[1], "risk")


class NoBundleTests(unittest.TestCase):
    def test_without_a_bundle_parity_is_skipped_with_a_reason(self):
        ws = Path(tempfile.mkdtemp())
        (ws / ".zas").mkdir()
        (ws / ".zas" / "spec.resolved.json").write_text(json.dumps({"holes": []}))
        Dx = design.D(str(ws))
        design.g_parity(Dx, None)
        self.assertEqual(Dx.results[0]["status"], "skip")
        self.assertIn("no approval bundle", Dx.results[0]["detail"])


class ReportTests(unittest.TestCase):
    def test_parity_is_reported_not_blocking(self):
        self.assertTrue("design.parity.pages.workload.manager".startswith(report.NON_BLOCKING))
        self.assertIn("parity", design.GROUPS)


class OneLookTests(unittest.TestCase):
    def build(self):
        root = Path(tempfile.mkdtemp())
        (root / "ws" / ".zas").mkdir(parents=True)
        return StudioBuild(skill_dir=str(root), workspace=str(root / "ws"), spec_path=str(root / "s.yaml"),
                           run_dir=str(root), base_dir=str(root), app_name="demo")

    def test_the_look_lists_each_approved_and_built_pair(self):
        b = self.build()
        self.assertEqual(b.look_digest(), "")
        (b.zas_dir / "parity_looks.json").write_text(json.dumps([
            {"screen": "/pages/@workload", "role": "Manager", "approved": ".zas/bundle/screens/pages.workload/shot.manager.png",
             "built": ".zas/screens/parity/pages.workload.manager.png"},
            {"screen": "/pages/@other", "role": "Manager", "approved": None, "built": ".zas/screens/parity/x.png"},
        ]))
        text = b.look_digest()
        self.assertIn("approved `.zas/bundle/screens/pages.workload/shot.manager.png`, built `.zas/screens/parity/pages.workload.manager.png`", text)
        self.assertNotIn("/pages/@other", text)

    def test_parity_failures_alone_do_not_fail_the_build(self):
        from zango.apps.agent_mode import studio_build

        only_parity = LayerResult(name="design", status="fail", failures=[{"id": "design.parity.pages.x.manager"}])
        other = LayerResult(name="design", status="fail", failures=[{"id": "design.tree.v.manager"}])
        self.assertFalse(studio_build.blocking({"design": only_parity}))
        self.assertTrue(studio_build.blocking({"design": other}))
        self.assertTrue(studio_build.blocking({"api": LayerResult(name="api", status="fail")}))

    def test_build_status_and_report_verdict_agree_on_what_blocks(self):
        # Regression: goldens failed as "Ready with gaps" in the report but StudioChecksFailed on the run.
        from zango.apps.agent_mode import studio_build

        self.assertEqual(set(studio_build.NON_FAILING), set(report.NON_BLOCKING))
        gallery = LayerResult(name="design", status="fail", failures=[{"id": "design.gallery.badges"}])
        self.assertFalse(studio_build.blocking({"design": gallery}))


class OpenParityTests(unittest.TestCase):
    """Open mode parity before P2 (plan B6): a look score per screen, the look round, the report."""

    def test_the_look_score_grows_with_the_difference(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            a, same, other = (str(Path(tmp) / n) for n in ("a.png", "same.png", "other.png"))
            Image.new("RGB", (1280, 1200), "white").save(a)
            Image.new("RGB", (1280, 1200), "white").save(same)
            im = Image.new("RGB", (640, 500), "white")  # another size: scaled to 1280 wide first
            im.paste((11, 79, 74), (0, 0, 120, 500))  # a dark sidebar
            im.save(other)
            self.assertEqual(design.look_score(a, same), 0)
            self.assertGreater(design.look_score(a, other), 0.1)

    def test_the_look_round_speaks_open_mode(self):
        pairs = [{"screen": "prototype/tests", "role": "Admin", "kind": "prototype", "class": "theme", "score": 0.1,
                  "approved": "a.png", "built": "b.png"},
                 {"screen": "prototype/home", "role": "Admin", "kind": "prototype", "class": "rebuild", "score": 0.3,
                  "approved": "c.png", "built": "d.png", "dom": "c.html"}]
        text = StudioBuild.prototype_look_digest(pairs, 1, 2)
        self.assertIn("next to the approved prototype", text)
        self.assertNotIn("sketch.js", text)
        self.assertLess(text.index("prototype/home"), text.index("prototype/tests"))  # worst first
        self.assertIn("snapshot `c.html`", text)
        self.assertIn("Never replace the runtime page with custom code", text)

    def test_the_report_lists_each_screen(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".zas").mkdir()
            (Path(tmp) / ".zas" / "parity_looks.json").write_text(json.dumps(
                [{"screen": "prototype/tests", "score": 0.2}, {"screen": "prototype/tests", "score": 0.4}]))
            D = {"ws": tmp, "M": {"prototype": {"screens": [
                     {"id": "tests", "cls": "theme", "kind": "page", "page": "tests", "maps": "/pages/@tests"},
                     {"id": "signin", "cls": "prototype-only", "reason": "platform sign-in"}]}},
                 "results": [{"id": "design.parity.proto.tests.admin", "status": "pass", "role": "Admin", "detail": ""},
                             {"id": "design.parity.proto.tests.lab", "status": "fail", "role": "Lab", "detail": "HTTP 500 /x"}],
                 "steps": [{"phase": 6, "step": "library: Chart.js", "status": "ok", "detail": "npm chart.js"}]}
            rows, libs = report.proto_screens(D)
            self.assertEqual((rows[0]["passed"], rows[0]["checked"], rows[0]["score"]), (1, 2, 0.4))
            self.assertEqual(rows[1]["builds"], "-")
            self.assertEqual(libs, ["Chart.js: npm chart.js"])
            self.assertIn("Prototype screens", report.s_proto(D))
