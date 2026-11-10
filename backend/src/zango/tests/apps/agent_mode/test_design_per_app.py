"""Design checks follow the app's approved design, not the runtime's defaults.

- tokens.css's default look draws with --zl-* variables, which app.design retargets (DESIGN_MAP), so a
  user who changed the design gets it on panels, titles, tabs and tables;
- the gallery goldens check the runtime's own look: they stay out of a build's design groups and must be
  re-shot whenever the CSS they depict changes;
- a record screen is compared on its own sections, tabs and buttons, not on the demo record's name.
"""

import json
import re
import sys
import unittest

from pathlib import Path

from zango.apps.agent_mode import studio_build
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir


SKILL = Path(studio_plugin_dir()) / "skills" / "zango-app-studio"
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import proto_landmarks as PL  # noqa: E402
import spec_check  # noqa: E402

from zas_test import design  # noqa: E402


TOKENS = (SKILL / "assets" / "frontend" / "zas" / "tokens.css").read_text(encoding="utf-8")
PALETTE = ("#1E1B4B", "#E5E7EB", "#F3F4F6", "#D1D5DB", "#F9FAFB", "#4B5563", "#6B7280", "#9CA3AF", "#1F2937")


class DefaultLookFollowsAppDesign(unittest.TestCase):
    def test_no_palette_hex_left_in_the_default_look(self):
        look = TOKENS[TOKENS.index("/* ── default look"):]
        found = {h for h in PALETTE if re.search(re.escape(h) + r"\b", look, re.I)}
        self.assertFalse(found, f"default-look rules hard-code {sorted(found)}: use var(--zl-*)")

    def test_every_zl_variable_is_defined_and_retargetable(self):
        used = set(re.findall(r"var\((--zl-[\w-]+)\)", TOKENS))
        defined = set(spec_check._token_defaults())
        self.assertTrue(used <= defined, f"undefined: {sorted(used - defined)}")
        mapped = {v for targets in spec_check.DESIGN_MAP.values() for v in targets}
        self.assertTrue(used <= mapped, f"app.design cannot reach: {sorted(used - mapped)}")

    def test_app_design_reaches_panels_titles_and_tables(self):
        css, _, problems = spec_check.design_css({"tokens": {
            "border": "#112233", "border-faint": "#223344", "text-strong": "#334455", "sunk": "#445566"}})
        self.assertFalse(problems)
        for var, value in (("--zl-bd", "#112233"), ("--zl-bdf", "#223344"), ("--zl-ink", "#334455"), ("--zl-sunk", "#445566")):
            self.assertIn(f"{var}: {value};", css)


class ActivityAndStatusColours(unittest.TestCase):
    ZAS = SKILL / "assets" / "frontend" / "zas"

    def test_timeline_draws_from_and_to_as_status_badges(self):
        ui = (self.ZAS / "ui.tsx").read_text(encoding="utf-8")
        tl = ui[ui.index("export function Timeline("):ui.index("export function CopyButton")]
        self.assertIn('zasKey="from"', tl)
        self.assertIn('zasKey="to"', tl)
        self.assertIn("zas-tlch", tl)  # an edit lists its field changes

    def test_filter_chips_take_the_status_colour(self):
        table = (self.ZAS / "ZasTable.tsx").read_text(encoding="utf-8")
        self.assertIn("zas-qf-dot", table)
        self.assertIn(".zas-qf-dot", TOKENS)

    def test_a_single_all_chip(self):
        table = (self.ZAS / "ZasTable.tsx").read_text(encoding="utf-8")
        self.assertIn("!quick.some(isAll)", table)

    def test_guidance_forbids_hand_drawn_activity(self):
        text = (SKILL / "references" / "custom-code.md").read_text(encoding="utf-8")
        self.assertIn("Activity and status are never hand-drawn", text)


class LookScore(unittest.TestCase):
    def test_a_taller_header_is_not_a_different_layout(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow not installed")
        import tempfile
        import os

        def page(path, dy):
            im = Image.new("RGB", (1280, 900), "white")
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, 255, 900), outline="#999999")  # the sidebar never moves
            for k in range(5):  # cards under a header whose height varies
                y = 120 + dy + k * 150
                d.rectangle((290, y, 920, y + 120), outline="#555555")
                d.text((310, y + 20), f"Section {k}", fill="black")
            im.save(path)

        with tempfile.TemporaryDirectory() as tmp:
            a, b = os.path.join(tmp, "a.png"), os.path.join(tmp, "b.png")
            page(a, 0)
            page(b, 14)
            self.assertLess(design.look_score(b, a), 0.15)


class GalleryGoldens(unittest.TestCase):
    def test_not_a_build_check(self):
        self.assertNotIn("gallery", studio_build.DESIGN_BROWSER_GROUPS)
        self.assertNotIn("gallery", design.GROUPS)
        self.assertIn("gallery", design.RUNNERS)

    def test_goldens_are_fresh(self):
        meta = json.loads((SKILL / "assets" / "goldens" / "meta.json").read_text())
        self.assertEqual(
            meta.get("runtime"), design.runtime_fingerprint(),
            "tokens.css, kit.css or Gallery.tsx changed: re-shoot the goldens "
            "(python3 -m zas_test.design --make-goldens --workspace <built app>) and commit them")


class RecordParity(unittest.TestCase):
    DOM = ('<div><h2>Asha Verma</h2><h2>Senior Backend Engineer</h2><button>Move to Offer</button>'
           '<div role="tab">Details</div><h3>Contact</h3></div>')

    def test_record_name_is_data_but_sections_and_buttons_are_required(self):
        gaps = PL.content_gaps(self.DOM, "<div></div>", "", record=True)
        self.assertNotIn("missing heading 'Asha Verma'", gaps)
        self.assertNotIn("missing heading 'Senior Backend Engineer'", gaps)
        self.assertIn("missing heading 'Contact'", gaps)
        self.assertIn("missing tab 'Details'", gaps)
        self.assertIn("missing button 'Move to Offer'", gaps)

    def test_a_list_page_still_requires_its_headings(self):
        gaps = PL.content_gaps(self.DOM, "<div></div>", "", record=False)
        self.assertIn("missing heading 'Asha Verma'", gaps)


if __name__ == "__main__":
    unittest.main()
