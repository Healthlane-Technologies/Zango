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
