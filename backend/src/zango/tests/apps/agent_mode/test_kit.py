"""Free design: the app's kit is built from the prototype and compared with it, automatically.

Each piece the prototype shows is mapped (frontend/src/custom/kit/map.json) to one instance in a
prototype screen; zas_test.design --only kit crops it and scores it against the app's piece. Pieces
over the limit go to their own kit rounds; what is left is a report gap, never the verdict.
"""

import json
import shutil
import sys
import tempfile
import unittest

from pathlib import Path
from unittest import mock

from zango.apps.agent_mode import studio_build
from zango.apps.agent_mode.studio_build import LayerResult, StudioBuild, _merge_scoped
from zango.apps.agent_mode.studio_tools import SLICE_LAYERS, _paths
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir

from .test_studio_build import CREDS, FakeRun, StudioTestBase, manage_stub, results_writer


SKILL = Path(studio_plugin_dir()) / "skills" / "zango-app-studio"
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from zas_test import design, kit  # noqa: E402


def workspace(prototype=True):
    ws = Path(tempfile.mkdtemp(prefix="kit-"))
    (ws / "frontend" / "src" / "custom" / "kit").mkdir(parents=True)
    if prototype:
        screen = ws / ".zas" / "bundle" / "prototype" / "screens" / "requests"
        screen.mkdir(parents=True)
        (ws / ".zas" / "bundle" / "prototype" / "manifest.json").write_text("{}")
        (screen / "css.used.css").write_text(".btn.pri { background: #234635; color: rgb(255, 255, 255); }")
    return ws


def piece(**kw):
    p = {"id": "button-primary", "component": "Button", "props": {"variant": "primary", "children": "New"},
         "mockup": {"screen": "requests", "role": "maya", "selector": ".btn.pri"}}
    p.update(kw)
    return p


CAPTURE = {"requests": {"id": "requests", "roles": [{"role": "maya"}]}}


class KitMapTests(unittest.TestCase):
    def setUp(self):
        self.ws = workspace()
        self.addCleanup(shutil.rmtree, self.ws, True)

    def test_a_good_map_has_no_problems(self):
        self.assertEqual(kit.map_problems(str(self.ws), [piece()], CAPTURE), [])

    def test_the_map_names_a_real_screen_and_persona(self):
        probs = kit.map_problems(str(self.ws), [
            piece(mockup={"screen": "nope", "role": "maya", "selector": ".x"}),
            piece(id="b2", mockup={"screen": "requests", "role": "zed", "selector": ".x"}),
            piece(id="b3", mockup={"screen": "requests", "role": "maya"}),
        ], CAPTURE)
        self.assertIn("is not a prototype screen", probs[0])
        self.assertIn("has no persona 'zed'", probs[1])
        self.assertIn("needs screen, role and selector", probs[2])

    def test_table_and_shell_are_compared_on_the_screens_not_the_map(self):
        probs = kit.map_problems(str(self.ws), [piece(component="ZasTable")], CAPTURE)
        self.assertIn("compared on the screens", probs[0])

    def test_an_exported_piece_needs_a_map_entry(self):
        (self.ws / "frontend/src/custom/kit/index.ts").write_text(
            'import "./kit.css";\nexport { Button } from "./Button";\nexport const Panel = () => null;\n'
            "export { ZasTable } from './Table';\n")
        self.assertEqual(kit.exported_pieces(str(self.ws)), {"Button", "Panel", "ZasTable"})
        probs = kit.map_problems(str(self.ws), [piece()], CAPTURE)
        self.assertEqual(probs, ["kit/index.ts exports Panel but map.json has no piece for it: nothing compares it"])

    def test_duplicate_or_bad_ids(self):
        probs = kit.map_problems(str(self.ws), [piece(), piece(), piece(id="Bad Id")], CAPTURE)
        self.assertTrue(any("listed twice" in p for p in probs))
        self.assertTrue(any("lower-case" in p for p in probs))


class KitScoreTests(unittest.TestCase):
    def setUp(self):
        from PIL import Image, ImageDraw

        self.dir = Path(tempfile.mkdtemp(prefix="kitscore-"))
        self.addCleanup(shutil.rmtree, self.dir, True)

        def button(path, w, fill, text_x=12):
            im = Image.new("RGB", (w, 34), "white")
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((0, 0, w - 1, 33), 8, fill=fill)
            d.text((text_x, 11), "New request", fill="white" if fill != "white" else "black")
            im.save(path)
        button(self.dir / "m.png", 132, "#234635")
        button(self.dir / "same.png", 130, "#234635", text_x=11)  # 2 px narrower: the text moves
        button(self.dir / "other.png", 132, "white")

    def test_a_matching_piece_is_within_the_limit(self):
        s = kit.kit_score(str(self.dir / "same.png"), str(self.dir / "m.png"))
        self.assertLessEqual(s["score"], kit.KIT_LIMIT)

    def test_a_different_fill_is_far_over_it(self):
        s = kit.kit_score(str(self.dir / "other.png"), str(self.dir / "m.png"))
        self.assertGreater(s["score"], 0.5)


class KitLintTests(unittest.TestCase):
    def setUp(self):
        self.ws = workspace()
        self.addCleanup(shutil.rmtree, self.ws, True)
        self.Dx = design.D(None)
        self.Dx.ws, self.Dx.M = str(self.ws), {"app": {"design": {"tokens": {"brand": "#0F766E"}}}}

    def problems(self, rel, code):
        palette = design.prototype_palette(str(self.ws))
        return design.kit_problems(self.Dx, str(self.ws / rel), rel, code, palette)

    def test_the_prototype_palette_may_be_spelled_as_it_is(self):
        self.assertEqual(self.problems("kit.css", ".zas-btn.pri { background: #234635; color: rgb(255,255,255) }"), [])
        probs = self.problems("kit.css", ".zas-btn.pri { background: #ff00aa }")
        self.assertIn("#ff00aa", probs[0])

    def test_kit_css_restyles_kit_markup_only(self):
        probs = self.problems("kit.css", "body { margin: 0 } .zk-card, [data-zas=page] { padding: 4px }")
        self.assertEqual(len(probs), 1)
        self.assertIn("`body`", probs[0])

    def test_a_piece_imports_the_base_kit_not_itself(self):
        good = 'import { Button as Base } from "../../zas/ui";\n'
        bad = 'import { Button as Base } from "../../zas";\n'
        self.assertEqual(self.problems("Button.tsx", good), [])
        self.assertIn("re-exports the kit itself", self.problems("Button.tsx", bad)[0])


class KitRoundTests(StudioTestBase):
    def setUp(self):
        super().setUp()
        zas = self.ws / ".zas"
        zas.mkdir()
        (zas / "spec.resolved.json").write_text(json.dumps({"app": {}, "roles": {}, "modules": []}))
        (zas / "test_users.json").write_text("{}")
        (zas / "menu_icons.json").write_text("{}")
        (self.ws / "frontend" / "src" / "custom" / "kit").mkdir(parents=True)

    def finish(self, kit_records, rounds=2):
        fake = FakeRun(self.ws, {
            "zas_test.api": results_writer(self.ws, "api", lambda a: []),
            "zas_test.design": results_writer(self.ws, "design", kit_records),
            "zas_test.scenarios": results_writer(self.ws, "scenarios", lambda a: []),
        })
        digests = []

        def agent(digest):
            digests.append(digest)
            if digest.startswith("Kit round"):  # the agent restyles its kit
                (self.ws / "frontend/src/custom/kit/kit.css").write_text(f"/* {len(digests)} */")
            return True
        with mock.patch.object(studio_build.subprocess, "run", fake), mock.patch.object(
            studio_build, "run_step", manage_stub([])
        ), mock.patch.object(StudioBuild, "app_reachable", return_value=(True, "")), mock.patch.object(
            StudioBuild, "has_playwright", return_value=True
        ), mock.patch.object(studio_build, "look_rounds", return_value=0):
            outcome = self.build(first_build=False).finish(CREDS, resume_agent=agent, rounds=rounds)
        return outcome, digests

    @staticmethod
    def gap(ok=False):
        return [{"id": "design.lint", "status": "pass"},
                {"id": "design.kit.button-primary", "title": "kit piece", "spec_path": "kit.button-primary",
                 "status": "pass" if ok else "fail", "detail": "18% different from the prototype's piece"}]

    def test_kit_gaps_get_kit_rounds_not_fix_rounds_and_never_fail_the_build(self):
        outcome, digests = self.finish(lambda a: self.gap())
        self.assertEqual(len(digests), studio_build.kit_rounds())
        self.assertTrue(all(d.startswith("Kit round") for d in digests))
        self.assertIn("button-primary", digests[0])
        self.assertIn("last kit round", digests[-1])
        self.assertTrue(outcome.ok)  # a look gap: the internal report, not the verdict

    def test_kit_rounds_stop_when_every_piece_matches(self):
        state = {"fixed": False}

        def records(argv):
            state["fixed"] = state["fixed"] or (self.ws / "frontend/src/custom/kit/kit.css").is_file()
            return self.gap(ok=state["fixed"])
        outcome, digests = self.finish(records)
        self.assertEqual(len(digests), 1)
        self.assertTrue(outcome.ok)

    def test_a_scoped_rerun_replaces_only_the_kit_checks(self):
        old = LayerResult(name="design", status="fail", failures=[
            {"id": "design.parity.proto.home.maya", "detail": "x"}, {"id": "design.kit.b", "detail": "y"}])
        merged = _merge_scoped(old, LayerResult(name="design", status="pass"), "design.kit")
        self.assertEqual([f["id"] for f in merged.failures], ["design.parity.proto.home.maya"])
        self.assertEqual(merged.status, "fail")


class SliceToolKitTests(unittest.TestCase):
    def test_the_slice_check_takes_the_kit(self):
        self.assertEqual(_paths({"paths": ["kit", "entities.case", "kit.button-primary", "nonsense"]}),
                         ["kit", "entities.case", "kit.button-primary"])
        self.assertIn("kit", SLICE_LAYERS["design"])


class RuntimeKitTests(unittest.TestCase):
    """The runtime draws with the app's kit; the stub keeps the default."""

    def test_runtime_pages_import_pieces_through_the_kit(self):
        zas = SKILL / "assets" / "frontend" / "zas"
        for f in ("ZasTable.tsx", "Detail360.tsx", "ListPage.tsx", "dialogs.tsx", "renderers.tsx", "CustomPage.tsx"):
            src = (zas / f).read_text()
            self.assertIn('from "./kit"', src, f)
            for name in ("Button", "Badge", "Panel", "Drawer", "Modal", "ZasTable"):
                line = next((ln for ln in src.splitlines() if ln.startswith("import {") and 'from "./ui"' in ln), "")
                self.assertNotRegex(line, rf"\b{name}\b", f"{f} imports {name} from ./ui")

    def test_the_kit_lists_the_same_pieces_as_the_check(self):
        src = (SKILL / "assets" / "frontend" / "zas" / "kit.tsx").read_text()
        for name in kit.KIT_PIECES:
            self.assertIn(f'"{name}"', src)

    def test_the_stub_exports_nothing(self):
        stub = SKILL / "assets" / "templates" / "frontend" / "kit"
        self.assertEqual(json.loads((stub / "map.json").read_text()), {"pieces": []})
        ws = workspace(prototype=False)
        self.addCleanup(shutil.rmtree, ws, True)
        shutil.copy(stub / "index.ts", ws / "frontend/src/custom/kit/index.ts")
        self.assertEqual(kit.exported_pieces(str(ws)), set())


if __name__ == "__main__":
    unittest.main()
