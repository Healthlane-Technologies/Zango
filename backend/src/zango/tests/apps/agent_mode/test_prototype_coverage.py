"""The YAML covers the approved prototype (open mode, spec_mark_ready).

The build follows the YAML, so whatever the prototype shows and the YAML leaves out is dropped: a
menu item, a column, a status tab, a section, a button. proto_landmarks reads each captured screen's
labels; prototype_coverage matches them against the YAML the screen maps to.
"""

import json
import sys
import tempfile
import unittest

from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from zango.apps.agent_mode import prototype_coverage as pc
from zango.apps.agent_mode.spec_tools import SpecWorkbench, ToolRefused
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir


SCRIPTS = Path(studio_plugin_dir()) / "skills" / "zango-app-studio" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import proto_landmarks as PL  # noqa: E402
import spec_check  # noqa: E402


NAV = """
<aside><nav>
  <a class="nav-item">Home <span class="cnt">3</span></a>
  <div class="nav-label">Lab</div>
  <a class="nav-item">Samples <span class="cnt">12</span></a>
  <a class="nav-item">Instruments</a>
  <div class="nav-label">Help</div>
  <a class="nav-item">Tour</a>
</nav></aside>
<header><button>New sample</button><button>RV Rosa Vance Lab lead</button></header>
"""

SAMPLES = NAV + """
<main><h1>Samples</h1>
  <button>Open 8</button><button>Due today 2</button>
  <table><thead><tr><th>Sample</th><th>Assay</th><th>Next step</th><th>Received</th></tr></thead>
  <tbody><tr><td>LAB-2026-0042</td><td>PCR</td><td><button>Assign</button></td><td>$1,200</td></tr></tbody></table>
</main>
"""

SAMPLE = NAV + """
<main><h1>Throat swab from Ward 4 east, second draw</h1>
  <button>Edit</button><button>Release result</button>
  <div role="tablist"><button role="tab">Overview</button><button role="tab">Results</button></div>
  <h3>Chain of custody</h3><dl><dt>Collected by</dt><dd>Rosa Vance</dd></dl>
</main>
"""

HOME = NAV + "<main><h1>Good morning, Rosa</h1><h2>Your queue</h2></main>"

MANIFEST = {
    "personas": {"rosa": {"name": "Rosa Vance"}, "omar": {"name": "Omar Diaz"}},
    "roles": {"rosa": "Lab lead", "omar": "Technician"},
    "screens": [
        {"id": "home", "title": "Home"},
        {"id": "samples", "title": "Samples", "group": "Lab"},
        {"id": "sample", "title": "Sample", "record": "samples", "sample": "s1"},
        {"id": "instruments", "title": "Instruments", "group": "Lab"},
        {"id": "tour", "title": "Tour", "group": "Help", "only": "prototype"},
    ],
}


def spec(**over):
    doc = {
        "roles": [
            {"name": "Lab lead", "menu": [
                {"page": "home"},
                {"group": "Lab", "items": [{"page": "samples"}, {"page": "instruments"}]},
            ]},
            {"name": "Technician", "menu": [
                {"page": "home"},
                {"group": "Lab", "items": [{"page": "samples"}, {"page": "instruments"}]},
            ]},
        ],
        "modules": [{"code": "lab", "entities": [{
            "code": "sample",
            "fields": [{"key": "assay", "label": "Assay"}, {"key": "received_on", "label": "Received"},
                       {"key": "collected_by", "label": "Collected by"}],
            "workflow": {"transitions": [{"key": "release", "label": "Release result"}]},
            "table": {"columns": [{"ref": {"label": "Sample"}}, {"assay": {}}, {"next_step": {"label": "Next step"}},
                                  {"received_on": {}}],
                      "quick_filters": [{"label": "Open"}, {"label": "Due today"}],
                      "row_actions": [{"key": "assign", "label": "Assign", "type": "edit"}]},
        }]}],
        "pages": [
            {"code": "home", "type": "dashboard", "title": "Home",
             "blocks": [{"table": {"title": "Your queue", "entity": "sample"}}]},
            {"code": "samples", "type": "crud", "title": "Samples", "entity": "sample"},
            {"code": "instruments", "type": "crud", "title": "Instruments", "entity": "sample"},
        ],
        "detail_views": [{
            "code": "sample_360", "hero": "sample",
            "header": {"actions": {"buttons": [{"key": "edit", "label": "Edit"}]}},
            "tabs": [{"code": "overview", "label": "Overview", "type": "summary",
                      "sections": [{"title": "Chain of custody"}]},
                     {"code": "results", "label": "Results", "type": "timeline"}],
        }],
        "prototype": {"screens": [
            {"id": "home", "maps": "/pages/@home"},
            {"id": "samples", "maps": "/pages/@samples"},
            {"id": "sample", "maps": "/detail_views/@sample_360"},
            {"id": "instruments", "maps": "/pages/@instruments"},
            {"id": "tour", "only": "prototype", "why": "Demo tour",
             "menu": {"group": "Help", "label": "Tour", "icon": "flag"}},
        ]},
    }
    doc.update(over)
    return doc


def write_bundle(root: Path, doms=None) -> Path:
    doms = doms or {"home": HOME, "samples": SAMPLES, "sample": SAMPLE, "instruments": SAMPLES, "tour": HOME}
    (root / "manifest.json").write_text(json.dumps(MANIFEST))
    screens = []
    for sid, html in doms.items():
        d = root / "screens" / sid
        d.mkdir(parents=True)
        roles = []
        for persona in MANIFEST["personas"]:
            (d / f"dom.{persona}.html").write_text(html)
            roles.append({"role": persona, "files": [f"dom.{persona}.html", f"shot.{persona}.png"]})
        screens.append({"id": sid, "roles": roles})
    (root / "capture.json").write_text(json.dumps({"probe": "ok", "screens": screens}))
    return root


class LandmarkTests(unittest.TestCase):
    def test_the_menu_keeps_groups_and_drops_counts(self):
        marks = PL.landmarks(SAMPLES)
        self.assertEqual(marks["menu"], [(None, "Home"), ("Lab", "Samples"), ("Lab", "Instruments"), ("Help", "Tour")])

    def test_columns_tabs_and_buttons_skip_record_data(self):
        marks = PL.landmarks(SAMPLES)
        self.assertEqual(marks["column"], ["Sample", "Assay", "Next step", "Received"])
        self.assertIn("Due today", marks["button"])
        self.assertNotIn("LAB-2026-0042", sum(marks.values(), []))
        detail = PL.landmarks(SAMPLE)
        self.assertEqual(detail["tab"], ["Overview", "Results"])
        self.assertEqual(detail["label"], ["Collected by"])
        self.assertEqual(detail["title"], [])  # a long record name is data, not copy


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bundle = write_bundle(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_spec_that_says_everything_has_no_gaps(self):
        result = pc.coverage(spec(), self.bundle)
        self.assertEqual(result["menu"], [])
        self.assertEqual(result["screens"], [])

    def test_a_dropped_column_status_tab_and_section_are_named(self):
        doc = spec()
        ent = doc["modules"][0]["entities"][0]
        ent["table"]["columns"] = ent["table"]["columns"][:2] + ent["table"]["columns"][3:]
        ent["table"]["quick_filters"] = [{"label": "Open"}]
        doc["detail_views"][0]["tabs"][0]["sections"] = []
        gaps = {s["id"]: s["gaps"] for s in pc.coverage(doc, self.bundle)["screens"]}
        self.assertEqual(gaps["samples"], {"column": ["Next step"], "button": ["Due today"]})
        self.assertEqual(gaps["sample"], {"heading": ["Chain of custody"]})
        self.assertNotIn("instruments", gaps)  # renders exactly like samples: checked once

    def test_menu_labels_groups_and_not_built_screens(self):
        doc = spec()
        doc["pages"][1]["title"] = "Sample queue"
        doc["prototype"]["screens"][4].pop("menu")
        menu = pc.coverage(doc, self.bundle)["menu"]
        self.assertIn(
            "menu (Lab lead): the prototype shows this role 'Samples' (group 'Lab'), 'Tour' (group 'Help'); "
            "the YAML menu doesn't have them",
            menu,
        )

    def test_each_persona_sees_exactly_its_roles_menu(self):
        # One menu drawn for every persona, while the requirements give the Technician less:
        # the preview must change, so the user approves what the build will show.
        doc = spec()
        doc["roles"][1]["menu"] = [{"group": "Lab", "items": [{"page": "samples"}]}]
        menu = pc.coverage(doc, self.bundle)["menu"]
        self.assertTrue(any(g.startswith("menu (Technician): the prototype shows this role 'Home'") for g in menu))
        # and a role whose YAML menu has more than its persona sees
        doc = spec()
        doc["roles"][0]["menu"].append({"page": "reports", "label": "Reports"})
        menu = pc.coverage(doc, self.bundle)["menu"]
        self.assertEqual(menu, ["menu (Lab lead): the YAML menu has 'Reports'; the prototype doesn't show them to this role"])

    def test_not_built_while_the_preview_still_shows_it_is_a_gap(self):
        # The user approves the preview as the app: what won't be built must leave the preview too.
        doc = spec()
        doc["prototype"]["screens"][2]["not_built"] = [{"text": "Release result", "why": "later"}]
        doc["modules"][0]["entities"][0]["workflow"]["transitions"] = []
        gaps = {s["id"]: s["gaps"] for s in pc.coverage(doc, self.bundle)["screens"]}
        self.assertEqual(gaps["sample"], {"still_shown": ["Release result"]})
        self.assertIn("the preview still shows: 'Release result'", pc.format_gaps(pc.coverage(doc, self.bundle)))

    def test_an_uploaded_pages_record_screen_is_rebuilt(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = write_bundle(Path(tmp))
            (bundle / "manifest.json").write_text(json.dumps({**MANIFEST, "source": "imported"}))
            gaps = {s["id"]: s["gaps"] for s in pc.coverage(spec(), bundle)["screens"]}
            self.assertIn("needs_rebuild", gaps["sample"])
            doc = spec()
            doc["prototype"]["screens"][2].update(rebuild=True, why="tracker and side panels")
            result = pc.coverage(doc, bundle)
        self.assertEqual(result["screens"], [])
        self.assertIn("Release result", result["rebuild"]["sample"]["button"])

    def test_rebuild_takes_labels_off_the_gaps(self):
        doc = spec()
        doc["prototype"]["screens"][1].update(rebuild=True, why="row layout")
        doc["modules"][0]["entities"][0]["table"]["columns"] = []
        result = pc.coverage(doc, self.bundle)
        self.assertNotIn("samples", [s["id"] for s in result["screens"]])
        self.assertIn("Next step", result["rebuild"]["samples"]["column"])

    def test_personas_and_shell_chrome_are_not_screen_copy(self):
        doc = spec()
        doc["pages"][0]["blocks"] = []
        gaps = {s["id"]: s["gaps"] for s in pc.coverage(doc, self.bundle)["screens"]}
        # "Good morning, Rosa" names a persona; "New sample" sits in the top bar on every screen
        self.assertEqual(gaps["home"], {"heading": ["Your queue"]})


    def test_a_heading_is_a_title_not_a_field_of_that_name(self):
        doc = spec()
        doc["detail_views"][0]["tabs"][0]["sections"] = [{"title": "Details", "fields": ["chain_of_custody"]}]
        gaps = {s["id"]: s["gaps"] for s in pc.coverage(doc, self.bundle)["screens"]}
        self.assertEqual(gaps["sample"], {"heading": ["Chain of custody"]})

    def test_a_360_has_the_prototypes_tabs_and_no_others(self):
        doc = spec()
        tabs = doc["detail_views"][0]["tabs"]
        tabs[1]["label"] = "Results and reports"
        tabs.append({"code": "audit", "label": "Audit", "type": "timeline"})
        gaps = {s["id"]: s["gaps"] for s in pc.coverage(doc, self.bundle)["screens"]}
        self.assertEqual(gaps["sample"], {"tab": ["Results"], "extra_tab": ["Results and reports", "Audit"]})

    def test_a_rebuilt_360_still_has_the_prototypes_tabs_only(self):
        doc = spec()
        entry = next(e for e in doc["prototype"]["screens"] if e["id"] == "sample")
        entry.update(rebuild=True, why="tracker above the tabs")
        doc["detail_views"][0]["tabs"].append({"code": "audit", "label": "Audit", "type": "timeline"})
        gaps = {s["id"]: s["gaps"] for s in pc.coverage(doc, self.bundle)["screens"]}
        self.assertEqual(gaps["sample"], {"extra_tab": ["Audit"]})

    def test_a_top_bar_button_most_screens_show_is_chrome(self):
        bare = NAV.replace("<button>New sample</button>", "")
        doms = {"home": bare + "<main><h2>Your queue</h2></main>", "samples": SAMPLES, "sample": SAMPLE,
                "instruments": SAMPLES, "tour": HOME}
        with tempfile.TemporaryDirectory() as tmp:
            result = pc.coverage(spec(), write_bundle(Path(tmp), doms))
        self.assertEqual(result["screens"], [])

    def test_a_not_built_item_counts_in_its_place_in_the_menu(self):
        nav = [(None, "Home"), ("Lab", "Samples"), ("AI", "Helpers"), ("Help", "Tour")]
        doc = spec()
        doc["prototype"]["screens"].append(
            {"id": "helpers", "only": "prototype", "why": "later", "menu": {"group": "AI", "label": "Helpers"}})
        role = {"name": "Lab lead", "menu": [{"page": "home", "label": "Home"},
                                            {"group": "Lab", "items": [{"page": "samples", "label": "Samples"}]}]}
        have = pc._menu_labels(doc, role, doc["prototype"]["screens"], MANIFEST, PL.norm, nav)
        self.assertEqual(have, nav)
        self.assertEqual(pc._role_menu_gaps("Lab lead", nav, have, PL.norm), [])


    def test_not_built_items_follow_the_prototype_not_the_spec_order(self):
        nav = [(None, "Home"), ("Lab", "Samples"), ("Help", "Tour"), ("Help", "Contact")]
        manifest = {**MANIFEST, "screens": MANIFEST["screens"] + [{"id": "contact", "title": "Contact", "group": "Help"}]}
        doc = spec()
        doc["prototype"]["screens"].insert(
            0, {"id": "contact", "only": "prototype", "why": "later", "menu": {"group": "Help", "label": "Contact"}})
        role = {"name": "Lab lead", "menu": [{"page": "home", "label": "Home"},
                                            {"group": "Lab", "items": [{"page": "samples", "label": "Samples"}]}]}
        self.assertEqual(pc._menu_labels(doc, role, doc["prototype"]["screens"], manifest, PL.norm, nav), nav)
        rows = [{"id": "contact", "cls": "prototype-only", "menu": {"group": "Help", "label": "Contact"}},
                {"id": "tour", "cls": "prototype-only", "menu": {"group": "Help", "label": "Tour"}}]
        self.assertEqual([i["label"] for i in spec_check.soon_items(rows, manifest)], ["Tour", "Contact"])


class RowTargetTests(unittest.TestCase):
    """Where a list row goes in the prototype (capture row_opens) against table.row_click."""

    def doc(self, row_click=None):
        doc = spec()
        doc["modules"][0]["entities"].append({
            "code": "result", "fields": [{"key": "sample", "type": "link", "to": "sample"}],
            "table": {"row_click": row_click} if row_click else {},
        })
        doc["pages"].append({"code": "results", "type": "crud", "title": "Results", "entity": "result"})
        doc["detail_views"][0]["tabs"].append(
            {"code": "results_tab", "label": "Results", "type": "related_table", "entity": "result", "via": "sample"})
        doc["prototype"]["screens"].append({"id": "results", "maps": "/pages/@results"})
        return doc

    def capture(self, goes):
        return {"screens": [{"id": "results", "row_opens": goes},
                            {"id": "samples", "row_opens": {"screen": "sample", "tab": "Overview"}}]}

    def test_a_row_that_opens_its_parent_on_a_tab_needs_view_hash_tab(self):
        gaps = pc.row_gaps(self.doc(), self.capture({"screen": "sample", "tab": "Results"}), PL.norm)
        self.assertEqual(len(gaps), 1)
        self.assertIn("set result's table.row_click: sample_360#results_tab (now 'drawer')", gaps[0])
        ok = pc.row_gaps(self.doc("sample_360#results_tab"), self.capture({"screen": "sample", "tab": "Results"}), PL.norm)
        self.assertEqual(ok, [])  # and samples rows open their own 360 by default

    def test_a_drawer_in_the_prototype_wants_drawer(self):
        gaps = pc.row_gaps(self.doc("sample_360#results_tab"), self.capture({"screen": None, "overlay": True}), PL.norm)
        self.assertIn("opens a drawer", gaps[0])
        self.assertEqual(pc.row_gaps(self.doc(), self.capture({"screen": None, "overlay": True}), PL.norm), [])


class MarkReadyTests(unittest.TestCase):
    def bench(self):
        b = SpecWorkbench.__new__(SpecWorkbench)
        b.proto = SimpleNamespace(parts={})
        return b

    def test_gaps_refuse_with_where_each_goes(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = write_bundle(Path(tmp))
            doc = spec()
            doc["pages"][1]["title"] = "Sample queue"
            with mock.patch.object(pc, "ensure_capture", return_value=(bundle, "")):
                with self.assertRaises(ToolRefused) as ctx:
                    self.bench()._check_prototype_coverage(doc, None)
        self.assertIn("roles[].menu", str(ctx.exception))
        self.assertIn("'Samples' (group 'Lab')", str(ctx.exception))

    def test_covered_spec_lists_what_is_not_built(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = write_bundle(Path(tmp))
            doc = spec()
            doc["prototype"]["screens"][2]["not_built"] = [{"text": "Barcode printing", "why": "later"}]
            with mock.patch.object(pc, "ensure_capture", return_value=(bundle, "")):
                note = self.bench()._check_prototype_coverage(doc, None)
        self.assertIn("covers every prototype screen", note)
        self.assertIn("sample: Barcode printing (later)", note)

    def test_no_browser_skips_with_a_note(self):
        with mock.patch.object(pc, "ensure_capture", return_value=(None, "unavailable: no Playwright")):
            note = self.bench()._check_prototype_coverage(spec(), None)
        self.assertIn("not checked: unavailable", note)


class CommitTests(unittest.TestCase):
    """Commit for build runs the same check, so the coverage gate can't be skipped."""

    def test_gaps_block_commit_with_a_brief_for_the_agent(self):
        import yaml

        from zango.apps.agent_mode import template_spec

        doc = spec()
        doc["pages"][1]["title"] = "Sample queue"
        req = SimpleNamespace(spec_markdown=yaml.safe_dump(doc), prototype_parts={"body.html": "x"})
        with tempfile.TemporaryDirectory() as tmp:
            bundle = write_bundle(Path(tmp))
            with mock.patch.object(pc, "ensure_capture", return_value=(bundle, "")):
                issues = template_spec.prototype_gaps(req)
        self.assertEqual(issues[0]["path"], "/roles")
        self.assertIn("'Samples' (group 'Lab')", issues[0]["message"])
        self.assertTrue(all(i["level"] == "error" for i in issues))

    def test_no_browser_lets_commit_through(self):
        import yaml

        from zango.apps.agent_mode import template_spec

        req = SimpleNamespace(spec_markdown=yaml.safe_dump(spec()), prototype_parts={})
        with mock.patch.object(pc, "ensure_capture", return_value=(None, "no Playwright")):
            self.assertEqual(template_spec.prototype_gaps(req), [])


class BuildHandoffTests(unittest.TestCase):
    def test_not_built_screens_go_to_the_shell_after_their_prototype_group(self):
        manifest = {"screens": [{"id": "a", "group": "Lab"}, {"id": "ai", "group": "AI"}, {"id": "b", "group": "Help"}]}
        rows = [{"id": "ai", "cls": "prototype-only", "menu": {"group": "AI", "label": "Agents", "icon": "bot"}},
                {"id": "b", "cls": "prototype-only", "menu": None}]
        self.assertEqual(spec_check.soon_items(rows, manifest),
                         [{"label": "Agents", "group": "AI", "icon": "bot", "after": "Lab"}])

    def test_a_rebuilt_screen_must_show_its_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "dom.rosa.html").write_text(SAMPLES)
            shows = spec_check.must_show(str(d), [{"text": "Assay", "why": "x"}])
        self.assertIn("column 'Next step'", shows)
        self.assertNotIn("'Assay'", shows)


if __name__ == "__main__":
    unittest.main()
