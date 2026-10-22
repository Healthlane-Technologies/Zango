"""The approval bundle (spec-to-build F2): what the user approved, per custom screen, for the build.

agent_mode/approval_bundle.py writes .zas/bundle/ at build prepare: each custom screen's sketch,
contract, kit tree per distinct structure, and screenshots. The workbench-style tests use a stand-in
probe; the last class runs the real preview headless when Playwright is installed.
"""

import base64
import json
import re
import tempfile
import unittest

from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import yaml

from zango.apps.agent_mode.approval_bundle import index_md, screen_folder, write_bundle
from zango.apps.agent_mode.preview_probe import ProbeError, playwright_available
from zango.apps.agent_mode.studio_build import StudioBuild
from zango.apps.shared.app_templates.seed import PACKS_DIR


PACK = PACKS_DIR / "zango_app"
EXAMPLE = (PACK / "example.yaml").read_text()
DASHBOARD = "/pages/@dashboard"
CHECKLIST = "/detail_views/@vendor_360/sidebar/2"
PNG = base64.b64encode(b"\x89PNG fake").decode()
TREE = [{"kit": "kpis", "items": ["Open POs"]}, {"kit": "bars", "title": "PO value by month"}]


class FakeProbe:
    def __init__(self):
        self.captured = []

    def sketches(self, yaml_text):
        return {"parse_error": None, "sketches": []}

    def capture(self, yaml_text, path, kit_tree_js, max_variants=3):
        self.captured.append(path)
        assert "data-zas-kit" in kit_tree_js
        if path == DASHBOARD:
            return {"kind": "page", "variants": [
                {"roles": ["Procurement Manager", "Procurement Executive"], "record": None, "tree": TREE,
                 "run": {"draws": ["KPI tiles: Open POs 8"]}, "png": PNG}], "in_page": None}
        return {"kind": "panel", "variants": [
            {"roles": ["Procurement Manager"], "record": {"entity": "vendor", "id": 1, "label": "Pioneer"},
             "tree": [], "run": {"excerpt": "3 of 5 done"}, "png": PNG}], "in_page": PNG}


VIEWS_SPEC = """
app: {code: demo, name: Demo}
pages:
  - {code: tasks, type: crud, title: Tasks, entity: task, views: [{type: table}, {type: kanban, label: Board}]}
  - {code: notes, type: crud, title: Notes, entity: note}
"""
LAYOUT = {"switcher": "toolbar", "shell": {"sidebar": True, "brand": "Demo", "brand_role": "Admin",
                                           "user_in_sidebar": True, "topbar": True, "topbar_title": "Tasks",
                                           "topbar_actions": 2}}


class LayoutProbe(FakeProbe):
    def __init__(self):
        super().__init__()
        self.layouts = []

    def capture_layout(self, yaml_text, kind, page=None, view=0):
        self.layouts.append((kind, page, view))
        return {"role": "Admin", "page": page or "tasks", "layout": LAYOUT, "png": PNG}


class StandardScreenTests(unittest.TestCase):
    """List pages with views and the app shell get screenshots too (they were missing, so a built
    list page and shell could differ from the approved preview without the agent ever seeing it)."""

    def setUp(self):
        self.out = Path(tempfile.mkdtemp())

    def test_each_view_of_a_page_with_a_switcher_and_the_shell_are_shot(self):
        probe = LayoutProbe()
        manifest = write_bundle(VIEWS_SPEC, self.out, probe=probe)
        self.assertEqual(probe.layouts, [("view", "tasks", 0), ("view", "tasks", 1), ("shell", None, 0)])
        paths = [s["path"] for s in manifest["screens"]]
        self.assertEqual(paths, ["/pages/@tasks/views/0", "/pages/@tasks/views/1", "/shell"])
        board = manifest["screens"][1]
        self.assertEqual((board["kind"], board["view_type"], board["layout"]["switcher"]), ("view", "kanban", "toolbar"))
        self.assertTrue((self.out / board["variants"][0]["shot"]).is_file())
        self.assertEqual(json.loads((self.out / "screens" / "shell" / "layout.json").read_text())["role"], "Admin")

    def test_the_index_names_the_lever_for_each_standard_screen(self):
        write_bundle(VIEWS_SPEC, self.out, probe=LayoutProbe())
        index = (self.out / "index.md").read_text()
        self.assertIn("# Standard screens", index)
        self.assertIn('makeViewsPage("tasks", { … }, { switcher: "toolbar" })', index)
        self.assertIn("frontend/src/custom/views/tasks_kanban.tsx", index)
        self.assertIn("navbarConfig.customLogo", index)
        self.assertIn('data-zas="shell-user"', index)
        self.assertIn("2 icon button(s)", index)

    def test_a_probe_without_layout_capture_still_lists_the_screens(self):
        manifest = write_bundle(VIEWS_SPEC, self.out, probe=FakeProbe())
        shell = next(s for s in manifest["screens"] if s["kind"] == "shell")
        self.assertEqual(shell["variants"], [])


class FolderTests(unittest.TestCase):
    def test_a_folder_is_the_holes_spec_path(self):
        self.assertEqual(screen_folder("/pages/@dashboard"), "pages.dashboard")
        self.assertEqual(screen_folder(CHECKLIST), "detail_views.vendor_360.sidebar.2")
        self.assertEqual(screen_folder("/detail_views/@v/tabs/@risk/sections/0"), "detail_views.v.tabs.risk.sections.0")


class WriteBundleTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())

    def test_without_a_probe_the_sketches_and_contracts_still_go(self):
        manifest = write_bundle(EXAMPLE, self.out)
        self.assertTrue(manifest["probe"].startswith("unavailable"))
        dash = self.out / "screens" / "pages.dashboard"
        self.assertIn("ui.kpis(", (dash / "sketch.js").read_text())
        contract = json.loads((dash / "contract.json").read_text())
        self.assertTrue(contract["acceptance"])
        self.assertNotIn("preview", contract)
        index = (self.out / "index.md").read_text()
        self.assertIn("No screenshots or kit outlines", index)
        self.assertIn("## `/pages/@dashboard`", index)

    def test_each_structure_gets_a_view_and_a_screenshot(self):
        probe = FakeProbe()
        manifest = write_bundle(EXAMPLE, self.out, probe=probe)
        self.assertEqual(sorted(probe.captured), sorted([DASHBOARD, CHECKLIST]))
        dash = next(s for s in manifest["screens"] if s["path"] == DASHBOARD)
        self.assertEqual(dash["variants"][0]["roles"], ["Procurement Manager", "Procurement Executive"])
        self.assertEqual((self.out / dash["variants"][0]["shot"]).read_bytes(), base64.b64decode(PNG))
        view = json.loads((self.out / dash["variants"][0]["view"]).read_text())
        self.assertEqual(view["tree"], TREE)
        panel = next(s for s in manifest["screens"] if s["path"] == CHECKLIST)
        self.assertTrue(panel["variants"][0]["hand_written"])
        self.assertTrue((self.out / panel["in_page"]).is_file())
        index = (self.out / "index.md").read_text()
        self.assertIn('  - bars "PO value by month"', index)
        self.assertIn("hand-written markup (no kit blocks): port it from `sketch.js` with its styles", index)
        self.assertIn("In its 360 page:", index)

    def test_a_screen_that_cannot_be_captured_is_named_not_fatal(self):
        probe = FakeProbe()
        probe.capture = mock.Mock(side_effect=ProbeError("hung"))
        manifest = write_bundle(EXAMPLE, self.out, probe=probe)
        custom = [s for s in manifest["screens"] if s.get("kind") not in ("view", "shell")]
        self.assertTrue(custom and all(s.get("error") == "hung" for s in custom))
        self.assertIn("Could not capture: hung", (self.out / "index.md").read_text())

    def test_an_unsketched_screen_is_built_from_its_text(self):
        doc = yaml.safe_load(EXAMPLE)
        next(p for p in doc["pages"] if p["code"] == "dashboard").pop("preview")
        manifest = write_bundle(yaml.safe_dump(doc), self.out, probe=FakeProbe())
        dash = next(s for s in manifest["screens"] if s["path"] == DASHBOARD)
        self.assertFalse(dash["sketched"])
        self.assertEqual(dash["variants"], [])
        self.assertIn("No sketch: build from the contract's text.", index_md(manifest))


class HoleTextTests(unittest.TestCase):
    """spec_check points each custom screen's hole at its bundle folder (written before it runs)."""

    def run_check(self, probe):
        import subprocess
        import sys

        from zango.apps.shared.app_templates.services.generic import studio_plugin_dir

        ws = Path(tempfile.mkdtemp())
        spec = ws / "app_spec.yaml"
        spec.write_text(EXAMPLE)
        write_bundle(EXAMPLE, ws / ".zas" / "bundle", probe=probe)
        script = Path(studio_plugin_dir()) / "skills" / "zango-app-studio" / "scripts" / "spec_check.py"
        proc = subprocess.run([sys.executable, str(script), str(spec), "--workspace", str(ws), "--quiet"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        resolved = json.loads((ws / ".zas" / "spec.resolved.json").read_text())
        return {h["where"]: h for h in resolved["holes"]}, (ws / ".zas" / "holes.md").read_text()

    def test_custom_holes_name_their_approved_look(self):
        holes, md = self.run_check(FakeProbe())
        self.assertEqual(holes["pages.dashboard"]["bundle"], ".zas/bundle/screens/pages.dashboard/")
        row = next(line for line in md.splitlines() if "`pages.dashboard`" in line)
        self.assertIn("Approved look: `.zas/bundle/screens/pages.dashboard/`", row)
        panel = next(h for w, h in holes.items() if w.startswith("detail_views.vendor_360.sidebar"))
        self.assertIn("hand-drawn parts (raw HTML and styles in the sketch): port them, do not simplify them", panel["text"])
        self.assertNotIn("bundle", holes.get("pages.finance_home", {}))  # a declared dashboard is not custom

    def test_without_a_bundle_the_holes_are_as_before(self):
        import subprocess
        import sys

        from zango.apps.shared.app_templates.services.generic import studio_plugin_dir

        ws = Path(tempfile.mkdtemp())
        (ws / "app_spec.yaml").write_text(EXAMPLE)
        script = Path(studio_plugin_dir()) / "skills" / "zango-app-studio" / "scripts" / "spec_check.py"
        subprocess.run([sys.executable, str(script), str(ws / "app_spec.yaml"), "--workspace", str(ws), "--quiet"], check=True)
        self.assertNotIn("Approved look", (ws / ".zas" / "holes.md").read_text())


class StudioPrepareTests(unittest.TestCase):
    """StudioBuild writes the bundle into .zas/ and never fails the build over it."""

    def build(self):
        root = Path(tempfile.mkdtemp())
        spec = root / "app_spec.yaml"
        spec.write_text(EXAMPLE)
        (root / "ws" / ".zas").mkdir(parents=True)
        return StudioBuild(skill_dir=str(root / "skill"), workspace=str(root / "ws"), spec_path=str(spec),
                           run_dir=str(root), base_dir=str(root), app_name="demo")

    def test_the_bundle_lands_in_zas(self):
        b = self.build()
        with mock.patch("zango.apps.agent_mode.preview_probe.probe_for", return_value=None):
            manifest = b.write_bundle(SimpleNamespace(version="1.1.17"))
        self.assertEqual(manifest["template_version"], "1.1.17")
        self.assertTrue((b.zas_dir / "bundle" / "index.md").is_file())
        self.assertEqual(b.steps[-1].step, "studio:bundle")

    def test_a_failure_is_a_skipped_step(self):
        b = self.build()
        with mock.patch("zango.apps.agent_mode.approval_bundle.write_bundle", side_effect=RuntimeError("boom")), \
                mock.patch("zango.apps.agent_mode.preview_probe.probe_for", return_value=None):
            self.assertIsNone(b.write_bundle(SimpleNamespace(version="1")))
        self.assertIn("boom", b.steps[-1].skipped_reason)


@unittest.skipUnless(playwright_available(), "Playwright is not installed")
class HeadlessBundleTests(unittest.TestCase):
    def test_the_example_bundle_from_the_real_preview(self):
        from zango.apps.agent_mode.preview_probe import PreviewProbe

        html = (PACK / "builder" / "app-studio.html").read_text()
        html = html.replace("</body>", "<script>" + (PACK / "builder" / "adapter.js").read_text() + "</script></body>")
        probe = PreviewProbe(html)
        out = Path(tempfile.mkdtemp())
        try:
            manifest = write_bundle(EXAMPLE, out, probe=probe)
        except ProbeError as exc:
            if re.search(r"Executable doesn't exist|playwright install", str(exc)):
                self.skipTest(str(exc))
            raise
        finally:
            probe.close()
        self.assertEqual(manifest["probe"], "ok")
        dash = next(s for s in manifest["screens"] if s["path"] == DASHBOARD)
        self.assertEqual(dash["kind"], "page")
        self.assertEqual([n["kit"] for n in dash["variants"][0]["tree"]], ["kpis", "bars", "list"])
        self.assertTrue((out / dash["variants"][0]["shot"]).read_bytes().startswith(b"\x89PNG"))
        panel = next(s for s in manifest["screens"] if s["path"] == CHECKLIST)
        self.assertTrue(panel["variants"][0]["hand_written"])
        self.assertTrue((out / panel["in_page"]).read_bytes().startswith(b"\x89PNG"))
