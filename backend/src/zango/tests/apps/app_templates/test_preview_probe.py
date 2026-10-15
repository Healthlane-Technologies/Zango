"""The analyst's eyes on its custom screens (agent_mode/preview_probe.py).

Edits to a custom page, 360 tab or panel report what its sketch drew; preview_look
screenshots one; spec_mark_ready wants each to draw cleanly and to have been looked at.
The workbench tests use a stand-in probe; the last class runs the real preview page in
headless Chromium when Playwright is installed.
"""

import asyncio
import base64
import copy
import unittest

import yaml

from zango.apps.agent_mode.preview_probe import (
    PreviewProbe,
    ProbeError,
    custom_screens,
    format_check,
    playwright_available,
)
from zango.apps.agent_mode.preview_probe import format_result
from zango.apps.agent_mode.spec_tools import SpecWorkbench, ToolRefused, make_handler, tool_specs
from zango.apps.agent_mode.template_spec import unfinished_custom_work
from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack

from .tests import AppTemplatesTestBase


PACK = PACKS_DIR / "zango_app"
DASHBOARD = "/pages/@dashboard"
CHECKLIST = "/detail_views/@vendor_360/sidebar/2"
PNG = base64.b64encode(b"\x89PNG fake").decode()


class FakeProbe:
    """Answers like PreviewProbe; screens in ``broken`` fail."""

    def __init__(self, screens):
        self.screens = screens
        self.broken: set = set()
        self.calls: list = []
        self.looks = 0
        self.closed = False

    def _run(self, path):
        if path in self.broken:
            return {"path": path, "role": "Procurement Manager", "ok": False, "error": "x is not defined"}
        return {
            "path": path,
            "role": "Procurement Manager",
            "ok": True,
            "reads": [{"entity": "purchase_order", "rows": 12, "via": None}],
            "draws": ["KPI tiles: Open POs 8"],
        }

    def check(self, yaml_text, paths=None):
        self.calls.append(paths)
        return {"parse_error": None, "results": [self._run(p) for p in (paths or self.screens)]}

    def look(self, yaml_text, path, role=None, record=None, width=1280):
        self.looks += 1
        return {"show": {"ok": True, "role": "Procurement Manager", "record": None}, "run": self._run(path), "png": PNG}

    def close(self):
        self.closed = True


class PreviewProbeTestBase(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        self.version, _ = import_pack(PACK, publish_now=True)
        catalogue.clear_caches()
        self.template = catalogue.get_template("zango-app")
        self.doc = yaml.safe_load(self.template.example_yaml)
        self.emitted = []

    def bench(self, doc=None, probe=True, looks=None):
        text = self.template.example_yaml if doc is None else yaml.safe_dump(doc, sort_keys=False)
        self.probe = FakeProbe([DASHBOARD, CHECKLIST]) if probe else None
        return SpecWorkbench(text, self.template, emit=self.emitted.append, probe=self.probe, sketch_looks=looks)


class CustomScreensTests(PreviewProbeTestBase):
    def test_custom_screens_are_named_as_the_spec_tools_address_them(self):
        self.assertEqual(sorted(custom_screens(self.doc)), sorted([DASHBOARD, CHECKLIST]))

    def test_tabs_and_tab_sections_without_a_code_use_their_index(self):
        doc = copy.deepcopy(self.doc)
        doc["detail_views"][0]["tabs"].append({"label": "Board", "type": "custom"})
        doc["detail_views"][0]["tabs"].append(
            {"code": "summary2", "type": "summary", "sections": [{"type": "custom", "title": "Risk"}]}
        )
        n = len(doc["detail_views"][0]["tabs"])
        paths = custom_screens(doc)
        self.assertIn(f"/detail_views/@vendor_360/tabs/{n - 2}", paths)
        self.assertIn("/detail_views/@vendor_360/tabs/@summary2/sections/0", paths)

    def test_a_failed_run_reads_as_one_line(self):
        out = format_check([{"path": DASHBOARD, "role": "Finance", "ok": False, "error": "boom"}])
        self.assertIn("1 problem(s)", out)
        self.assertIn(f"✗ {DASHBOARD} as Finance: boom", out)


class EditChecksTests(PreviewProbeTestBase):
    def test_an_edit_to_a_custom_screen_reports_what_it_drew(self):
        bench = self.bench()
        out = bench.set(f"{DASHBOARD}/title", "Home")
        self.assertIn("Custom screens this edit changed", out)
        self.assertIn("KPI tiles: Open POs 8", out)
        self.assertEqual(self.probe.calls, [[DASHBOARD]])

    def test_an_edit_elsewhere_runs_nothing(self):
        bench = self.bench()
        crud = next(p["code"] for p in self.doc["pages"] if p.get("type") == "crud")
        out = bench.set(f"/pages/@{crud}/title", "All of them")
        self.assertNotIn("Custom screens", out)
        self.assertEqual(self.probe.calls, [])

    def test_a_data_edit_reports_only_the_screens_it_broke(self):
        bench = self.bench()
        out = bench.set("/modules/0/name", "Renamed")
        self.assertEqual(self.probe.calls, [None])  # every screen, once
        self.assertNotIn("broke", out)
        self.probe.broken.add(DASHBOARD)
        out = bench.set("/modules/0/name", "Renamed again")
        self.assertIn("This edit broke custom screens", out)
        self.assertIn(f"✗ {DASHBOARD}", out)

    def test_an_unsketched_screen_is_called_out_as_not_done(self):
        doc = copy.deepcopy(self.doc)
        next(p for p in doc["pages"] if p["code"] == "dashboard").pop("preview")
        bench = self.bench(doc)
        out = bench.set(f"{DASHBOARD}/text", "KPIs and a chart.")
        self.assertIn(f"NOT DONE: {DASHBOARD} has no `preview` sketch", out)
        self.assertIn("Changing `text` changes nothing they can see", out)
        self.assertNotIn("NOT DONE", self.bench().set(f"{DASHBOARD}/title", "Home"))

    def test_a_probe_failure_never_blocks_the_edit(self):
        bench = self.bench()

        def boom(*a, **k):
            raise ProbeError("Chromium is missing")

        self.probe.check = boom
        out = bench.set(f"{DASHBOARD}/title", "Home")
        self.assertTrue(out.startswith("Done:"))
        self.assertIn("could not be checked: Chromium is missing", out)

    def test_without_a_probe_there_are_no_preview_tools(self):
        names = {name for name, *_ in tool_specs(self.bench(probe=False))}
        self.assertNotIn("preview_look", names)
        names = {name for name, *_ in tool_specs(self.bench())}
        self.assertTrue({"preview_check", "preview_look"} <= names)


class LookTests(PreviewProbeTestBase):
    def test_a_look_returns_the_screenshot_and_is_remembered(self):
        bench = self.bench()
        res = bench.preview_look(DASHBOARD)
        kinds = [c["type"] for c in res["content"]]
        self.assertEqual(kinds, ["image", "text"])
        self.assertEqual(res["content"][0]["data"], PNG)
        self.assertIn("KPI tiles", res["content"][1]["text"])
        self.assertEqual(self.emitted[-1], {"sketch_looks": {DASHBOARD: bench._screens[DASHBOARD]}})

    def test_a_look_accepts_an_index_path(self):
        index = next(i for i, p in enumerate(self.doc["pages"]) if p["code"] == "dashboard")
        self.bench().preview_look(f"/pages/{index}")
        self.assertIn(DASHBOARD, self.emitted[-1]["sketch_looks"])

    def test_only_custom_screens_can_be_looked_at(self):
        crud = next(p["code"] for p in self.doc["pages"] if p.get("type") == "crud")
        with self.assertRaises(ToolRefused) as refused:
            self.bench().preview_look(f"/pages/@{crud}")
        self.assertIn("No custom page", str(refused.exception))

    def test_looks_are_capped_per_turn(self):
        bench = self.bench()
        self.probe.looks = SpecWorkbench.MAX_LOOKS
        with self.assertRaises(ToolRefused):
            bench.preview_look(DASHBOARD)


class AutoLookTests(PreviewProbeTestBase):
    """An edit that changes a sketch comes back with a screenshot of the screen."""

    def call(self, bench, name, args):
        fn = next(f for n, _, _, f in tool_specs(bench) if n == name)
        return asyncio.run(make_handler(bench, fn)(args))

    def test_an_edit_to_a_sketch_comes_with_its_screenshot(self):
        bench = self.bench()
        res = self.call(bench, "spec_set", {"path": f"{DASHBOARD}/title", "value": "Home"})
        self.assertEqual([c["type"] for c in res["content"]], ["image", "text"])
        self.assertEqual(res["content"][0]["data"], PNG)
        self.assertIn(f"Screenshot attached of {DASHBOARD}", res["content"][1]["text"])
        self.assertEqual(bench.sketch_looks[DASHBOARD], bench._screens[DASHBOARD])
        self.assertEqual(bench.take_images(), [])  # sent once

    def test_a_screen_that_fails_is_not_screenshotted(self):
        bench = self.bench()
        self.probe.broken.add(DASHBOARD)
        res = self.call(bench, "spec_set", {"path": f"{DASHBOARD}/title", "value": "Home"})
        self.assertEqual([c["type"] for c in res["content"]], ["text"])
        self.assertEqual(self.probe.looks, 0)

    def test_edits_elsewhere_take_no_screenshot(self):
        bench = self.bench()
        self.call(bench, "spec_set", {"path": "/modules/0/name", "value": "Renamed"})
        crud = next(p["code"] for p in self.doc["pages"] if p.get("type") == "crud")
        self.call(bench, "spec_set", {"path": f"/pages/@{crud}/title", "value": "All"})
        self.assertEqual(self.probe.looks, 0)

    def test_screens_already_looked_at_are_not_screenshotted_again(self):
        bench = self.bench()
        bench.set(f"{DASHBOARD}/title", "Home")
        self.assertEqual(self.probe.looks, 1)
        bench.take_images()
        bench.set("/modules/0/name", "Renamed")  # runs every screen, changes none
        self.assertEqual(self.probe.looks, 1)

    def test_the_screenshot_makes_the_screen_ready(self):
        bench = self.bench()
        bench.preview_look(CHECKLIST)
        bench.set(f"{DASHBOARD}/title", "Home")
        self.assertIn("Marked ready", bench.mark_ready("done"))

    def test_a_warning_is_not_a_pass(self):
        run = {"path": DASHBOARD, "role": "Finance", "ok": True, "draws": ["board"], "warnings": ["x.y is empty"]}
        self.assertTrue(format_result(run).startswith(f"⚠ {DASHBOARD}"))
        self.assertTrue(format_result({**run, "warnings": []}).startswith(f"✓ {DASHBOARD}"))


class ContractNudgeTests(PreviewProbeTestBase):
    """An edit to custom work says NOT DONE while a contract is missing, so the user never has to ask."""

    def test_an_edit_to_a_page_lists_the_missing_contracts(self):
        doc = copy.deepcopy(self.doc)
        next(p for p in doc["pages"] if p["code"] == "dashboard").pop("acceptance")
        out = self.bench(doc, probe=False).set(f"{DASHBOARD}/title", "Home")
        self.assertIn("NOT DONE: these custom parts have no contract yet", out)
        self.assertIn(f"- {DASHBOARD}: acceptance", out)

    def test_nothing_missing_nothing_said(self):
        out = self.bench(probe=False).set(f"{DASHBOARD}/title", "Home")
        self.assertNotIn("no contract", out)

    def test_an_edit_elsewhere_says_nothing(self):
        doc = copy.deepcopy(self.doc)
        next(p for p in doc["pages"] if p["code"] == "dashboard").pop("acceptance")
        out = self.bench(doc, probe=False).set("/app/name", "Renamed")
        self.assertNotIn("no contract", out)


class ApprovalGateTests(PreviewProbeTestBase):
    """Approving (Build) refuses what spec_mark_ready would, whichever model ran the interview."""

    def test_the_example_is_finished(self):
        self.assertEqual(unfinished_custom_work(self.template.example_yaml), [])

    def test_an_unsketched_screen_or_missing_contract_blocks_the_build(self):
        doc = copy.deepcopy(self.doc)
        page = next(p for p in doc["pages"] if p["code"] == "dashboard")
        page.pop("preview")
        page.pop("acceptance")
        found = {(i["path"], i["message"][:20]) for i in unfinished_custom_work(yaml.safe_dump(doc))}
        self.assertIn((DASHBOARD, "Custom screen with n"), found)
        self.assertIn((DASHBOARD, "Missing acceptance: "), found)


class ReadyGateTests(PreviewProbeTestBase):
    def test_ready_wants_a_look_at_every_custom_screen(self):
        bench = self.bench()
        with self.assertRaises(ToolRefused) as refused:
            bench.mark_ready("done")
        self.assertIn("look at each custom screen", str(refused.exception))
        bench.preview_look(DASHBOARD)
        bench.preview_look(CHECKLIST)
        self.assertIn("Marked ready", bench.mark_ready("done"))

    def test_a_look_counts_until_the_screen_changes(self):
        bench = self.bench()
        bench.preview_look(DASHBOARD)
        bench.preview_look(CHECKLIST)
        self.probe.looks = SpecWorkbench.MAX_LOOKS  # no screenshot comes with the edit
        bench.set(f"{DASHBOARD}/title", "Home")
        with self.assertRaises(ToolRefused) as refused:
            bench.mark_ready("done")
        self.assertIn(DASHBOARD, str(refused.exception))
        self.assertNotIn(CHECKLIST, str(refused.exception))

    def test_looks_from_earlier_turns_count(self):
        looks = SpecWorkbench(self.template.example_yaml, self.template, emit=lambda e: None)._screens
        self.assertIn("Marked ready", self.bench(looks=looks).mark_ready("done"))

    def test_ready_is_refused_while_a_screen_fails(self):
        bench = self.bench()
        bench.preview_look(DASHBOARD)
        bench.preview_look(CHECKLIST)
        self.probe.broken.add(CHECKLIST)
        with self.assertRaises(ToolRefused) as refused:
            bench.mark_ready("done")
        self.assertIn("error or a blank", str(refused.exception))

    def test_without_a_probe_the_gates_are_skipped(self):
        self.assertIn("Marked ready", self.bench(probe=False).mark_ready("done"))


@unittest.skipUnless(playwright_available(), "Playwright is not installed")
class HeadlessPreviewTests(PreviewProbeTestBase):
    """The real preview page in headless Chromium."""

    def setUp(self):
        super().setUp()
        from zango.apps.shared.app_templates.services.builder import compose

        self.real = PreviewProbe(compose(self.version))
        self.addCleanup(self.real.close)

    def run_check(self, text, paths=None):
        try:
            return self.real.check(text, paths)
        except ProbeError as exc:  # Chromium itself not installed
            if "playwright install" in str(exc) or "Executable doesn't exist" in str(exc):
                self.skipTest(str(exc))
            raise

    def test_the_example_sketches_draw_for_every_role(self):
        res = self.run_check(self.template.example_yaml)
        self.assertIsNone(res["parse_error"])
        self.assertTrue(res["results"])
        self.assertEqual([r for r in res["results"] if not r["ok"]], [])
        dash = next(r for r in res["results"] if r["path"] == DASHBOARD)
        self.assertTrue(any(d.startswith("KPI tiles") for d in dash["draws"]))

    def test_a_broken_sketch_reports_its_error(self):
        broken = self.template.example_yaml.replace("preview: |", "preview: |\n      nope();", 1)
        res = self.run_check(broken, [DASHBOARD])
        self.assertFalse(res["results"][0]["ok"])
        self.assertIn("nope is not defined", res["results"][0]["error"])

    def test_a_field_the_demo_data_never_fills_is_called_out(self):
        doc = copy.deepcopy(self.doc)
        page = next(p for p in doc["pages"] if p["code"] == "dashboard")
        vendor = next(e for m in doc["modules"] for e in m.get("entities") or [] if e["code"] == "vendor")
        vendor["fields"].append({"site_photo": {"type": "image", "label": "Site photo"}})
        page["preview"] = (
            "const rows = ctx.rows('vendor');"
            "return ctx.ui.list('Photos', rows.map(r => ({ title: ctx.fmt(r, 'legal_name'), subtitle: r.site_photo || 'none' })));"
        )
        run = self.run_check(yaml.safe_dump(doc, sort_keys=False), [DASHBOARD])["results"][0]
        self.assertTrue(run["ok"], run)
        self.assertIn("vendor.site_photo is empty on all", " ".join(run["warnings"]))
        self.assertFalse([w for w in run["warnings"] if "legal_name" in w])

    def test_a_user_field_named_after_a_role_holds_that_roles_users(self):
        from playwright.sync_api import sync_playwright

        from zango.apps.shared.app_templates.services.builder import compose

        doc = copy.deepcopy(self.doc)
        role = next(r["name"] for r in doc["roles"] if " " in r["name"])  # a two-word role
        key = "assigned_" + role.lower().replace(" ", "_")
        vendor = next(e for m in doc["modules"] for e in m.get("entities") or [] if e["code"] == "vendor")
        vendor["fields"].append({key: {"type": "link", "to": "app_user", "label": "Assigned"}})
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.route("**/*", lambda r: r.abort())
            page.set_content(compose(self.version))
            out = page.evaluate(
                "([y, role, key]) => { window.zangoLoad(y); "
                "return { users: S.users[role], values: S.db.vendor.map(r => r[key]) }; }",
                [yaml.safe_dump(doc, sort_keys=False), role, key],
            )
            browser.close()
        filled = [v for v in out["values"] if v]
        self.assertTrue(filled)
        self.assertTrue(set(filled) <= set(out["users"]), (filled, out["users"]))

    def test_a_look_is_a_png_of_that_screen(self):
        self.run_check(self.template.example_yaml)
        res = self.real.look(self.template.example_yaml, CHECKLIST)
        self.assertTrue(res["show"]["ok"])
        self.assertTrue(base64.b64decode(res["png"]).startswith(b"\x89PNG"))


@unittest.skipUnless(playwright_available(), "Playwright is not installed")
class PointingTests(PreviewProbeTestBase):
    """What the user can point at in the preview names a real place in the YAML."""

    WALK = """y => {
        window.zangoLoad(y);
        const paths = new Set();
        const grab = () => document.querySelectorAll('[data-zas-path]').forEach(e => paths.add(e.dataset.zasPath));
        for (const role of S.M.roles.map(r => r.name)) {
            ZAS_GOTO({ role });
            for (const p of Object.values(S.M.pages)) {
                if (!canPage(p)) continue;
                ZAS_GOTO({ role, page: p.code });
                grab();
                if (p.type === 'crud') {
                    const E = S.M.ents[p.entity];
                    if (E.form.create) { openCreate(E, {}); grab(); closeModal(); }
                    (p.views || []).forEach((v, i) => { S.views[p.code] = i; render(); grab(); });
                }
                if (p.type === 'detail') {
                    const dv = S.M.dvs[p.detail_view];
                    dv.tabs.forEach(t => { if (t.code) { ZAS_GOTO({ role, page: p.code, record: S.route.id ? { id: S.route.id } : null, tab: { code: t.code } }); grab(); } });
                }
            }
        }
        return [...paths];
    }"""

    def test_every_path_the_preview_draws_resolves_in_the_spec(self):
        import re

        from playwright.sync_api import sync_playwright

        from zango.apps.shared.app_templates.services.builder import compose
        from zango.apps.shared.app_templates.services.spec import document, yamlio

        html = compose(self.version)
        text = self.template.example_yaml
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page()
                page.route("**/*", lambda r: r.abort())
                page.set_content(html)
                paths = page.evaluate(self.WALK, text)
                browser.close()
        except Exception as exc:  # noqa: BLE001 - Chromium itself not installed
            if re.search(r"Executable doesn't exist|playwright install", str(exc)):
                self.skipTest(str(exc))
            raise
        doc = yamlio.load_rt(text)
        self.assertGreater(len(paths), 40)
        kinds = {re.sub(r"/@[^/]+|/\d+", "", p) for p in paths}
        for kind in ("/roles/menu", "/pages", "/detail_views/header/facts", "/detail_views/stats",
                     "/detail_views/tabs", "/modules/entities/fields", "/modules/entities/table/columns"):
            self.assertIn(kind, kinds)
        unresolved = []
        for path in paths:
            try:
                document.get(doc, path)
            except Exception as exc:  # noqa: BLE001
                unresolved.append(f"{path}: {exc}")
        self.assertEqual(unresolved, [])
