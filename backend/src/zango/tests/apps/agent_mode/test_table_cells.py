"""A list cell is drawn as the preview draws it: an icon or initials, the value, a muted second line.

Regression (run 8): the approved Requests list showed "Midwest Glaucoma Summit 2027 · Gold
exhibitor" over a monospace "SP-2026-0061 · Congress exhibit", after an icon per request type. The
YAML column could only name one field and the gate compared headings only, so the build drew a
plain title.
"""

import copy
import sys
import tempfile
import unittest

from pathlib import Path

import yaml

from zango.apps.agent_mode import prototype_coverage as pc
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir


SKILL = Path(studio_plugin_dir()) / "skills" / "zango-app-studio"
if str(SKILL / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL / "scripts"))

import proto_landmarks as PL  # noqa: E402
import spec_check  # noqa: E402

from .test_prototype_coverage import MANIFEST, NAV, spec, write_bundle  # noqa: E402


ROW = """<td><div style="display:flex"><span class="ico"><svg><path d="M1 1"/></svg></span>
  <div><div class="t">Throat swab, Ward 4</div><div class="s mono">LAB-2026-0042 · PCR</div></div></div></td>"""

SAMPLES = NAV + f"""
<main><h1>Samples</h1>
  <button>Open 8</button><button>Due today 2</button>
  <table><thead><tr><th>Sample</th><th>Assay</th><th>Next step</th><th>Received</th></tr></thead>
  <tbody><tr>{ROW}<td>PCR</td><td><button>Assign</button></td><td>$1,200</td></tr>
         <tr><td>Second row is not read</td><td>x</td><td>y</td><td>z</td></tr></tbody></table>
</main>
"""


class CellLandmarkTests(unittest.TestCase):
    def test_a_two_line_cell_with_an_icon(self):
        self.assertEqual(
            PL.cells(SAMPLES),
            [{"column": "Sample", "index": 0, "lines": ["Throat swab, Ward 4", "LAB-2026-0042 · PCR"],
              "icon": "icon", "mono": True}],
        )

    def test_initials_are_an_avatar_not_a_line(self):
        html = ("<table><tr><th>Organiser</th></tr><tr><td><span class='av'><div>NO</div></span>"
                "<div><div>Northern Ohio Society</div><div>Cleveland, OH</div></div></td></tr></table>")
        [cell] = PL.cells(html)
        self.assertEqual((cell["icon"], cell["lines"]), ("initials", ["Northern Ohio Society", "Cleveland, OH"]))

    def test_plain_cells_are_not_reported(self):
        self.assertEqual(PL.cells("<table><tr><th>A</th></tr><tr><td><span class='pill'>Open</span></td></tr></table>"), [])


class CellGapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bundle = write_bundle(Path(self.tmp.name), {"samples": SAMPLES})

    def tearDown(self):
        self.tmp.cleanup()

    def gaps(self, doc):
        return {s["id"]: s["gaps"] for s in pc.coverage(doc, self.bundle)["screens"]}.get("samples", {})

    def test_a_plain_column_for_a_two_line_cell_is_a_gap(self):
        [gap] = self.gaps(spec())["cell"]
        self.assertIn("'Sample'", gap)
        self.assertIn("`secondary: [<fields>]`, `secondary_style: mono`", gap)
        self.assertIn("`icon:", gap)

    def test_secondary_and_icon_cover_it(self):
        doc = spec()
        doc["modules"][0]["entities"][0]["table"]["columns"][0] = {
            "ref": {"label": "Sample", "secondary": ["ref", "assay"], "secondary_style": "mono", "icon": "flask-conical"}}
        self.assertNotIn("cell", self.gaps(doc))

    def test_the_lead_column_under_another_heading_still_counts(self):
        doc = spec()
        doc["modules"][0]["entities"][0]["table"]["columns"][0] = {"ref": {"label": "ID"}}
        self.assertIn("'Sample'", " ".join(self.gaps(doc).get("cell", [])))


class CellSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = yaml.safe_load((SKILL / "evals" / "vendor_hub.yaml").read_text())

    def check(self, conf):
        raw = copy.deepcopy(self.raw)
        ent = next(e for m in raw["modules"] for e in m["entities"] if e["code"] == "vendor")
        ent["table"]["columns"][1] = {"legal_name": {"label": "Name", **conf}}
        S = spec_check.Spec(raw, "t.yaml")
        S.build()
        S.lint()
        col = next(c for c in S.M["entities"]["vendor"]["table"]["columns"] if c["key"] == "legal_name")
        msgs = [i["msg"] for i in S.L.items if ".legal_name" in i["where"]]
        ui = S._ui_column(S.M["entities"]["vendor"], col)
        return col, msgs, ui

    def test_secondary_and_a_fixed_icon_reach_the_runtime(self):
        col, msgs, ui = self.check({"secondary": "vendor_ref", "secondary_style": "mono", "icon": "building-2"})
        self.assertEqual(msgs, [])
        self.assertEqual(col["secondary"], ["vendor_ref"])
        self.assertEqual(ui["icon"], {"by": None, "map": {}, "default": "building-2"})
        self.assertEqual(ui["secondary_style"], "mono")

    def test_bad_paths_and_icons_are_errors(self):
        _, msgs, _ = self.check({"secondary": ["nope"], "icon": {"by": "nope", "map": {"x": "Bad Icon"}}})
        text = " ".join(msgs)
        self.assertIn("'nope'", text)
        self.assertIn("not lucide icon names", text)

    def test_an_icon_by_value_checks_the_choices(self):
        _, msgs, _ = self.check({"icon": {"by": "vendor_type", "map": {"no_such_type": "truck"}}})
        self.assertTrue(any("not choices of vendor_type" in m for m in msgs), msgs)


if __name__ == "__main__":
    unittest.main()


# ---- the built screen shows what the approved one does (run 8: a rebuild that wrapped the stock table) ----

APPROVED = NAV + """
<main><h1>Sponsorship requests</h1><p>Congress exhibits and symposia · $366,000 requested</p>
  <button class="chip">Open <span>7</span></button><button class="chip">Closed <span>5</span></button>
  <table><thead><tr><th>Request</th><th>Organiser</th></tr></thead>
  <tbody><tr><td><div><div>Summit 2027</div><div class="mono">SP-1 · Congress exhibit</div></div></td><td>NOS</td></tr></tbody></table>
</main>
"""

STOCK = NAV + """
<main><h1>Sponsorship requests</h1><p>48 records</p>
  <button>Open</button><button>Closed</button>
  <table><thead><tr><th>Request</th><th>Organiser</th></tr></thead>
  <tbody><tr><td>Summit 2027</td><td>NOS</td></tr></tbody></table>
</main>
"""


def text_of(html):
    import re
    return re.sub(r"<[^>]+>", " ", html)


class ContentParityTests(unittest.TestCase):
    def test_a_stock_table_in_place_of_the_approved_one_is_named(self):
        gaps = PL.content_gaps(APPROVED, STOCK, text_of(STOCK))
        text = " | ".join(gaps)
        self.assertIn("filter chip 'Open' shows no count", text)
        self.assertIn("subtitle under the title", text)
        self.assertIn("column 'Request' cells lack a second line", text)

    def test_the_same_screen_has_no_gaps(self):
        self.assertEqual(PL.content_gaps(APPROVED, APPROVED, text_of(APPROVED)), [])

    def test_persona_names_chrome_and_spec_drawn_cells_are_not_gaps(self):
        approved = "<main><h1>Good morning, Elena</h1><button>EP Elena Park Budget owner</button></main>"
        built = "<main><h1>Good morning, Test</h1></main>"
        self.assertEqual(PL.content_gaps(approved, built, text_of(built),
                                         ignore_words=["Elena Park", "Budget owner"]), [])
        gaps = PL.content_gaps(APPROVED, STOCK, text_of(STOCK), drawn_cells=["Request"])
        self.assertFalse([g for g in gaps if "cells lack" in g])


class ListGapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        html = SAMPLES.replace("<h1>Samples</h1>", "<h1>Samples</h1><p>Every sample received this week</p>")
        self.bundle = write_bundle(Path(self.tmp.name), {"samples": html})

    def tearDown(self):
        self.tmp.cleanup()

    def gaps(self, doc):
        return {s["id"]: s["gaps"] for s in pc.coverage(doc, self.bundle)["screens"]}

    def test_counts_subtitle_and_exact_column_labels_are_asked_for(self):
        doc = spec()
        for q in doc["modules"][0]["entities"][0]["table"]["quick_filters"]:
            q.pop("count")
        g = self.gaps(doc)["samples"]
        self.assertEqual(g["count"], ["Open", "Due today"])
        self.assertEqual(g["subtitle"], ["Every sample received this week"])

    def test_count_and_subtitle_in_the_yaml_cover_them(self):
        doc = spec()
        doc["pages"][1]["subtitle"] = {"text": "Every sample received this week"}
        for q in doc["modules"][0]["entities"][0]["table"]["quick_filters"]:
            q["count"] = True
        g = self.gaps(doc).get("samples", {})
        self.assertNotIn("count", g)
        self.assertNotIn("subtitle", g)

    def test_a_rebuilt_wizard_on_a_kept_list_page_needs_its_own_page(self):
        doc = spec()
        doc["prototype"]["screens"].append({"id": "new", "maps": "/pages/@samples", "rebuild": True, "why": "wizard"})
        with tempfile.TemporaryDirectory() as tmp:
            bundle = write_bundle(Path(tmp), {"samples": SAMPLES, "new": SAMPLES})
            g = {s["id"]: s["gaps"] for s in pc.coverage(doc, bundle)["screens"]}
        self.assertIn("shared_rebuild", g["new"])


class SubtitleSpecTests(CellSpecTests):
    def page(self, sub):
        raw = copy.deepcopy(self.raw)
        page = next(p for p in raw["pages"] if p.get("entity") == "purchase_order")
        page["subtitle"] = sub
        S = spec_check.Spec(raw, "t.yaml")
        S.build()
        S.lint()
        S.prototype_screens()
        S.page_holes()
        S.derive()
        S.number_holes({})
        msgs = [i["msg"] for i in S.L.items if ".subtitle" in i["where"]]
        return msgs, S.ui_json()["pages"][page["code"]].get("subtitle")

    def test_text_and_a_sum_reach_the_runtime(self):
        msgs, ui = self.page({"text": "Orders this year", "stat": {"sum": "total_amount", "format": "money",
                                                                  "suffix": "ordered", "where": "status != cancelled"}})
        self.assertEqual(msgs, [])
        self.assertEqual(ui, {"text": "Orders this year", "stat": {"format": "money", "suffix": "ordered"}})

    def test_a_sum_of_a_text_field_is_an_error(self):
        msgs, _ = self.page({"text": "x", "stat": {"sum": "po_ref"}})
        self.assertTrue(any("not a number field" in m for m in msgs), msgs)


class GluedCountTests(unittest.TestCase):
    def test_a_count_drawn_against_its_label_still_shows_the_label(self):
        built = STOCK.replace("<button>Open</button>", "<button>Open<span>7</span></button>")
        gaps = PL.content_gaps(APPROVED, built, "Sponsorship requests Open7 Closed Request Organiser Summit 2027")
        self.assertFalse([g for g in gaps if "'Open'" in g], gaps)
        self.assertIn("missing button 'Open'", PL.content_gaps(APPROVED, built, "Sponsorship requests Closed"))
