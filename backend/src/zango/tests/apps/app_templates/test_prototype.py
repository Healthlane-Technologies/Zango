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
