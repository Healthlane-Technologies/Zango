"""The build reproduces the approved preview.

sample_management_mrs: the dashboard sketch drew a gradient banner and a donut as raw HTML. The kit
outline did not show them, so the agent never opened the screenshot. Design lint rejected the
donut's inline background, so the agent removed it, and the single look came after the fix rounds,
on a stale screenshot, with no second look. Now:
  1. an approved slot may use its sketch's colours and inline styles (and no others);
  2. the bundle tells the agent to read the screenshot and sketch first, and flags hand-drawn parts;
  4. the look repeats, re-shot after every change, until the agent changes nothing.
"""

import json
import shutil
import sys
import tempfile
import unittest

from pathlib import Path
from unittest import mock

from zango.apps.agent_mode import approval_bundle
from zango.apps.agent_mode.studio_build import LayerResult, StudioBuild
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir


SCRIPTS = Path(studio_plugin_dir()) / "skills" / "zango-app-studio" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from zas_test import design  # noqa: E402


SKETCH = """const hero = `<div style="background:linear-gradient(135deg,#312e81,#4F46E5);color:#fff">x</div>`;
const donut = `<div style="background:conic-gradient(#0d9488 0% 40%, rgb(245, 158, 11) 40% 100%)"></div>`;
return ui.stack(hero, ui.kpis([{ label: 'Open', value: 1 }]), donut);
"""


class Workspace(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp(prefix="fidelity-"))
        self.addCleanup(shutil.rmtree, self.ws, True)
        bundle = self.ws / ".zas" / "bundle" / "screens" / "pages.dashboard"
        bundle.mkdir(parents=True)
        (bundle / "sketch.js").write_text(SKETCH)
        (self.ws / "frontend" / "src" / "custom" / "slots").mkdir(parents=True)
        holes = [
            {"id": "H-01", "kind": "custom_page", "where": "pages.dashboard",
             "bundle": ".zas/bundle/screens/pages.dashboard/",
             "target": "frontend/src/custom/slots/Overview.tsx::Overview"},
            {"id": "H-02", "kind": "custom_panel", "where": "detail_views.v.sidebar[0]",
             "target": "frontend/src/custom/slots/Plain.tsx::Plain"},
        ]
        (self.ws / ".zas" / "spec.resolved.json").write_text(json.dumps({"roles": {}, "holes": holes}))

    def slot(self, name, body):
        (self.ws / "frontend" / "src" / "custom" / "slots" / name).write_text(body)

    def lint(self):
        Dx = design.D(str(self.ws))
        design.g_lint(Dx)
        return next(r for r in Dx.results if r["id"] == "design.lint")


class ApprovedStyleLintTests(Workspace):
    def test_an_approved_slot_may_use_its_sketchs_colours_and_inline_styles(self):
        self.slot("Overview.tsx", '// zas:hole H-01 · pages.dashboard\n'
                  'const hero = { background: "linear-gradient(135deg, #312E81, var(--brand))", color: "#ffffff" };\n'
                  'const donut = { background: "conic-gradient(#0d9488 0 40%, rgb(245,158,11) 0)" };\n'
                  'export default () => <div style={{ background: "#312e81" }} />;\n')
        self.assertEqual(self.lint()["status"], "pass")

    def test_a_colour_the_sketch_does_not_use_is_rejected(self):
        self.slot("Overview.tsx", '// zas:hole H-01 · pages.dashboard\n'
                  'export default () => <div style={{ background: "#ff0000" }} />;\n')
        lint = self.lint()
        self.assertEqual(lint["status"], "fail")
        self.assertIn("`#ff0000` is not in .zas/bundle/screens/pages.dashboard/sketch.js", lint["detail"])

    def test_a_slot_without_an_approved_look_keeps_the_strict_rules(self):
        self.slot("Plain.tsx", '// zas:hole H-02 · detail_views.v.sidebar[0]\n'
                  'export default () => <div style={{ background: "#312e81" }} />;\n')
        detail = self.lint()["detail"]
        self.assertIn("Plain.tsx:2: colour literal", detail)
        self.assertIn("inline `background` style", detail)

    def test_an_unmarked_helper_may_use_the_approved_colours(self):
        self.slot("Donut.tsx", 'export const Donut = () => <div style={{ background: "#0d9488" }} />;\n')
        self.assertEqual(self.lint()["status"], "pass")

    def test_css_files_are_still_rejected(self):
        self.slot("Overview.module.css", ".x { color: #0d9488 }\n")
        self.assertIn("stylesheet in src/custom", self.lint()["detail"])


class BundleTests(unittest.TestCase):
    def test_markup_beside_kit_calls_is_detected(self):
        self.assertTrue(approval_bundle.has_markup(SKETCH))
        self.assertFalse(approval_bundle.has_markup("return ui.stack(ui.kpis([{ label: 'a<b' }]), ui.list('x', rows));"))

    def test_index_asks_for_the_screenshot_first_and_names_hand_drawn_parts(self):
        text = approval_bundle.index_md({"probe": "ok", "screens": [{
            "path": "/pages/@dashboard", "folder": "screens/pages.dashboard", "title": "Overview",
            "sketched": True, "markup": True, "variants": [{
                "roles": ["Admin"], "shot": "screens/pages.dashboard/shot.admin.png", "record": None,
                "hand_written": False, "tree": [{"kit": "kpis", "items": ["Open"]}]}]}]})
        self.assertIn("Before you write a screen's slot, Read its screenshot(s) and its `sketch.js`", text)
        self.assertIn("Has hand-drawn parts", text)
        self.assertNotIn("Open a screenshot when", text)


class LookRoundTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="looks-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        ws = self.root / "ws"
        (ws / ".zas").mkdir(parents=True)
        (ws / "frontend" / "src" / "custom").mkdir(parents=True)
        (ws / ".zas" / "parity_looks.json").write_text(json.dumps([
            {"screen": "/pages/@dashboard", "role": "Admin",
             "approved": ".zas/bundle/screens/pages.dashboard/shot.admin.png",
             "built": ".zas/screens/parity/pages.dashboard.admin.png"}]))
        self.build = StudioBuild(skill_dir=str(self.root), workspace=str(ws), spec_path=str(self.root / "s.yaml"),
                                 run_dir=str(self.root), base_dir=str(self.root), app_name="demo")
        self.slot = ws / "frontend" / "src" / "custom" / "Overview.tsx"
        self.messages = []
        self.shoots = []

    def agent(self, edits):
        """An agent that edits the slot in the first ``edits`` rounds, then changes nothing."""
        def resume(message):
            self.messages.append(message)
            if len(self.messages) <= edits:
                self.slot.write_text(f"// round {len(self.messages)}\n")
            return True
        return resume

    def run_looks(self, edits, rounds=2, stale=False):
        layers = {"design": LayerResult(name="design", status="pass")}

        def verify(emit=None, only=None, **kw):
            self.shoots.append(only)
            return {"design": LayerResult(name="design", status="pass")}

        with mock.patch("zango.apps.agent_mode.studio_build.look_rounds", return_value=rounds), \
                mock.patch.object(StudioBuild, "verify", side_effect=verify), \
                mock.patch.object(StudioBuild, "bring_up", return_value=True) as bring_up:
            ok = self.build.look_rounds(layers, {}, self.agent(edits), None, stale, set(), set())
        return ok, bring_up

    def test_an_agent_that_changes_nothing_ends_the_looks(self):
        ok, bring_up = self.run_looks(edits=0)
        self.assertTrue(ok)
        self.assertEqual(len(self.messages), 1)
        bring_up.assert_not_called()
        self.assertEqual(self.shoots, [])

    def test_each_change_is_rebuilt_and_reshot_before_the_next_look(self):
        ok, bring_up = self.run_looks(edits=1)
        self.assertEqual(len(self.messages), 2)
        self.assertEqual(bring_up.call_count, 1)
        self.assertEqual(len(self.shoots), 1)
        self.assertIn("parity", self.shoots[0]["design"])
        self.assertIn("design_lint", self.shoots[0])
        self.assertIn("Look 1 of 2", self.messages[0])
        self.assertIn("Look 2 of 2", self.messages[1])
        self.assertIn("last look", self.messages[1])

    def test_the_rounds_are_capped(self):
        self.run_looks(edits=5, rounds=2)
        self.assertEqual(len(self.messages), 2)

    def test_stale_shots_are_retaken_before_the_first_look(self):
        # Regression: the look showed a screenshot from before the last fix round's rebuild.
        self.run_looks(edits=0, stale=True)
        self.assertEqual(len(self.shoots), 1)
        self.assertIn("parity", self.shoots[0]["design"])

    def test_the_parity_gaps_are_the_looks_checklist(self):
        gap = {"id": "design.parity.pages.dashboard.admin",
               "detail": 'panel "Product mix": approved has a chart (donut, ring or SVG), built has none. '
                         "Compare a.png with b.png."}
        text = self.build.look_digest(1, 2, [gap])
        self.assertIn('- `design.parity.pages.dashboard.admin`: panel "Product mix": approved has a chart', text)
        self.assertNotIn("Compare a.png", text)

    def test_the_look_names_the_sketch_and_allows_its_styles(self):
        text = self.build.look_digest(1, 2)
        self.assertIn("sketch `.zas/bundle/screens/pages.dashboard/sketch.js`", text)
        self.assertIn("colours, gradients, charts and inline styles are allowed", text)
        self.assertIn("**matches** or **differs**", text)


# Captured from sample_management_mrs: the approved preview and the built dashboard (kit_tree.js).
APPROVED_LOOK = [
    {"kit": "markup", "text": "2026-10-16 Sample programme at a glance 263 units in use across 12 requests",
     "look": ["filled", "gradient"]},
    {"kit": "kpis", "items": ["Waiting for approval", "Units acknowledged"], "look": []},
    {"kit": "panel", "title": "Request pipeline", "look": ["accent"]},
    {"kit": "panel", "title": "Top MRs by units", "look": ["avatar"]},
    {"kit": "panel", "title": "Product mix", "look": ["chart"]},
]
BUILT_FLAT = [
    {"kit": "markup", "text": "Sample management overview", "look": []},
    {"kit": "markup", "text": "2026-10-16Sample programme at a glance54 units in use across 38 requests", "look": []},
    {"kit": "kpis", "items": ["Waiting for approval", "Units acknowledged"], "look": []},
    {"kit": "panel", "title": "Request pipeline", "look": []},
    {"kit": "panel", "title": "Top MRs by units", "look": []},
    {"kit": "panel", "title": "Product mix", "look": []},
]


class LookParityTests(unittest.TestCase):
    def test_a_flattened_port_names_each_lost_feature(self):
        self.assertEqual(design.parity_diff(APPROVED_LOOK, BUILT_FLAT), [
            'panel "Request pipeline": approved has coloured accent borders, built has none',
            'panel "Top MRs by units": approved has avatar circles, built has none',
            'panel "Product mix": approved has a chart (donut, ring or SVG), built has none',
            'hand-drawn block "2026-10-16 Sample programme at a glance …": approved has a gradient background, built has none',
        ])

    def test_a_faithful_port_passes_whatever_the_numbers(self):
        built = json.loads(json.dumps(BUILT_FLAT))
        built[1]["look"] = ["filled", "gradient"]
        for n, f in zip(built[3:], (["accent"], ["avatar", "filled"], ["chart"])):
            n["look"] = f
        self.assertEqual(design.parity_diff(APPROVED_LOOK, built), [])

    def test_a_hand_drawn_block_with_no_counterpart_is_missing(self):
        built = [n for n in BUILT_FLAT if "glance" not in n.get("text", "")]
        self.assertIn('missing hand-drawn block "2026-10-16 Sample programme at a glance …"',
                      design.parity_diff(APPROVED_LOOK, built))

    def test_a_bundle_without_looks_compares_structure_only(self):
        old = [{k: v for k, v in n.items() if k != "look"} for n in APPROVED_LOOK if n["kit"] != "markup"]
        self.assertEqual(design.parity_diff(old, BUILT_FLAT), [])

    def test_the_outline_shows_hand_drawn_blocks_and_looks(self):
        lines = approval_bundle._outline(APPROVED_LOOK)
        self.assertEqual(lines[0], '- hand-drawn block "2026-10-16 Sample programme at a glance 263 units …" [look: filled, gradient]')
        self.assertIn('- panel "Product mix" [look: chart]', lines)

    def test_hand_drawn_means_no_kit_blocks(self):
        self.assertFalse(approval_bundle._has_kit_blocks(APPROVED_LOOK[:1]))
        self.assertTrue(approval_bundle._has_kit_blocks(APPROVED_LOOK))
        self.assertFalse(approval_bundle._has_kit_blocks([]))


if __name__ == "__main__":
    unittest.main()
