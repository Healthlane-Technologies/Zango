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
