"""design_diff: a template app's built styles against the approved prototype (the kit page).

The kit page and the runtime draw the same pieces with two class vocabularies (scripts/kit_vocab.py);
zas_test/style.py pairs them, compares computed styles, blocks on what the creator changed (approved
differs from the baseline) and writes the approved values on the runtime selectors. The change map
carries the look (changed stylesheets, the classes they touch, their diffs).
"""

import json
import re
import sys
import tempfile
import unittest

from pathlib import Path
from unittest import mock

from zango.apps.agent_mode import studio_build
from zango.apps.agent_mode.approval_bundle import change_map, look_changes, write_change_map
from zango.apps.agent_mode.studio_build import STYLE_CHECK, StudioBuild, blocking
from zango.apps.agent_mode.studio_tools import _paths
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir


SKILL = Path(studio_plugin_dir()) / "skills" / "zango-app-studio"
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import kit_vocab as V  # noqa: E402

from zas_test import style  # noqa: E402

KIT_PAGE = Path(__file__).resolve().parents[3] / "apps" / "shared" / "app_templates" / "packs" / "zango_app" / "builder" / "app-studio.html"
RUNTIME = SKILL / "assets" / "frontend" / "zas"


def kit_classes():
    page = KIT_PAGE.read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", "".join(re.findall(r"<style[^>]*>(.*?)</style>", page, re.S)), flags=re.S)
    out = set()
    for sel in re.findall(r"([^{}]+)\{[^{}]*\}", css):
        out |= set(re.findall(r"\.((?:z|d)-[a-zA-Z0-9-]+)", sel))
    return out


def runtime_classes():
    text = (RUNTIME / "tokens.css").read_text(encoding="utf-8")
    text += "".join(p.read_text(encoding="utf-8") for p in RUNTIME.glob("*.tsx"))
    return set(re.findall(r"(zas-[a-zA-Z0-9-]+)", text))


class VocabularyTests(unittest.TestCase):
    """The mapping table stays complete as either kit changes: CI fails on drift."""

    def test_every_kit_class_is_mapped(self):
        missing = sorted(kit_classes() - set(V.CLASS_MAP))
        self.assertEqual(missing, [], "kit classes with no entry in kit_vocab.CLASS_MAP")

    def test_every_mapped_runtime_class_exists(self):
        have = runtime_classes()
        gone = sorted(v for v in V.CLASS_MAP.values() if v and v not in have)
        self.assertEqual(gone, [], "kit_vocab.CLASS_MAP names runtime classes the zas runtime no longer has")

    def test_every_part_names_real_classes_on_both_sides(self):
        kit, rt = kit_classes(), runtime_classes()
        for pid, _label, kit_sel, rt_sel, groups, _data in V.PARTS:
            self.assertTrue(V.classes_of(kit_sel) & kit, f"{pid}: {kit_sel} names no kit class")
            names = {c for c in V.classes_of(rt_sel) if c.startswith("zas-")}
            self.assertTrue(names and names <= rt, f"{pid}: {rt_sel} names a class the runtime lacks")
            self.assertTrue(set(groups) <= set(V.PROPS), pid)

    def test_the_kit_app_look_is_what_the_kit_draws(self):
        from zango.apps.agent_mode.prototype_kit import KIT_APP_LOOK

        page = KIT_PAGE.read_text(encoding="utf-8").lower()
        for name, value in KIT_APP_LOOK.items():
            short = value.lower().replace("#ffffff", "#fff")
            self.assertTrue(value.lower() in page or short in page, f"{name}: {value} is not in the kit's CSS")

    def test_selectors_translate(self):
        self.assertEqual(V.translate_selector(".d-head .d-fact > span"), ".zas-dhead .zas-dfact > span")
        self.assertEqual(V.translate_selector(".z-qf.on"), ".zas-qf.on")
        self.assertEqual(V.translate_selector(".z-user .z-av"), ".zas-sh-user .zas-sh-av")
        self.assertIsNone(V.translate_selector(".z-money input"))

    def test_touched_classes_reach_their_parts(self):
        ids = V.touched_parts({"d-head", "d-tab"})
        self.assertIn("head", ids)
        self.assertIn("head_title", ids)
        self.assertIn("tab_on", ids)
        self.assertNotIn("sidebar", ids)
        self.assertEqual(V.touched_parts({"*"}), {p[0] for p in V.PARTS})


def styles(**parts):
    """STYLES_JS-shaped results: part id → props (count 1), or None for a part not shown."""
    return {k: ({"count": 0} if v is None else {"count": 1, "props": v}) for k, v in parts.items()}


HEAD_APPROVED = {
    "background-color": "rgba(0, 0, 0, 0)",
    "background-image": "linear-gradient(135deg, rgb(11, 90, 112) 0%, rgb(14, 116, 144) 55%)",
    "border-top-left-radius": "18px",
    "box-shadow": "rgba(14, 116, 144, 0.25) 0px 10px 30px 0px",
}
HEAD_TEMPLATE = {
    "background-color": "rgb(255, 255, 255)",
    "background-image": "none",
    "border-top-left-radius": "12px",
    "box-shadow": "rgba(16, 24, 40, 0.04) 0px 1px 2px 0px",
}


class CompareTests(unittest.TestCase):
    def test_values_compare_by_what_they_look_like(self):
        same = style.same_value
        self.assertTrue(same("background-color", "rgb(255, 255, 255)", "color(srgb 1 1 1)"))
        self.assertTrue(same("color", "rgb(14, 116, 144)", "rgb(16, 117, 146)"))
        self.assertFalse(same("color", "rgb(255, 255, 255)", "rgb(20, 23, 31)"))
        self.assertTrue(same("background-color", "rgba(0, 0, 0, 0)", "rgba(255, 255, 255, 0)"))
        self.assertFalse(same("background-image", HEAD_APPROVED["background-image"], "none"))
        self.assertFalse(same("box-shadow", HEAD_APPROVED["box-shadow"], HEAD_TEMPLATE["box-shadow"]))
        self.assertFalse(same("border-top-left-radius", "18px", "12px"))
        self.assertTrue(same("letter-spacing", "normal", "0px"))
        self.assertFalse(same("border-top-width", "0px", "1px"))
        self.assertTrue(same("padding-top", "10px", "10.5px"))

    def test_only_what_the_creator_changed_blocks(self):
        approved = styles(head=HEAD_APPROVED, card={"background-color": "rgb(255, 255, 255)",
                                                    "border-top-left-radius": "12px"})
        baseline = styles(head=HEAD_TEMPLATE, card={"background-color": "rgb(255, 255, 255)",
                                                    "border-top-left-radius": "12px"})
        built = styles(head=HEAD_TEMPLATE, card={"background-color": "rgb(250, 250, 250)",
                                                 "border-top-left-radius": "16px"})
        diffs = style.compare(approved, built)
        changed = style.changed_keys(approved, baseline)
        blocking_ = [d for d in diffs if style.is_blocking(d, set(), changed)]
        self.assertEqual({d["part"] for d in blocking_}, {"head"})
        self.assertIn("background-image", {d["prop"] for d in blocking_})
        # the card differs too, but the creator never changed it: listed, not blocking
        self.assertIn("card", {d["part"] for d in diffs if not style.is_blocking(d, set(), changed)})

    def test_without_a_baseline_the_touched_classes_decide(self):
        diffs = style.compare(styles(head=HEAD_APPROVED), styles(head=HEAD_TEMPLATE))
        self.assertTrue(all(style.is_blocking(d, V.touched_parts({"d-head"})) for d in diffs))
        self.assertFalse(any(style.is_blocking(d, V.touched_parts({"z-t"})) for d in diffs))

    def test_a_missing_part_and_a_missing_decoration_are_differences(self):
        approved = styles(head=HEAD_APPROVED, badge={"color": "rgb(1, 2, 3)"})
        approved["head"]["::before"] = {"background-color": "rgba(255, 255, 255, 0.1)", "width": "260px",
                                        "height": "260px", "border-top-left-radius": "50%",
                                        "top": "-80px", "bottom": "7px", "right": "-60px", "left": "786px"}
        built = styles(head=HEAD_APPROVED, badge=None)
        diffs = style.compare(approved, built)
        self.assertIn(("badge", "present"), {(d["part"], d["prop"]) for d in diffs})
        self.assertIn(("head", "::before"), {(d["part"], d["prop"]) for d in diffs})
        # a data-dependent part the built rows don't show never blocks
        badge = next(d for d in diffs if d["part"] == "badge")
        self.assertFalse(style.is_blocking(badge, {"badge"}, {("badge", "present")}))

    def test_the_fix_puts_the_approved_values_on_the_runtime_selectors(self):
        approved = styles(head=HEAD_APPROVED, fact={"border-top-left-radius": "12px",
                                                    "border-bottom-right-radius": "12px",
                                                    "padding-top": "10px", "padding-right": "16px",
                                                    "padding-bottom": "10px", "padding-left": "16px",
                                                    "background-color": "color(srgb 1 1 1 / 0.14)"})
        approved["head"]["::before"] = {"background-color": "rgba(255, 255, 255, 0.1)", "width": "260px",
                                        "height": "260px", "border-top-left-radius": "50%",
                                        "top": "-80px", "bottom": "7px", "right": "-60px", "left": "786px"}
        built = styles(head=HEAD_TEMPLATE, fact={"border-top-left-radius": "0px",
                                                 "border-bottom-right-radius": "0px",
                                                 "padding-top": "0px", "padding-right": "0px",
                                                 "padding-bottom": "0px", "padding-left": "0px",
                                                 "background-color": "rgba(0, 0, 0, 0)"})
        css = style.fix_css(style.compare(approved, built))
        self.assertIn("html .zas-dhead {", css)
        self.assertIn("linear-gradient(135deg, rgb(11, 90, 112) 0%", css)
        self.assertIn("html .zas-dhead::before {", css)
        before = re.search(r"html \.zas-dhead::before \{([^}]*)\}", css).group(1)
        self.assertIn("top: -80px", before)
        self.assertIn("right: -60px", before)
        self.assertNotIn("left:", before)
        self.assertNotIn("bottom:", before)
        self.assertIn("html .zas-dhead > * { position: relative; z-index: 1; }", css)
        fact = re.search(r"html \.zas-dfact \{([^}]*)\}", css).group(1)
        self.assertIn("border-radius: 12px", fact)
        self.assertIn("padding: 10px 16px 10px 16px", fact)
        self.assertIn("rgba(255, 255, 255, 0.14)", fact)
        self.assertNotIn("color(srgb", css)


BASE = {
    "manifest.json": json.dumps({"screens": [{"id": "dashboard"}, {"id": "patient_360"}], "kit": True}),
    "imported/bridge.css": ".hd,.ed{display:none!important}\n.body{grid-template-columns:1fr!important}\n",
    "imported/styles.css": ".d-head{background:#fff}.z-card{border-radius:12px}",
    "tokens.css": ":root{--brand:#0E7490}",
}


class LookChangeMapTests(unittest.TestCase):
    def test_no_change_touches_nothing(self):
        self.assertEqual(look_changes(dict(BASE), dict(BASE))["touched"], [])

    def test_a_bridge_rule_touches_its_classes_and_carries_its_diff(self):
        parts = {**BASE, "imported/bridge.css": BASE["imported/bridge.css"]
                 + ".d-head{background:linear-gradient(#0B5A70,#14A38B)!important}\n.d-tab.on{background:#fff}\n"}
        look = look_changes(parts, BASE)
        self.assertEqual(look["parts"], ["imported/bridge.css"])
        self.assertEqual(look["touched"], ["d-head", "d-tab", "on"])
        self.assertIn("+.d-head{background:linear-gradient", look["diffs"]["imported/bridge.css"])

    def test_a_root_variable_touches_everything(self):
        parts = {**BASE, "tokens.css": ":root{--brand:#7C3AED}"}
        self.assertIn("*", look_changes(parts, BASE)["touched"])

    def test_the_change_map_writes_the_look_and_its_diff_files(self):
        parts = {**BASE, "imported/bridge.css": BASE["imported/bridge.css"] + ".d-fact{border-radius:12px}\n"}
        changes, _ = change_map(parts, BASE, "template t@1")
        self.assertEqual(changes["look"]["touched"], ["d-fact"])
        with tempfile.TemporaryDirectory() as out:
            written = write_change_map(out, parts, ("template t@1", BASE))
            rel = written["look"]["diffs"]["imported/bridge.css"]
            self.assertEqual(rel, "shared/imported__bridge.css.diff")
            self.assertIn("+.d-fact{border-radius:12px}", (Path(out) / rel).read_text())
            saved = json.loads((Path(out) / "changes.json").read_text())
            self.assertEqual(saved["look"]["diffs"]["imported/bridge.css"], rel)


class BuildWiringTests(unittest.TestCase):
    def test_style_failures_fail_the_build(self):
        layer = studio_build.LayerResult(name="design", status="fail",
                                         failures=[{"id": f"{STYLE_CHECK}.patient_360.program_manager"}])
        self.assertTrue(blocking({"design": layer}))

    def test_the_style_check_runs_in_the_design_layer_and_studio_verify(self):
        self.assertIn("style", studio_build.DESIGN_BROWSER_GROUPS)
        self.assertEqual(_paths({"paths": ["style", "style.patient_360", "kit"]}),
                         ["style", "style.patient_360", "kit"])

    def test_fix_rounds_leave_style_to_the_style_rounds(self):
        sb = StudioBuild.__new__(StudioBuild)
        layer = studio_build.LayerResult(name="design", status="fail",
                                         failures=[{"id": f"{STYLE_CHECK}.patient_360.pm"}])
        with mock.patch.object(StudioBuild, "platform_issue_ids", return_value=[]):
            out = sb._for_agent({"design": layer})
        self.assertEqual(out["design"].failures, [])

    def test_the_style_digest_points_at_the_fix(self):
        sb = StudioBuild.__new__(StudioBuild)
        text = sb.style_digest(1, 4, [{"id": f"{STYLE_CHECK}.patient_360.pm", "detail": "record header …"}])
        self.assertIn(".zas/style_fix.css", text)
        self.assertIn("kit.css", text)
        self.assertIn('studio_verify(["style"])', text)



class PreviewLookTests(unittest.TestCase):
    """The analyst's look lands in the preview: look.css (and the bridge) load after the kit's own
    stylesheet, a look request in words is held to a prototype change, proto_look sees this turn's YAML."""

    def test_look_css_loads_after_the_kit_stylesheet(self):
        from zango.apps.agent_mode.prototype import _ordered

        parts = {"tokens.css": "", "imported/styles.css": "", "imported/bridge.css": "", "look.css": "",
                 "imported/script-01.js": ""}
        css, _ = _ordered(parts, {"screens": []})
        self.assertEqual(css, ["tokens.css", "imported/styles.css", "imported/bridge.css", "look.css"])

    def test_a_look_request_in_words(self):
        from types import SimpleNamespace

        from zango.apps.agent_mode.documents import is_look_request

        req = SimpleNamespace(mode="template")
        self.assertTrue(is_look_request(req, SimpleNamespace(content="make the sidebar dark")))
        self.assertTrue(is_look_request(req, SimpleNamespace(content="rounder cards and a hero header")))
        self.assertFalse(is_look_request(req, SimpleNamespace(content="add a due date column to requests")))
        self.assertFalse(is_look_request(SimpleNamespace(mode="journey"),
                                         SimpleNamespace(content="make the sidebar dark")))

    def bench(self, writes=0, theme_now=None, theme_then=None):
        from types import SimpleNamespace

        from zango.apps.agent_mode.spec_tools import SpecWorkbench

        b = SpecWorkbench.__new__(SpecWorkbench)
        b.proto = SimpleNamespace(writes=writes)
        b.reference_turn, b.look_turn = False, True
        b._look_unavailable, b._looked_at_writes = False, writes
        b.reference_html, b._ref_looks, b._ref_unavailable = False, 0, False
        b.doc = {"app": {"theme": theme_now}}
        b._theme_at_start = json.dumps(theme_then, sort_keys=True, default=str)
        return b

    def test_a_look_request_with_no_prototype_change_is_sent_back(self):
        gap = self.bench().reference_gap()
        self.assertIn("look.css", gap)

    def test_a_brand_colour_change_in_the_yaml_is_enough(self):
        self.assertIsNone(self.bench(theme_now={"primary": "#7C3AED"},
                                     theme_then={"primary": "#0E7490"}).reference_gap())

    def test_a_look_change_that_was_looked_at_passes(self):
        self.assertIsNone(self.bench(writes=2).reference_gap())



class CompiledLookTests(unittest.TestCase):
    """The platform carries the creator's look over: look.css and the bridge on the runtime's selectors."""

    def test_rules_move_to_the_runtime_selectors(self):
        css, skipped = V.compile_css(
            ".hd,.ed{display:none!important}\n.body{grid-template-columns:1fr}\n"
            ".d-head{background:linear-gradient(#0B5A70,#14A38B)!important}\n"
            ".d-head::before{content:\"\";position:absolute;right:-60px}\n"
            ".d-head .d-av{width:68px}.z-t tbody tr:hover td{background:#F3FAFB}\n"
            ".z-money input{border:0}\n@media (max-width:800px){.d-facts{gap:4px}}\n:root{--brand:#123}")
        self.assertIn("html .zas-dhead { background:linear-gradient(#0B5A70,#14A38B)!important }", css)
        self.assertIn("html .zas-dhead::before {", css)
        self.assertIn("html .zas-dhead .zas-av { width:68px }", css)
        self.assertIn("html .zas-t tbody tr:hover td {", css)
        self.assertIn("@media (max-width:800px) {\nhtml .zas-dfacts { gap:4px }\n}", css)
        self.assertNotIn(".hd", css)
        self.assertNotIn("--brand", css)
        self.assertEqual(skipped, [".z-money input"])

    def test_proto_port_writes_the_look_for_a_kit_page_only(self):
        import proto_port

        html = ('<html><head><style data-part="imported/styles.css">.d-head{background:#fff}</style>'
                '<style data-part="imported/bridge.css">.hd{display:none}</style>'
                '<style data-part="look.css">.d-head{border-radius:18px}.z-money{border:0}</style>'
                "</head><body></body></html>")
        for kit_page in (True, False):
            with tempfile.TemporaryDirectory() as ws:
                ws = Path(ws)
                proto = ws / ".zas" / "bundle" / "prototype"
                proto.mkdir(parents=True)
                (proto / "prototype.html").write_text(html)
                (proto / "manifest.json").write_text(json.dumps({"kit": kit_page}))
                (ws / "frontend" / "src" / "zas").mkdir(parents=True)
                result = proto_port.run(str(ws))
                look = ws / "frontend" / "src" / "zas" / "look.gen.css"
                if kit_page:
                    text = look.read_text()
                    self.assertIn("html .zas-dhead { border-radius:18px }", text)
                    self.assertNotIn(".zas-dhead { background:#fff }", text)  # the kit's own stylesheet stays out
                    self.assertIn("Not carried over", text)
                    self.assertEqual(result["look_skipped"], [".z-money"])
                else:
                    self.assertFalse(look.exists())

    def test_the_runtime_ships_and_imports_an_empty_look(self):
        self.assertTrue((RUNTIME / "look.gen.css").is_file())
        self.assertIn('import "./look.gen.css";', (RUNTIME / "kit.tsx").read_text())


if __name__ == "__main__":
    unittest.main()


class ReferenceLookTests(unittest.TestCase):
    """An HTML reference is seen (ref_look) before it is applied, its measured look is mapped onto
    the kit and the YAML, and a kit-page prototype draws with the current kit."""

    def bench(self, ref_looks=0, unavailable=False):
        from types import SimpleNamespace

        from zango.apps.agent_mode.spec_tools import SpecWorkbench

        b = SpecWorkbench.__new__(SpecWorkbench)
        b.proto = SimpleNamespace(writes=3, documents={"AZ.html": "<html></html>"})
        b.reference_turn, b.look_turn, b.reference_html = True, False, True
        b._look_unavailable, b._looked_at_writes = False, 3
        b._ref_looks, b._ref_unavailable = ref_looks, unavailable
        return b

    def test_an_html_reference_not_seen_is_sent_back(self):
        self.assertIn("ref_look", self.bench().reference_gap())

    def test_a_seen_reference_passes(self):
        self.assertIsNone(self.bench(ref_looks=1).reference_gap())

    def test_a_reference_that_cannot_render_is_not_held(self):
        self.assertIsNone(self.bench(unavailable=True).reference_gap())

    def test_an_unknown_document_is_refused(self):
        from zango.apps.agent_mode.spec_tools import ToolRefused

        with self.assertRaises(ToolRefused):
            self.bench().ref_look("other.html")

    def test_the_measured_look_is_mapped_onto_the_kit_and_the_yaml(self):
        from zango.apps.agent_mode.spec_tools import format_reference

        text = format_reference("AZ.html", {
            "url": "/#/app/referrals", "title": "AZ",
            "styles": {"button_primary": {"background-color": "#830051", "_text": "Export"},
                       "table_header": {"font-size": "12px"},
                       "palette": {"backgrounds": ["#FFFFFF"], "text": ["#0B0D14"]}},
            "tables": [{"columns": ["Patient"], "rows": 20, "first_row": [
                {"column": "Patient", "lines": ["Harpreet Banerjee", "AZC0104"], "avatar": "HB",
                 "pills": [], "progress_bar": False, "chevron": False}]}],
            "clickable": ["Referrals"],
        })
        self.assertIn(".z-btn.pri", text)
        self.assertIn("#830051", text)
        self.assertIn(".z-t th", text)
        self.assertIn("columns.<k>.secondary", text)
        self.assertIn("icon: initials", text)

    def test_the_worker_renders_a_page(self):
        import base64
        import subprocess

        from zango.apps.agent_mode.spec_tools import REF_WORKER

        try:
            import playwright  # noqa: F401
        except ImportError:
            self.skipTest("no Playwright")
        html = ("<html><body style='background:#FAF8F6;font-family:Arial'><aside style='height:900px;"
                "width:240px;background:#fff'><a>Home</a></aside><button style='background:#830051;"
                "color:#fff'>Export</button><table><thead><tr><th>Patient</th></tr></thead><tbody><tr>"
                "<td><div>Harpreet Banerjee</div><div>AZC0104</div></td></tr></tbody></table></body></html>")
        run = subprocess.run([sys.executable, str(REF_WORKER)], input=json.dumps({"html": html}),
                             capture_output=True, text=True, timeout=120)
        res = json.loads(run.stdout)
        self.assertTrue(res["ok"])
        self.assertTrue(base64.b64decode(res["png"]).startswith(b"\x89PNG"))
        self.assertEqual(res["styles"]["button_primary"]["background-color"], "#830051")
        self.assertEqual(res["tables"][0]["first_row"][0]["lines"], ["Harpreet Banerjee", "AZC0104"])

    def kit(self, script="draw()"):
        return f"<html><head><style>.z-t{{color:red}}</style></head><body><div id=zapp></div><script>{script}</script></body></html>"

    def parts(self, script="draw()"):
        from zango.apps.agent_mode.prototype import import_html
        from zango.apps.agent_mode.prototype_kit import BRIDGE_PART, SPEC_PART

        parts, _ = import_html(self.kit(script))
        parts.update({SPEC_PART: "spec", BRIDGE_PART: "bridge", "imported/bridge.css": "b",
                      "look.css": ".z-side{background:#000}", "tokens.css": ":root{}"})
        return parts

    def test_an_untouched_kit_page_moves_to_the_current_kit(self):
        from zango.apps.agent_mode.prototype_kit import SPEC_PART, refresh_kit

        old = self.parts()
        new = refresh_kit(old, old, self.kit("draw2()"))
        self.assertIsNotNone(new)
        self.assertIn("draw2()", "".join(new.values()))
        self.assertEqual(new["look.css"], old["look.css"])
        self.assertEqual(new[SPEC_PART], "spec")
        # refreshed once, it is still "untouched" for the next kit
        self.assertIsNotNone(refresh_kit(new, old, self.kit("draw3()")))
        self.assertIsNone(refresh_kit(new, old, self.kit("draw2()")))

    def test_an_edited_kit_page_is_left_alone(self):
        from zango.apps.agent_mode.prototype_kit import refresh_kit

        pristine = self.parts()
        edited = {**pristine, "imported/styles.css": ".z-t{color:blue}"}
        self.assertIsNone(refresh_kit(edited, pristine, self.kit("draw2()")))
        self.assertIsNone(refresh_kit({"look.css": ""}, None, self.kit("draw2()")))



# ---- design features the kit and the runtime both draw (template 1.1.27) ----

import copy  # noqa: E402

import yaml  # noqa: E402

import spec_check  # noqa: E402


class DesignFeatureSpecTests(unittest.TestCase):
    """spec_check normalises the new design keys for the runtime and refuses bad values; the kit draws
    them from the same YAML (its markup is checked in KitDesignFeatureTests)."""

    @classmethod
    def setUpClass(cls):
        cls.raw = yaml.safe_load((SKILL / "evals" / "vendor_hub.yaml").read_text())

    def run_spec(self, edit):
        raw = copy.deepcopy(self.raw)
        edit(raw)
        S = spec_check.Spec(raw, "t.yaml")
        S.build()
        S.lint()
        S.prototype_screens()
        S.page_holes()
        S.derive()
        S.number_holes({})
        return S, [f"{i['where']}: {i['msg']}" for i in S.L.items if i["level"] == "error"]

    @staticmethod
    def ent(raw, code):
        return next(e for m in raw["modules"] for e in m["entities"] if e["code"] == code)

    @staticmethod
    def page(raw, code):
        return next(p for p in raw["pages"] if p["code"] == code)

    def test_list_stats_reach_the_metadata_and_the_ui(self):
        def edit(raw):
            self.page(raw, "purchase_orders")["stats"] = [
                {"label": "Open", "count": True, "where": "status not_in [closed, cancelled]", "tone": "blue", "icon": "inbox"},
                {"label": "Value", "sum": "total_amount", "format": "money", "hint": "All orders"}]
        S, errs = self.run_spec(edit)
        self.assertEqual(errs, [])
        st = S.M["pages"]["purchase_orders"]["stats"]
        self.assertEqual([s["key"] for s in st], ["s1", "s2"])
        self.assertIsNotNone(st[0]["ast"])
        ui = S.ui_json()["pages"]["purchase_orders"]["stats"]
        self.assertEqual(ui[1], {"key": "s2", "label": "Value", "format": "money", "hint": "All orders"})

    def test_bad_list_stats_are_errors(self):
        def edit(raw):
            self.page(raw, "purchase_orders")["stats"] = [
                {"label": "A", "sum": "po_ref"}, {"label": "B"}, {"label": "C", "count": True, "tone": "neon", "format": "date"},
                {"label": "D", "count": True, "where": "status == nope"}]
            self.page(raw, "dashboard")["stats"] = [{"label": "X", "count": True}]
        _, errs = self.run_spec(edit)
        text = " | ".join(errs)
        self.assertIn("'po_ref' is not a number field", text)
        self.assertIn("stat needs count: true or sum", text)
        self.assertIn("tone 'neon'", text)
        self.assertIn("format 'date'", text)
        self.assertIn("'nope' is not a status", text)
        self.assertIn("stats go on a crud page", text)

    def test_badge_progress_and_chevron(self):
        def edit(raw):
            tb = self.ent(raw, "purchase_order")["table"]
            tb["columns"][3] = {"expected_by": {"label": "Expected", "badge": {"label": "Late", "when": "expected_by < today", "tone": "red"}}}
            tb["columns"][6] = {"status": {"source": "status", "progress": {"steps": ["draft", "pending_approval", "approved", "closed"]}}}
            tb["row_chevron"] = True
        S, errs = self.run_spec(edit)
        self.assertEqual(errs, [])
        E = S.M["entities"]["purchase_order"]
        cols = {c["key"]: c for c in E["table"]["columns"]}
        self.assertIsNotNone(cols["expected_by"]["badge"]["ast"])
        ui = S.ui_json()["entities"]["purchase_order"]
        uc = {c["key"]: c for c in ui["columns"]}
        self.assertEqual(uc["status"]["progress"], {"steps": ["draft", "pending_approval", "approved", "closed"]})
        self.assertTrue(ui["row_chevron"])

    def test_progress_true_is_the_workflow_order(self):
        def edit(raw):
            self.ent(raw, "purchase_order")["table"]["columns"][6] = {"status": {"source": "status", "progress": True}}
        S, errs = self.run_spec(edit)
        self.assertEqual(errs, [])
        col = next(c for c in S.M["entities"]["purchase_order"]["table"]["columns"] if c["key"] == "status")
        self.assertEqual(col["progress"]["steps"][:3], ["draft", "pending_approval", "approved"])

    def test_bad_badge_progress_and_chevron_are_errors(self):
        def edit(raw):
            tb = self.ent(raw, "purchase_order")["table"]
            tb["columns"][0] = {"po_ref": {"badge": {"label": "New"}, "progress": True}}
            tb["columns"][3] = {"expected_by": {"badge": {"label": "Late", "when": "expected_by < today", "tone": "neon"}}}
            tb["columns"][6] = {"status": {"source": "status", "progress": {"steps": ["draft", "nope"]}}}
            tb["row_chevron"] = "yes"
        _, errs = self.run_spec(edit)
        text = " | ".join(errs)
        self.assertIn("badge needs `when`", text)
        self.assertIn("progress goes on a `source: status` column", text)
        self.assertIn("tone 'neon'", text)
        self.assertIn("not statuses of purchase_order: ['nope']", text)
        self.assertIn("row_chevron is true or false", text)

    def test_stepper_exits_where_the_record_left_the_steps(self):
        def edit(raw):
            raw_dv = next(v for v in raw["detail_views"] if v["code"] == "po_360")
            raw_dv.setdefault("header", {})["stepper"] = {"steps": ["draft", "pending_approval", "approved", "acknowledged", "closed"]}
        S, errs = self.run_spec(edit)
        self.assertEqual(errs, [])
        sp = S.ui_json()["detail_views"]["po_360"]["stepper"]
        # cancel runs from draft, pending_approval or approved: the furthest of them is approved (index 2)
        self.assertEqual(sp["exits"], {"partially_invoiced": 3, "cancelled": 2})

    def test_bad_steppers_are_errors(self):
        def edit(raw):
            next(v for v in raw["detail_views"] if v["code"] == "po_360").setdefault("header", {})["stepper"] = {"steps": ["draft", "nope"]}
        _, errs = self.run_spec(edit)
        self.assertIn("not statuses of purchase_order: ['nope']", " | ".join(errs))

        def edit2(raw):
            next(v for v in raw["detail_views"] if v["code"] == "po_360").setdefault("header", {})["stepper"] = "yes"
        _, errs = self.run_spec(edit2)
        self.assertIn("stepper is true, or {steps", " | ".join(errs))

    def test_menu_counts(self):
        def edit(raw):
            menu = next(r for r in raw["roles"] if r["name"] == "Finance")["menu"]
            menu[0]["count"] = {"where": "paid_on == null"}
            menu[1]["count"] = True
        S, errs = self.run_spec(edit)
        self.assertEqual(errs, [])
        items = S.M["roles"]["Finance"]["menu"]
        self.assertIsNotNone(items[0]["count"]["ast"])
        self.assertEqual(items[1]["count"], {"where": None, "ast": None})
        self.assertNotIn("count", self.raw["roles"][2]["menu"][0])  # the raw spec is not touched
        ui = S.ui_json()["menus"]["Finance"]["items"]
        self.assertEqual([i.get("count") for i in ui], [True, True])

    def test_bad_menu_counts_are_errors(self):
        def edit(raw):
            menu = next(r for r in raw["roles"] if r["name"] == "Procurement Manager")["menu"]
            menu[0]["count"] = True            # the dashboard: no entity
            menu[1]["count"] = {"where": "status == nope"}
            menu[2]["count"] = {"rows": 1}
        _, errs = self.run_spec(edit)
        text = " | ".join(errs)
        self.assertIn("count needs a crud page", text)
        self.assertIn("'nope' is not a status", text)
        self.assertIn("count is true, or {where", text)

    def test_shell_user(self):
        S, errs = self.run_spec(lambda raw: raw["app"].update(shell={"user": "top"}))
        self.assertEqual(errs, [])
        self.assertEqual(S.ui_json()["app"]["shell"], {"user": "top"})
        S, _ = self.run_spec(lambda raw: None)
        self.assertEqual(S.ui_json()["app"]["shell"], {"user": "bottom"})
        _, errs = self.run_spec(lambda raw: raw["app"].update(shell={"user": "left", "nav": "dark"}))
        text = " | ".join(errs)
        self.assertIn("app.shell.user 'left'", text)
        self.assertIn("does not know nav", text)


class KitDesignFeatureTests(unittest.TestCase):
    """The kit page draws each new key with the classes kit_vocab maps (the runtime draws their twins)."""

    def test_the_kit_renders_each_feature_with_its_classes(self):
        page = KIT_PAGE.read_text(encoding="utf-8")
        for needle in ("function listStats(", "function stepperHTML(", 'class="z-cpill"', 'class="z-cprog"',
                       'class="chev"', 'class="z-ni-n"', "M.app.shell.user === 'top'"):
            self.assertIn(needle, page)

    def test_the_runtime_draws_the_twins(self):
        src = "".join(p.read_text(encoding="utf-8") for p in RUNTIME.glob("*.tsx"))
        for needle in ('"zas-lstats"', '"zas-stepper"', '"zas-cpill"', '"zas-cprog"', 'className="chev"',
                       '"zas-sh-n"', '"zas-sh-foot top"', "zas_menu"):
            self.assertIn(needle, src)


class ZasCoreDesignFeatureTests(unittest.TestCase):
    """The table metadata and rows carry what the runtime draws (mixins.py, role-scoped)."""

    def test_mixins_compute_stats_badges_and_menu_counts(self):
        src = (SKILL / "assets" / "backend" / "zas_core" / "mixins.py").read_text(encoding="utf-8")
        self.assertIn('meta["zas"]["stats"]', src)
        self.assertIn('z.setdefault("badge", {})', src)
        self.assertIn("def _zas_menu_count", src)
        self.assertIn("access.scope_queryset", src[src.index("def _zas_menu_count"):])
