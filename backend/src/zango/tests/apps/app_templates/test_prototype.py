"""Open prototype (P1): parts, assembly, the proto_* tools and the ZAS runtime.

In open mode the analyst writes the app's prototype as parts; prototype.assemble joins them into
one sandboxed page. The headless tests boot the skill's worked example (a fictional lab) through
every screen and persona and walk one action, with the runtime the console injects.
"""

import json
import unittest

from pathlib import Path

from zango.apps.agent_mode import prototype as P
from zango.apps.agent_mode.preview_probe import playwright_available


EXAMPLE = (
    Path(P.__file__).parent
    / "skill_plugin"
    / "skills"
    / "zango-prototype"
    / "references"
    / "example"
)


def example_parts() -> dict:
    return {
        str(p.relative_to(EXAMPLE)): p.read_text()
        for p in sorted(EXAMPLE.rglob("*"))
        if p.is_file()
    }


MANIFEST = json.dumps(
    {
        "title": "T",
        "roles": {"a": "Office", "b": "Requester"},
        "screens": [{"id": "home", "title": "Home"}, {"id": "list", "title": "List"}],
    }
)


class AssemblyTests(unittest.TestCase):
    def test_load_order_csp_and_part_names(self):
        parts = {
            "manifest.json": MANIFEST,
            "screens/list.js": "ZAS.screen('list', () => 'L')",
            "screens/home.js": "ZAS.screen('home', () => 'H')",
            "shell.js": "ZAS.shell((c, b) => b)",
            "data.js": "ZAS.seed({})",
            "app.css": "body{}",
            "tokens.css": ":root{}",
            "lib/x.js": "window.X = 1",
        }
        html = P.assemble(parts)
        order = [html.index(f'data-part="{p}"') for p in (
            "tokens.css", "app.css", "data.js", "shell.js", "lib/x.js", "screens/home.js", "screens/list.js"
        )]
        self.assertEqual(order, sorted(order))
        self.assertIn('http-equiv="Content-Security-Policy"', html)
        self.assertIn("connect-src data: blob:", P.CSP)
        self.assertIn("//# sourceURL=proto/screens/home.js", html)
        self.assertTrue(html.rstrip().endswith("<script>ZAS.boot()</script>\n</body></html>"))

    def test_closing_tags_inside_parts_are_escaped(self):
        html = P.assemble({"manifest.json": MANIFEST, "data.js": "const s = '</script><b>'"})
        self.assertIn("'<\\/script><b>'", html)

    def test_manifest_problems(self):
        manifest = json.loads(MANIFEST)
        manifest["libraries"] = ["https://evil.example/x.js", "https://unpkg.com/chart.js/dist/chart.js"]
        manifest["fonts"] = ["https://fonts.example/x.css"]
        problems = P.static_problems({"manifest.json": json.dumps(manifest)})
        text = "\n".join(problems)
        self.assertIn("not allowed", text)
        self.assertIn("pin an exact version", text)
        self.assertIn("fonts URL not allowed", text)
        self.assertIn("screens/home.js, screens/list.js", text)
        self.assertNotIn("evil.example", P.assemble({"manifest.json": json.dumps(manifest)}))


class BenchTests(unittest.TestCase):
    def setUp(self):
        self.emitted = []
        self.pb = P.PrototypeBench({}, self.emitted.append)

    def test_write_patch_read_find(self):
        self.pb.write("manifest.json", MANIFEST)
        out = self.pb.write("screens/home.js", "ZAS.screen('home', () => 'Hi there')")
        self.assertIn("1/2 screens written", out)
        self.assertIn("screens/list.js", out)
        self.pb.patch("screens/home.js", "Hi there", "Hello")
        self.assertIn("Hello", self.pb.parts["screens/home.js"])
        self.assertIn("screens/home.js:1:", self.pb.find("hello"))
        self.assertIn("    1  ZAS.screen", self.pb.read("screens/home.js"))
        last = self.emitted[-1]
        self.assertEqual(last["prototype_hash"], P.parts_hash(self.pb.parts))
        self.assertEqual(set(last["prototype_parts"]), {"manifest.json", "screens/home.js"})

    def test_refusals(self):
        self.pb.write("data.js", "const a = 1; const b = 1;")
        with self.assertRaisesRegex(P.ProtoRefused, "Found 2 times"):
            self.pb.patch("data.js", "= 1", "= 2")
        self.pb.patch("data.js", "= 1", "= 2", all_=True)
        self.assertEqual(self.pb.parts["data.js"], "const a = 2; const b = 2;")
        with self.assertRaisesRegex(P.ProtoRefused, "Not found"):
            self.pb.patch("data.js", "nope", "x")
        with self.assertRaisesRegex(P.ProtoRefused, "valid JSON"):
            self.pb.write("manifest.json", "{")
        with self.assertRaisesRegex(P.ProtoRefused, "not a valid part path"):
            self.pb.write("../etc/passwd.js", "")
        with self.assertRaisesRegex(P.ProtoRefused, "per part"):
            self.pb.write("big.css", "x" * (P.MAX_PART_BYTES + 1))
        if P._node():
            with self.assertRaisesRegex(P.ProtoRefused, "does not parse"):
                self.pb.write("screens/bad.js", "function (")
        self.assertNotIn("screens/bad.js", self.pb.parts)

    def test_drafting_until_every_screen_has_a_part(self):
        self.assertTrue(P.is_drafting({}))
        self.pb.write("manifest.json", MANIFEST)
        self.pb.write("screens/home.js", "1")
        self.assertTrue(P.is_drafting(self.pb.parts))
        self.pb.write("screens/list.js", "2")
        self.assertFalse(P.is_drafting(self.pb.parts))

    def test_rename_and_remove(self):
        self.pb.write("screens/a.js", "1")
        self.pb.rename("screens/a.js", "screens/b.js")
        self.assertEqual(list(self.pb.parts), ["screens/b.js"])
        self.pb.remove("screens/b.js")
        self.assertEqual(self.pb.parts, {})
        self.assertIn("No prototype yet", self.pb.outline())

    def test_tools_are_registered_on_the_spec_server(self):
        from zango.apps.agent_mode.spec_tools import ALLOWED_TOOL_NAMES, ToolRefused

        specs = P.proto_tool_specs(self.pb)
        self.assertEqual(tuple(s[0] for s in specs), P.PROTO_TOOL_NAMES)
        for name in P.PROTO_TOOL_NAMES:
            self.assertIn(f"mcp__spec__{name}", ALLOWED_TOOL_NAMES)
        patch = dict((s[0], s[3]) for s in specs)["proto_patch"]
        with self.assertRaises(ToolRefused):
            patch({"part": "missing.js", "find": "a", "replace": "b"})


PAGE = """<!doctype html><html><head><meta charset=utf8><title>Field Visits</title>
<link href="https://fonts.googleapis.com/css2?family=Inter&display=swap" rel="stylesheet">
<style>body{margin:0}</style></head><body>
<style>.card{border:1px solid #ddd}</style>
<script src="https://cdn.jsdelivr.net/npm/dayjs@1.11.10/dayjs.min.js"></script>
<script src="https://evil.example/x.js"></script>
<script type="application/json" id="seed">{"visits": 2}</script>
<div id="root"></div>
<script>
let S = {who: 'rep', sec: 'home'};
const css = '<style>.not-a-style-element{}</style>';
function render() {
  document.getElementById('root').innerHTML = S.sec === 'home'
    ? '<h1>Home for ' + S.who + '</h1>' : '<h1>Visits</h1>';
}
render();
</script></body></html>"""

BRIDGE = (
    "ZAS.ready({go(screen, o) { if (o.role) S.who = o.role; S.sec = screen; render(); "
    "ZAS.at(screen, {role: S.who}); }});"
)


class ImportTests(unittest.TestCase):
    def test_page_is_split_without_changing_its_code(self):
        parts, notes = P.import_html(PAGE)
        manifest = json.loads(parts["manifest.json"])
        self.assertEqual(manifest["title"], "Field Visits")
        self.assertEqual(manifest["source"], "imported")
        self.assertEqual(manifest["fonts"], ["https://fonts.googleapis.com/css2?family=Inter&display=swap"])
        self.assertEqual(manifest["libraries"], ["https://cdn.jsdelivr.net/npm/dayjs@1.11.10/dayjs.min.js"])
        self.assertIn("body{margin:0}", parts["imported/styles.css"])
        self.assertIn(".card{", parts["imported/styles.css"])
        # A "<style" inside a script string stays in the script.
        self.assertIn("not-a-style-element", parts["imported/script-01.js"])
        self.assertNotIn("not-a-style-element", parts["imported/styles.css"])
        self.assertIn('id="seed"', parts["body.html"])
        self.assertIn('<div id="root">', parts["body.html"])
        self.assertNotIn("<title>", parts["body.html"])
        self.assertTrue(any("evil.example" in n for n in notes))

    def test_imported_prototype_rules(self):
        pb = P.PrototypeBench({}, lambda e: None, documents={"Field Visits.html": PAGE})
        out = pb.import_document("field visits.html")
        self.assertIn("Imported Field Visits.html", out)
        self.assertFalse(P.is_drafting(pb.parts))  # its screens are drawn by its own code
        self.assertTrue(any("ZAS.ready" in p for p in P.static_problems(pb.parts)))
        pb.write("zas-bridge.js", BRIDGE)
        self.assertFalse(any("ZAS.ready" in p for p in P.static_problems(pb.parts)))
        # Imported parts may be larger than a written part.
        pb.write("imported/big.css", "x" * (P.MAX_PART_BYTES + 10))
        with self.assertRaisesRegex(P.ProtoRefused, "No uploaded HTML file"):
            pb.import_document("other.html")

    def test_html_documents_are_accepted_with_an_outline(self):
        from zango.apps.agent_mode.documents import extract

        doc = extract("Field Visits.html", PAGE.encode())
        self.assertEqual(doc.content_type, "text/html")
        self.assertIn("Title: Field Visits", doc.text)
        self.assertIn("proto_import", doc.text)


class ApprovalTests(unittest.TestCase):
    def test_open_mode_does_not_ask_for_sketches(self):
        from zango.apps.agent_mode.template_spec import unfinished_custom_work

        spec = "pages:\n  - code: board\n    type: custom\n    text: A board\n"
        with_sketches = unfinished_custom_work(spec)
        without = unfinished_custom_work(spec, sketches=False)
        self.assertTrue(any("sketch" in i["message"] for i in with_sketches))
        self.assertFalse(any("sketch" in i["message"] for i in without))


@unittest.skipUnless(playwright_available(), "Playwright is not installed")
class RuntimeTests(unittest.TestCase):
    def _page(self, browser, html):
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.set_content(html)
        page.wait_for_function("window.ZAS && ZAS.state.screen")
        return page, errors

    def test_example_draws_every_screen_for_every_persona(self):
        from playwright.sync_api import sync_playwright

        parts = example_parts()
        self.assertEqual(P.static_problems(parts), [])
        manifest, _ = P.manifest_of(parts)
        html = P.assemble(parts)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page, errors = self._page(browser, html)
                for role in manifest["roles"]:
                    for screen in manifest["screens"]:
                        if screen.get("roles") and role not in screen["roles"]:
                            continue
                        record = "LS-24-0418" if screen.get("record") else None
                        page.evaluate("([s, r, rec]) => ZAS.go(s, {role: r, record: rec})", [screen["id"], role, record])
                        drawn = page.evaluate("ZAS.state.screen")
                        self.assertEqual(drawn, screen["id"], f"{role} could not open {screen['id']}")
                        text = page.inner_text("[data-zas-screen]")
                        self.assertTrue(text.strip(), f"{screen['id']} drew nothing for {role}")
                        self.assertNotIn("failed to draw", text)
                self.assertEqual(page.evaluate("ZAS.errors"), [])
                self.assertEqual(errors, [])
            finally:
                browser.close()

    def test_an_action_changes_the_store_and_redraws(self):
        from playwright.sync_api import sync_playwright

        html = P.assemble(example_parts())
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page, errors = self._page(browser, html)
                page.evaluate("ZAS.go('sample', {role: 'lead', record: 'LS-24-0422'})")
                page.click("text=Release result")
                page.wait_for_timeout(100)
                self.assertEqual(page.evaluate("ZAS.store.get('samples', 'LS-24-0422').stage"), "Released")
                self.assertIn("Result released", page.inner_text("body"))
                # Pointing back: the runtime reports where the user is.
                self.assertEqual(page.evaluate("ZAS.state.role"), "lead")
                self.assertEqual(errors, [])
            finally:
                browser.close()

    def test_an_imported_page_runs_and_the_preview_can_drive_it(self):
        from playwright.sync_api import sync_playwright

        parts, _ = P.import_html(PAGE)
        manifest = json.loads(parts["manifest.json"])
        manifest.update(
            roles={"rep": "Field rep", "lead": "Lead"},
            screens=[{"id": "home", "title": "Home"}, {"id": "visits", "title": "Visits"}],
        )
        parts["manifest.json"] = json.dumps(manifest)
        parts["zas-bridge.js"] = BRIDGE
        html = P.assemble(parts)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = browser.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.route("**/*", lambda r: r.abort() if "jsdelivr" in r.request.url else r.continue_())
                page.set_content(html)
                page.wait_for_function("window.ZAS")
                self.assertIn("Home for rep", page.inner_text("#root"))
                page.evaluate("ZAS.go('visits', {role: 'lead'})")
                self.assertIn("Visits", page.inner_text("#root"))
                self.assertEqual(page.evaluate("ZAS.state.screen"), "visits")
                self.assertEqual(page.inner_text("#zas-app"), "")  # the runtime draws nothing over it
                self.assertEqual(errors, [])
            finally:
                browser.close()

    def test_a_broken_screen_does_not_blank_the_app(self):
        from playwright.sync_api import sync_playwright

        parts = example_parts()
        parts["screens/samples.js"] = "ZAS.screen('samples', c => { throw new Error('boom') })"
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page, _ = self._page(browser, P.assemble(parts))
                page.evaluate("ZAS.go('samples', {role: 'lead'})")
                self.assertIn("failed to draw", page.inner_text("[data-zas-screen]"))
                self.assertIn("Sample Tracker", page.inner_text("body"))  # the shell still draws
                errs = page.evaluate("ZAS.errors")
                self.assertEqual(errs[-1]["part"], "screens/samples.js")
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()


class DesignTokenTests(unittest.TestCase):
    def test_generated_tokens_map_to_canonical_names(self):
        parts = {p.name: p.read_text() for p in EXAMPLE.glob("*.css")}
        parts["manifest.json"] = (EXAMPLE / "manifest.json").read_text()
        design = P.design_tokens(parts)
        self.assertEqual(design["source"], "prototype")
        self.assertTrue(design["tokens"]["brand"].startswith("#"))
        self.assertNotIn("var(", json.dumps(design))

    def test_imported_page_reads_top_level_root_rules_in_order(self):
        css = (
            ":root{color-scheme:light}"  # the artifact wrapper's own rule
            ":root{--green-500:#458261;--brand:var(--green-500);--ink:#111;--r-sm:6px;"
            "--font:'Inter',system-ui,sans-serif;--mono:'JetBrains Mono',monospace}"
            "@media (prefers-color-scheme:dark){:root{--ink:#eee}}"
            ".card{color:var(--ink)}"
            "/* client palette */ :root{--brand:#234635}"
        )
        parts = {
            "manifest.json": json.dumps({"source": "imported", "screens": []}),
            "imported/styles.css": css,
        }
        design = P.design_tokens(parts)
        self.assertEqual(design["fonts"], {"body": "Inter", "mono": "JetBrains Mono"})
        self.assertEqual(design["tokens"]["brand"], "#234635")
        self.assertEqual(design["tokens"]["text"], "#111")
        self.assertEqual(design["tokens"]["radius-sm"], "6px")
        self.assertEqual(design["tokens"]["green-500"], "#458261")


@unittest.skipUnless(playwright_available(), "Playwright is not installed")
class PrototypeBundleTests(unittest.TestCase):
    def test_every_screen_and_role_gets_a_snapshot(self):
        import tempfile

        from zango.apps.agent_mode.approval_bundle import write_prototype_bundle

        parts = {
            str(p.relative_to(EXAMPLE)): p.read_text()
            for p in EXAMPLE.rglob("*")
            if p.is_file() and p.suffix in (".css", ".js", ".json")
        }
        manifest = json.loads(parts["manifest.json"])
        with tempfile.TemporaryDirectory() as tmp:
            capture = write_prototype_bundle(parts, tmp, design={"tokens": {"brand": "#123456"}})
            self.assertEqual(capture["probe"], "ok")
            self.assertEqual(
                [s["id"] for s in capture["screens"]], [s["id"] for s in manifest["screens"]]
            )
            out = Path(tmp)
            for name in ("prototype.html", "manifest.json", "design.json", "libraries.json", "index.md"):
                self.assertTrue((out / name).is_file(), name)
            for screen in capture["screens"]:
                folder = out / "screens" / screen["id"]
                for r in screen["roles"]:
                    self.assertFalse(r.get("error") or r.get("errors"), (screen["id"], r))
                    if r.get("files"):
                        dom = (folder / f"dom.{r['role']}.html").read_text()
                        self.assertNotIn("<script", dom)
                        self.assertNotIn("z-persona", dom)
                        self.assertTrue((folder / f"shot.{r['role']}.png").is_file())
                    else:
                        self.assertIn("same_as", r)
                css = (folder / "css.used.css").read_text()
                self.assertNotIn("display:none!important", css.replace(" ", ""))
            record = next(s for s in capture["screens"] if s.get("record"))
            self.assertTrue(any(r.get("record") for r in record["roles"]))
            index = (out / "index.md").read_text()
            self.assertIn("brand #123456", index)
            self.assertIn("`src/custom/Shell.tsx` on the runtime's `makeShell`", index)

    def test_imported_record_screens_need_a_sample(self):
        parts = {
            "manifest.json": json.dumps(
                {"source": "imported", "roles": {"a": "A"},
                 "screens": [{"id": "list"}, {"id": "item", "record": "items"}]}
            ),
            "zas-bridge.js": "ZAS.ready({go: function () {}});",
        }
        self.assertTrue(any("item" in p and "sample" in p for p in P.static_problems(parts)))


class PrototypeIndexTests(unittest.TestCase):
    def test_the_shell_is_read_on_each_roles_home(self):
        from zango.apps.agent_mode.approval_bundle import prototype_index_md

        capture = {"screens": [
            {"id": "home", "roles": [{"role": "a", "files": ["shot.a.png"]}, {"role": "b", "same_as": "a"}]},
            {"id": "desk", "roles": [{"role": "c", "files": ["shot.c.png"]}]},
        ]}
        md = prototype_index_md(capture, {"home": {"a": "home", "b": "home", "c": "desk", "d": "gone"}})
        self.assertIn("a `screens/home/shot.a.png`, b `screens/home/shot.a.png`, c `screens/desk/shot.c.png`.", md)
        self.assertNotIn("gone", md)
