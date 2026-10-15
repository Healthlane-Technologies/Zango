"""The sketch kit (spec-to-build F1): the preview's ctx.ui blocks exist in the build's design system.

A custom screen's `preview` sketch calls ctx.ui (kpis, bars, list, table, board, progress, panel,
stack, grid). The runtime has the same blocks in zas/ui.tsx with the same arguments, styled rule for
rule like the preview, and both draw the same data-zas-kit markers, read by one extractor
(scripts/zas_test/kit_tree.js) for the build's parity check.
"""

import re
import unittest

from pathlib import Path

from zango.apps.agent_mode.preview_probe import playwright_available
from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir


PACK = PACKS_DIR / "zango_app"
SKILL = Path(studio_plugin_dir()) / "skills" / "zango-app-studio"
ZAS = SKILL / "assets" / "frontend" / "zas"
KIT_TREE = SKILL / "scripts" / "zas_test" / "kit_tree.js"

# preview rule -> its runtime twin (tokens.css)
PAIRS = [
    (".ui-stack", ".zas-kstack"), (".ui-grid", ".zas-kgrid"), (".ui-body", ".zas-kbody"),
    (".ui-bar", ".zas-kbar"), (".ui-bar b", ".zas-kbar b"), (".ui-li", ".zas-kli"),
    (".ui-li .ui-main", ".zas-kli .zas-kmain"), (".ui-li .ui-sub", ".zas-kli .zas-ksub"),
    (".ui-li .ui-meta", ".zas-kli .zas-kmeta"), (".ui-empty", ".zas-kempty"), (".ui-prog", ".zas-kprog"),
    (".ui-board", ".zas-kboard"), (".ui-board .pv-col", ".zas-kcol"), (".pv-col", ".zas-kcol"),
    (".pv-col > h4", ".zas-kcol > h4"), (".pv-card", ".zas-kcard"), (".pv-muted", ".zas-kmuted"),
    (".pv-bar", ".zas-ktrack"), (".d-stat", ".zas-stat"), (".d-panel", ".zas-panel"), (".d-panel > h3", ".zas-panel > h3"),
]
# The preview pins these to 12px; the runtime follows app.ui (radius), whose default is 12px.
RADIUS_TOKEN = {"var(--z-r-card)": "12px"}


def _split_selectors(sel: str) -> list:
    out, depth, cur = [], 0, ""
    for ch in sel:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    return out + [cur]


def css_rules(css: str) -> dict:
    out = {}
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        for one in _split_selectors(sel):
            key = " ".join(one.replace(">", " > ").split())
            decls = out.setdefault(key, {})
            for decl in body.split(";"):
                if ":" in decl:
                    k, v = decl.split(":", 1)
                    decls[k.strip()] = " ".join(v.strip().split())
    return out


class KitStyleTests(unittest.TestCase):
    """Each preview kit rule has a runtime twin with the same values (tokens resolved)."""

    def setUp(self):
        self.preview = css_rules((PACK / "builder" / "app-studio.html").read_text())
        runtime = css_rules((ZAS / "tokens.css").read_text())
        self.runtime = runtime
        self.root = runtime[":root"]

    def norm(self, value: str) -> str:
        for token, px in RADIUS_TOKEN.items():
            value = value.replace(token, px)
        for _ in range(3):
            value = re.sub(r"var\((--[\w-]+)(?:,\s*([^)]*))?\)",
                           lambda m: self.root.get(m.group(1), m.group(2) or m.group(0)), value)
        value = value.lower().replace(" ", "")
        value = re.sub(r"#([0-9a-f])([0-9a-f])([0-9a-f])\b", r"#\1\1\2\2\3\3", value)
        return re.sub(r"(?<![\d.])\.(\d)", r"0.\1", value)

    def test_every_preview_kit_rule_has_the_same_values_in_the_runtime(self):
        diffs = []
        for prev, rt in PAIRS:
            self.assertIn(prev, self.preview, prev)
            self.assertIn(rt, self.runtime, rt)
            for prop, value in self.preview[prev].items():
                if prev == ".pv-col" and prop == "flex":
                    continue  # the board overrides it (.ui-board .pv-col)
                got = self.runtime[rt].get(prop)
                if got is None or self.norm(got) != self.norm(value):
                    diffs.append(f"{prev} -> {rt}: {prop}: preview {value!r}, runtime {got!r}")
        self.assertEqual(diffs, [])

    def test_the_runtime_kit_carries_no_colours_of_its_own(self):
        kit = (ZAS / "tokens.css").read_text().split("/* sketch kit")[1].split("@media")[0]
        self.assertNotRegex(kit, r"#[0-9a-fA-F]{3,6}\b")


class KitComponentTests(unittest.TestCase):
    """zas/ui.tsx has a component for every ctx.ui call, marked for the parity check."""

    UI = (ZAS / "ui.tsx").read_text()

    def test_every_ctx_ui_call_has_a_component(self):
        for name in ("Stack", "Grid", "Kpis", "Bars", "List", "MiniTable", "Board", "Progress", "KitEmpty", "KitBadge"):
            self.assertRegex(self.UI, rf"export function {name}\b", name)
        self.assertIn("kit?: string", self.UI)  # Panel kit="panel"

    def test_blocks_draw_the_markers_the_preview_draws(self):
        for kit in ("kpis", "bars", "list", "table", "board", "progress", "stack", "grid"):
            self.assertIn(f'"{kit}"', self.UI, kit)
        self.assertIn("data-zas-item={k.label}", self.UI)
        self.assertIn("data-zas-item={c.label}", self.UI)

    def test_the_gallery_shows_the_kit(self):
        gallery = (ZAS / "Gallery.tsx").read_text()
        self.assertIn('data-gallery="kit"', gallery)
        design = (SKILL / "scripts" / "zas_test" / "design.py").read_text()
        self.assertRegex(design, r'SECTIONS = \[[^\]]*"kit"')


@unittest.skipUnless(playwright_available(), "Playwright is not installed")
class PreviewKitTreeTests(unittest.TestCase):
    """The extractor reads the preview's kit blocks: what the approval bundle records."""

    def tree(self, spec_text: str) -> dict:
        from playwright.sync_api import sync_playwright

        html = (PACK / "builder" / "app-studio.html").read_text()
        html = html.replace("</body>", "<script>" + (PACK / "builder" / "adapter.js").read_text() + "</script></body>")
        extractor = KIT_TREE.read_text()
        out = {}
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page()
                page.route("**/*", lambda r: r.abort())
                page.set_content(html)
                page.evaluate("y => window.zangoLoad(y)", spec_text)
                for sk in page.evaluate("() => ZAS_PROBE.sketches()"):
                    page.evaluate("p => ZAS_PROBE.show(p)", sk["path"])
                    out[sk["path"]] = page.evaluate(
                        f"p => ({extractor})(document.querySelector('[data-zas-sketch=\"' + p + '\"]'))", sk["path"])
                browser.close()
        except Exception as exc:  # noqa: BLE001 - Chromium itself not installed
            if re.search(r"Executable doesn't exist|playwright install", str(exc)):
                self.skipTest(str(exc))
            raise
        return out

    def test_the_example_dashboard_reads_as_its_blocks(self):
        trees = self.tree((PACK / "example.yaml").read_text())
        self.assertEqual(trees["/pages/@dashboard"], [
            {"kit": "kpis", "items": ["Vendors pending approval", "Open POs", "PO value this month", "Invoices overdue"]},
            {"kit": "bars", "title": "PO value by month"},
            {"kit": "list", "title": "Oldest POs awaiting approval"},
        ])
        # hand-written markup has no kit blocks: the build matches it from the screenshot
        self.assertEqual(trees["/detail_views/@vendor_360/sidebar/2"], [])


# ───────────────────────── the React kit against the preview, rendered ─────────────────────────

REPO = Path(__file__).resolve().parents[6]
CONSOLE_MODULES = REPO / "console" / "node_modules"

# One screen, written twice: as a preview sketch and as the slot a build would port it to.
SKETCH = """
const { ui } = ctx;
const rows = [{ po: 'PO-1', vendor: 'Apex', amount: '$480', status: 'Pending', tone: 'amber' },
              { po: 'PO-2', vendor: 'Globex', amount: '$90', status: 'Approved', tone: 'green' }];
return ui.stack(
  ui.kpis([{ label: 'Open POs', value: 8, icon: 'shopping-cart', tone: 'blue' }, { label: 'Overdue', value: 3, tone: 'red', hint: 'over 30 days' }]),
  ui.grid(
    ui.bars('Open by status', [{ label: 'Pending', value: 5, tone: 'amber' }, { label: 'Approved', value: 9 }]),
    ui.list('Due soonest', rows, { primary: r => r.vendor, secondary: r => r.po, meta: r => r.amount, badge: r => ({ text: r.status, tone: r.tone }) }),
  ),
  ui.table('Latest POs', rows, [{ label: 'PO', value: r => r.po }, { label: 'Vendor', value: r => r.vendor }, { label: 'Amount', value: r => r.amount, align: 'right' }]),
  ui.board('By owner', [{ title: 'Meera', items: [{ title: 'Apex', subtitle: 'Waiting 2 days' }] }, { title: 'Unassigned', tone: 'gray', items: [] }]),
  ui.panel('Onboarding', ui.progress(2, 5), { note: '2 of 5' }),
);
"""
SLOT = """
import React from "react";
import { createRoot } from "react-dom/client";
import { Board, Bars, Grid, Kpis, List, MiniTable, Panel, Progress, Stack } from "./zas/ui";
const rows = [{ po: "PO-1", vendor: "Apex", amount: "$480", status: "Pending", tone: "amber" },
              { po: "PO-2", vendor: "Globex", amount: "$90", status: "Approved", tone: "green" }];
function Screen() {
  return (
    <Stack>
      <Kpis items={[{ label: "Open POs", value: 8, icon: "shopping-cart", tone: "blue" }, { label: "Overdue", value: 3, tone: "red", hint: "over 30 days" }]} />
      <Grid>
        <Bars title="Open by status" items={[{ label: "Pending", value: 5, tone: "amber" }, { label: "Approved", value: 9 }]} />
        <List title="Due soonest" rows={rows} primary={(r) => r.vendor} secondary={(r) => r.po} meta={(r) => r.amount} badge={(r) => ({ text: r.status, tone: r.tone })} />
      </Grid>
      <MiniTable title="Latest POs" rows={rows} columns={[{ label: "PO", value: (r) => r.po }, { label: "Vendor", value: (r) => r.vendor }, { label: "Amount", value: (r) => r.amount, align: "right" }]} />
      <Board title="By owner" columns={[{ title: "Meera", items: [{ title: "Apex", subtitle: "Waiting 2 days" }] }, { title: "Unassigned", tone: "gray", items: [] }]} />
      <Panel kit="panel" title="Onboarding" note="2 of 5"><Progress done={2} total={5} /></Panel>
    </Stack>
  );
}
createRoot(document.getElementById("root")!).render(<div className="zas" id="screen"><Screen /></div>);
"""
# element pairs (preview selector, runtime selector) and the computed properties that must match
STYLE_PAIRS = [
    (".d-stat", ".zas-stat", ["padding-top", "padding-left", "border-top-left-radius", "gap", "border-top-color"]),
    (".d-stat b", ".zas-stat b", ["font-size", "font-weight", "color", "letter-spacing"]),
    (".d-stat span", ".zas-stat span", ["font-size", "color"]),
    (".d-panel > h3", ".zas-panel > h3", ["padding-top", "padding-left", "font-size", "font-weight", "color", "border-bottom-color"]),
    (".ui-bar", ".zas-kbar", ["padding-top", "font-size", "color", "column-gap"]),
    (".ui-bar .pv-bar", ".zas-kbar .zas-ktrack", ["height", "border-top-left-radius", "background-color"]),
    (".ui-li", ".zas-kli", ["padding-top", "padding-left", "font-size", "color"]),
    (".ui-li .ui-sub", ".zas-kli .zas-ksub", ["font-size", "color"]),
    (".pv-col", ".zas-kcol", ["padding-top", "background-color", "border-top-left-radius", "row-gap"]),
    (".pv-card", ".zas-kcard", ["padding-top", "padding-left", "font-size", "border-top-left-radius", "background-color"]),
    (".ui-board", ".zas-kboard", ["padding-top", "padding-left", "column-gap"]),
]


@unittest.skipUnless(playwright_available() and (CONSOLE_MODULES / ".bin" / "esbuild").exists() and (CONSOLE_MODULES / "react-dom").exists(),
                     "needs Playwright and the console's node_modules (esbuild, react)")
class RuntimeKitParityTests(unittest.TestCase):
    """The real zas/ui.tsx kit, bundled and rendered, against the preview drawing the same screen."""

    @classmethod
    def setUpClass(cls):
        import shutil
        import subprocess
        import tempfile

        root = Path(tempfile.mkdtemp())
        src = root / "src"
        shutil.copytree(ZAS, src / "zas")
        (src / "custom").mkdir()
        (src / "custom" / "spec.ui.json").write_text('{"app":{"code":"t","name":"T"},"pages":{},"entities":{},"detail_views":{},"slots":{},"menus":{}}')
        (src / "zas" / "icons.gen.ts").write_text("export const ICONS: Record<string, any> = {};\n")
        names = set()
        for f in (src / "zas").glob("*.tsx"):
            for m in re.finditer(r'import\s*\{([^}]*)\}\s*from\s*"lucide-react"', f.read_text()):
                names |= {n.strip().split(" as ")[0] for n in m.group(1).split(",") if n.strip()}
        stubs = root / "stubs"
        stubs.mkdir()
        (stubs / "lucide.js").write_text("const I = () => null;\n" + "".join(f"export const {n} = I;\n" for n in sorted(names)))
        (stubs / "crud.js").write_text("export function useTableContext() { throw new Error('no table'); }\n")
        (src / "entry.tsx").write_text(SLOT)
        out = root / "kit.js"
        proc = subprocess.run(
            [str(CONSOLE_MODULES / ".bin" / "esbuild"), str(src / "entry.tsx"), "--bundle", "--format=iife",
             f"--outfile={out}", "--loader:.json=json", "--jsx=automatic", "--define:process.env.NODE_ENV=\"production\"",
             f"--alias:lucide-react={stubs / 'lucide.js'}", f"--alias:@zango-core/crud/table={stubs / 'crud.js'}",
             "--log-level=error"],
            capture_output=True, text=True, env={"NODE_PATH": str(CONSOLE_MODULES), "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
            cwd=str(REPO / "console"),
        )
        if proc.returncode != 0:
            raise AssertionError("esbuild failed:\n" + proc.stderr[-3000:])
        cls.runtime_html = (
            "<!doctype html><html><head><style>" + (ZAS / "tokens.css").read_text() + "</style></head>"
            "<body style='margin:0;width:1200px'><div id='root'></div><script>" + out.read_text() + "</script></body></html>"
        )

    def render(self):
        import yaml
        from playwright.sync_api import sync_playwright

        doc = yaml.safe_load((PACK / "example.yaml").read_text())
        page_def = next(p for p in doc["pages"] if p["code"] == "dashboard")
        page_def["preview"] = SKETCH
        preview_html = (PACK / "builder" / "app-studio.html").read_text().replace(
            "</body>", "<script>" + (PACK / "builder" / "adapter.js").read_text() + "</script></body>")
        extractor = KIT_TREE.read_text()
        styles = "([pairs, i]) => pairs.map(([sel, props]) => { const el = document.querySelector(sel); if (!el) return null;" \
                 " const cs = getComputedStyle(el); return Object.fromEntries(props.map(p => [p, cs.getPropertyValue(p)])); })"
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.route("**/*", lambda r: r.abort())
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_content(self.runtime_html)
            page.wait_for_selector("#screen [data-zas-kit]")
            rt_tree = page.evaluate(f"() => ({extractor})(document.getElementById('screen'))")
            rt_styles = page.evaluate(styles, [[[b, props] for _, b, props in STYLE_PAIRS], 0])
            page.set_content(preview_html)
            page.evaluate("y => window.zangoLoad(y)", yaml.safe_dump(doc, sort_keys=False))
            page.evaluate("p => ZAS_PROBE.show(p)", "/pages/@dashboard")
            pv_tree = page.evaluate(f"() => ({extractor})(document.querySelector('[data-zas-sketch]'))")
            pv_styles = page.evaluate(styles, [[[a, props] for a, _, props in STYLE_PAIRS], 0])
            browser.close()
        return errors, rt_tree, pv_tree, rt_styles, pv_styles

    def test_the_ported_screen_has_the_sketchs_tree_and_looks_the_same(self):
        errors, rt_tree, pv_tree, rt_styles, pv_styles = self.render()
        self.assertEqual(errors, [])
        self.assertEqual(rt_tree, pv_tree)
        self.assertEqual([n["kit"] for n in rt_tree], ["kpis", "bars", "list", "table", "board", "panel"])
        diffs = []
        for (prev, rt, _), a, b in zip(STYLE_PAIRS, pv_styles, rt_styles):
            self.assertIsNotNone(a, prev)
            self.assertIsNotNone(b, rt)
            diffs += [f"{prev} vs {rt}: {k}: preview {a[k]!r} runtime {b[k]!r}" for k in a if a[k] != b[k]]
        self.assertEqual(diffs, [])
