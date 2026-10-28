"""Free design, port mode: screens are copied from the approved prototype's own code, not redrawn.

The platform hands the build the prototype's stylesheet (scoped under .zp) and its source; the lint lets
ported code keep the prototype's colours and inline styles; parity compares with references that really
are the screen, fills route params, and scores layout, not brightness; the app opens on demo data.
"""

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest

from pathlib import Path
from unittest import mock

from zango.apps.agent_mode import studio_build
from zango.apps.agent_mode.studio_build import StudioBuild
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir

from .test_studio_build import StudioTestBase


SKILL = Path(studio_plugin_dir()) / "skills" / "zango-app-studio"
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import proto_landmarks as PL  # noqa: E402
import proto_port  # noqa: E402
import zango_platform  # noqa: E402

from zas_test import browser, design, kit  # noqa: E402


def worker():
    path = Path(studio_build.__file__).with_name("preview_probe_worker.py")
    spec = importlib.util.spec_from_file_location("preview_probe_worker", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PAGE = """<!doctype html><html><head>
<style data-zas="runtime">.z-pill{color:#123}</style>
<style data-part="app/styles.css">
:root{--brand:#3F52A8} html,body{margin:0;height:100%;overflow:hidden;font-family:'Inter',sans-serif;color:#1F2330}
.btn{background:var(--brand)} .a,.b:is(.c,.d){color:#B23A2A}
@media (max-width:800px){body .card{padding:4px}}
@keyframes spin{to{transform:rotate(1turn)}}
</style>
<script type="application/json" id="zas-proto">{"title":"x"}</script>
<script src="https://unpkg.com/lib.js"></script>
<script data-zas="runtime">window.ZAS={}</script>
<script data-part="app/app.js">
const DOT = { ok: "#476E4D" };
function Dashboard() {
  return 1;
}
const Pill = () => null;
</script>
</head><body><div id="root"></div></body></html>"""


def workspace(page=PAGE):
    ws = Path(tempfile.mkdtemp(prefix="port-"))
    proto = ws / ".zas" / "bundle" / "prototype"
    proto.mkdir(parents=True)
    (proto / "manifest.json").write_text(json.dumps({
        "roles": {"doc": "Doctor", "adm": "Admin"}, "personas": {"doc": {"name": "Dr. Asha Rao"}},
        "home": {"doc": "home"}}))
    (proto / "prototype.html").write_text(page)
    (ws / "frontend" / "src" / "custom").mkdir(parents=True)
    return ws


class ProtoPortTests(unittest.TestCase):
    def setUp(self):
        self.ws = workspace()
        self.addCleanup(shutil.rmtree, self.ws, True)

    def test_every_rule_is_scoped_and_the_page_box_is_dropped(self):
        css = proto_port.scope_css(".x{color:red} :root{--a:1} html,body{margin:0;overflow:hidden;color:#111}"
                                   " body.dark .y{color:blue} .a,.b:is(.c,.d){top:0}"
                                   " @media (min-width:1px){html .z{left:0}} @keyframes k{to{opacity:0}}")
        self.assertIn(".zp .x{color:red}", css)
        self.assertIn(".zp{--a:1}", css)
        self.assertIn(".zp,.zp{color:#111}", css)  # margin and overflow belong to the app shell
        self.assertNotIn("overflow", css)
        self.assertIn(".zp.dark .y{color:blue}", css)
        self.assertIn(".zp .a,.zp .b:is(.c,.d){top:0}", css)  # a comma inside :is() is not a selector list
        self.assertIn("@media (min-width:1px){.zp .z{left:0}}", css)
        self.assertIn("@keyframes k{to{opacity:0}}", css)

    def test_run_writes_the_stylesheet_and_the_source_without_the_runtime(self):
        out = proto_port.run(str(self.ws))
        css = (self.ws / "frontend/src/custom/prototype.css").read_text()
        self.assertIn(".zp .btn{background:var(--brand)}", css)
        self.assertNotIn(".z-pill", css)  # the zas runtime's own style
        self.assertEqual(out["files"], ["app/styles.css", "app/app.js"])
        index = (self.ws / ".zas/bundle/prototype/source/index.md").read_text()
        self.assertIn("2: `DOT`", index)
        self.assertIn("3: `Dashboard`", index)
        self.assertIn("6: `Pill`", index)
        self.assertNotIn("window.ZAS", (self.ws / ".zas/bundle/prototype/source/app/app.js").read_text())

    def test_a_bundled_library_is_named_not_outlined(self):
        lines = proto_port.outline("source/vendor.js", "var a=" + "x" * 5000 + ";")
        self.assertIn("bundled library", lines[2])

    def test_no_prototype_no_work(self):
        ws = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, ws, True)
        self.assertEqual(proto_port.run(str(ws)), {"skipped": "no prototype bundle"})


class PortLintTests(unittest.TestCase):
    def setUp(self):
        self.ws = workspace()
        self.addCleanup(shutil.rmtree, self.ws, True)
        proto_port.run(str(self.ws))
        self.Dx = design.D(None)
        self.Dx.ws, self.Dx.M = str(self.ws), {"app": {"design": {"tokens": {"brand": "#3F52A8"}}}, "roles": {}}

    def lint(self):
        self.Dx.results = []
        design.g_lint(self.Dx)
        return next(r for r in self.Dx.results if r["id"] == "design.lint")

    def write(self, rel, code):
        p = self.ws / "frontend/src/custom" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(code)

    def test_ported_code_keeps_the_prototypes_colours_and_inline_styles(self):
        self.write("slots/Home.tsx", 'const DOT = { ok: "#476E4D" };\n'
                   'export default () => <div className="zp" style={{ background: DOT.ok, color: "#B23A2A",'
                   ' fontFamily: "Inter" }} />;\n')
        problems = [p for p in self.lint()["detail"].splitlines() if "Home.tsx" in p]
        self.assertEqual(problems, [])

    def test_a_colour_the_prototype_never_uses_fails(self):
        self.write("slots/Home.tsx", 'export default () => <div style={{ color: "#ff00aa" }} />;\n')
        self.assertIn("#ff00aa` is not in the approved prototype", self.lint()["detail"])

    def test_the_prototype_stylesheet_is_the_platforms(self):
        self.assertNotIn("prototype.css", self.lint()["detail"])
        p = self.ws / "frontend/src/custom/prototype.css"
        p.write_text(p.read_text() + ".zp .mine{color:#1F2330}\n")
        self.assertIn("prototype.css: edited", self.lint()["detail"])

    def test_any_other_stylesheet_still_fails(self):
        self.write("slots/home.css", ".x{color:red}")
        self.assertIn("slots/home.css: stylesheet in src/custom", self.lint()["detail"])


class ShellLintTests(unittest.TestCase):
    def setUp(self):
        self.ws = workspace()
        self.addCleanup(shutil.rmtree, self.ws, True)
        (self.ws / "frontend/src/App.tsx").write_text("<ZApp customComponents={{ Layout: Shell }} />")

    def shell(self, code):
        (self.ws / "frontend/src/custom/Shell.tsx").write_text(code)
        return design.open_shell_problems(str(self.ws))

    def test_options_or_a_port_around_the_platform_menu(self):
        self.assertEqual(self.shell('export default makeShell({ nav: "card" });'), [])
        ported = ('import { shellMenu, UserCard } from "../zas";\nexport default function Shell({ menu, profileInfo, children })'
                  ' { const items = shellMenu(menu, "", []); return <div className="zp" data-zas="shell">'
                  '<a data-zas="shell-nav" /><UserCard user={profileInfo} up />{children}</div>; }')
        self.assertEqual(self.shell(ported), [])

    def test_a_port_with_a_hard_coded_menu_fails(self):
        probs = self.shell('export default function Shell({ children }) { return <div data-zas="shell">'
                           '<a href="/app/cases">My cases</a>{children}</div>; }')
        self.assertIn("shellMenu", probs[0])
        self.assertIn("UserCard", probs[0])


class CaptureTests(unittest.TestCase):
    def test_a_screen_that_shows_another_has_no_reference(self):
        out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out, True)
        home = "<h1>Good afternoon</h1>" + "".join(f"<td>row {i}</td>" for i in range(30))
        pages = {"form": home + "<div>Saved</div>", "home": home, "help": "<h1>Help</h1><p>Call us</p>"}
        summary = {"screens": []}
        for sid, html in pages.items():  # form first: the home still keeps the page
            (out / "screens" / sid).mkdir(parents=True)
            (out / "screens" / sid / "dom.doc.html").write_text(html)
            summary["screens"].append({"id": sid, "roles": [{"role": "doc", "files": ["dom.doc.html"]}]})
        worker().did_not_open(summary, str(out), {"home": {"doc": "home"}})
        errors = {s["id"]: s["roles"][0].get("error") for s in summary["screens"]}
        self.assertIn("did not open form: it showed home", errors["form"])
        self.assertIsNone(errors["home"])
        self.assertIsNone(errors["help"])


class ParityTests(unittest.TestCase):
    def test_shell_labels_are_those_on_a_third_of_the_screens(self):
        proto = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, proto, True)
        nav = "<aside><button>My cases</button><button>Open screens</button></aside>"
        capture = {}
        for i in range(6):  # four screens with the sidebar, two bare link pages
            sid = f"s{i}"
            (proto / "screens" / sid).mkdir(parents=True)
            word = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot"][i]
            body = (nav if i < 4 else "") + f"<main><h1>{word} title</h1><button>Only {word}</button></main>"
            (proto / "screens" / sid / "dom.doc.html").write_text(body)
            capture[sid] = {"id": sid, "roles": [{"role": "doc"}]}
        chrome = design.shell_chrome(str(proto), capture, PL)["doc"]
        self.assertIn("my cases", chrome)
        self.assertIn("open screens", chrome)
        self.assertNotIn("only bravo", chrome)

    def test_a_route_param_is_a_record_of_the_page_it_sits_under(self):
        M = {"pages": {"cases": {"type": "crud", "entity": "case", "route": "/app/cases"},
                       "link": {"type": "custom", "route": "/app/r/:token"}},
             "entities": {"case": {"names": {"endpoint": "/cases/case/"}}}}
        sess = mock.Mock()
        sess.get.return_value.json.return_value = {"data": [{"object_uuid": "u2"}]}
        self.assertEqual(browser.fill_route(M, "/app/cases/:id/review", {"case": ["u1", "u2"]}, sess),
                         ("/app/cases/u2/review", None))
        path, why = browser.fill_route(M, "/app/r/:token", {}, sess)
        self.assertIsNone(path)
        self.assertIn("names no record", why)

    def test_a_greeting_follows_the_clock(self):
        gaps = PL.content_gaps("<h1>Good afternoon, Dr. Mehta</h1>", "<h1>Good morning, Dr. Mehta</h1>",
                               "Good morning, Dr. Mehta", ignore_words=["Dr. Rahul Mehta"])
        self.assertEqual(gaps, [])
        gaps = PL.content_gaps("<h1>Good afternoon, Dr. Mehta</h1>", "<h1>Welcome</h1>", "Welcome",
                               ignore_words=["Dr. Rahul Mehta"])
        self.assertIn("missing title", gaps[0])

    def test_raw_timestamps_are_a_problem(self):
        self.assertIn("raw timestamps", browser.raw_dates("Created 2026-10-28T03:45:48.336303+00:00"))
        self.assertIsNone(browser.raw_dates("Created 28 Oct 2026, 9:15 AM"))


class LookScoreTests(unittest.TestCase):
    def test_layout_counts_colour_barely_does(self):
        from PIL import Image, ImageDraw

        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)

        def page(path, boxes, fill="#334"):
            im = Image.new("RGB", (1280, 900), "white")
            dr = ImageDraw.Draw(im)
            for b in boxes:
                dr.rectangle(b, outline="#99a", width=2)
                dr.text((b[0] + 12, b[1] + 12), "Some label 123", fill=fill)
            im.save(path)
        cards = [(40 + i * 300, 40, 300 + i * 300, 180) for i in range(4)] + [(40, 220, 1240, 860)]
        page(d / "a.png", cards)
        page(d / "same.png", cards, fill="#a33")  # the same layout in another colour
        page(d / "other.png", [(40, 40, 600, 860), (640, 40, 1240, 400), (640, 440, 1240, 860)])
        same = design.look_score(str(d / "same.png"), str(d / "a.png"))
        other = design.look_score(str(d / "other.png"), str(d / "a.png"))
        self.assertLess(same, 0.1)
        self.assertGreater(other, 0.25)
        self.assertEqual(design.look_score(str(d / "a.png"), str(d / "a.png")), 0.0)


class KitOptionalTests(unittest.TestCase):
    def test_no_kit_pieces_is_fine_when_every_screen_is_ported(self):
        ws = workspace()
        self.addCleanup(shutil.rmtree, ws, True)
        (ws / "frontend/src/custom/kit").mkdir()
        (ws / "frontend/src/custom/kit/map.json").write_text('{"pieces": []}')
        Dx = design.D(None)
        Dx.ws, Dx.M = str(ws), {"prototype": {"screens": [{"id": "home", "cls": "rebuild"}]}}
        kit.g_kit(Dx, None)
        self.assertEqual([(r["id"], r["status"]) for r in Dx.results], [("design.kit", "skip")])
        Dx.results, Dx.M = [], {"prototype": {"screens": [{"id": "list", "cls": "kit"}]}}
        kit.g_kit(Dx, None)
        self.assertEqual(Dx.results[0]["status"], "fail")
        self.assertIn("kit pages (list)", Dx.results[0]["detail"])


class PersonaTests(unittest.TestCase):
    def test_the_test_user_is_the_prototypes_persona(self):
        ws = workspace()
        self.addCleanup(shutil.rmtree, ws, True)
        self.assertEqual(zango_platform.persona_name(str(ws), "Doctor"), "Dr. Asha Rao")
        self.assertIsNone(zango_platform.persona_name(str(ws), "Admin"))  # no persona name for it
        self.assertIsNone(zango_platform.persona_name(str(ws), "Nurse"))


class LookRoundTests(StudioTestBase):
    """Free design: the look rounds run on the score, not a fixed count."""

    def setUp(self):
        super().setUp()
        (self.ws / ".zas" / "bundle" / "prototype").mkdir(parents=True)
        (self.ws / ".zas" / "bundle" / "prototype" / "manifest.json").write_text("{}")
        (self.ws / "frontend" / "src" / "custom").mkdir(parents=True)

    def run_rounds(self, rounds_of_scores, change=True):
        """rounds_of_scores[i]: {screen: score} after round i (0 = before the first)."""
        build = self.build(first_build=False)
        shots = iter(rounds_of_scores)
        digests = []

        def shoot():
            looks = [{"screen": f"prototype/{k}", "role": "Doctor", "kind": "prototype", "score": v,
                      "approved": f"a/{k}.png", "built": f"b/{k}.png"} for k, v in next(shots).items()]
            (self.ws / ".zas" / "parity_looks.json").write_text(json.dumps(looks))
            return {"design": studio_build.LayerResult(name="design")}

        def agent(digest):
            digests.append(digest)
            if change:
                (self.ws / "frontend/src/custom/Slot.tsx").write_text(str(len(digests)))
            return True
        shoot()
        with mock.patch.object(StudioBuild, "verify", side_effect=lambda *a, **k: shoot()), \
                mock.patch.object(StudioBuild, "bring_up", return_value=True):
            ok = build.prototype_look_rounds({}, {}, agent, None, False, (), ())
        history = json.loads((self.ws / ".zas" / "look_rounds.json").read_text())
        return ok, digests, history

    def test_rounds_go_on_while_screens_get_closer_and_stop_when_all_are_within_the_limit(self):
        ok, digests, history = self.run_rounds([{"home": 0.58, "list": 0.12}, {"home": 0.40, "list": 0.12},
                                                {"home": 0.20, "list": 0.12}])
        self.assertTrue(ok)
        self.assertEqual(len(digests), 2)
        self.assertIn("prototype/home", digests[0])
        self.assertNotIn("prototype/list", digests[0])  # already within the limit: not sent
        self.assertEqual([h["scores"]["prototype/home|Doctor"] for h in history], [0.58, 0.40, 0.20])

    def test_a_round_that_brings_nothing_closer_is_the_last(self):
        ok, digests, _ = self.run_rounds([{"home": 0.58}, {"home": 0.57}, {"home": 0.30}])
        self.assertEqual(len(digests), 1)

    def test_never_more_than_the_cap(self):
        scores = [{"home": 0.9 - 0.1 * i} for i in range(8)]
        from django.test.utils import override_settings

        with override_settings(AGENT_MODE_LOOK_MAX_ROUNDS=3):
            _, digests, _ = self.run_rounds(scores)
        self.assertEqual(len(digests), 3)

    def test_the_report_shows_the_path(self):
        from zas_test import report

        r = {"id": "home", "score": 0.2, "rounds": [0.58, 0.4, 0.2]}
        self.assertEqual(report.look_path(r), "58% → 40% → 20%")
        self.assertEqual(report.look_path({"score": 0.2, "rounds": [0.2]}), "20%")


class DemoDataTests(StudioTestBase):
    def test_the_loader_runs_only_when_the_build_wrote_one(self):
        build = self.build(first_build=False)
        with mock.patch.object(StudioBuild, "manage") as manage:
            self.assertIsNone(build.load_demo_data())
            manage.assert_not_called()
            (self.ws / "backend").mkdir(exist_ok=True)
            (self.ws / "backend" / "demo_data.py").write_text("def load(users):\n    return {}\n")
            manage.return_value = mock.Mock(returncode=0)
            self.assertIsNone(build.load_demo_data())
            self.assertEqual(manage.call_args[0][1][:2], ["agent_mode_demo_data", build.app_name])
            manage.return_value = mock.Mock(returncode=1, stderr_tail="KeyError: 'status'", stdout_tail="")
            failure = build.load_demo_data()
        self.assertEqual(failure["id"], "design.demo_data")
        self.assertIn("KeyError", failure["detail"])
        self.assertEqual(studio_build._group_of("design", failure["id"]), "parity")  # re-run: loads again


if __name__ == "__main__":
    unittest.main()
