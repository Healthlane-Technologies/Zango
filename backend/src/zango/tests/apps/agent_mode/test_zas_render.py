"""zas-render.js: one renderer, one source, two copies (the kit page inline, the runtime's zas/).

The preview and the built app draw from the same file, so a copy that drifts from the source is a
design drift; CI fails on it. The node checks render a list page through a host with the module
alone, the contract the runtime relies on.
"""

import json
import re
import shutil
import subprocess
import unittest

from zango.apps.agent_mode import zas_render


class CopiesTests(unittest.TestCase):
    def test_copies_match_the_source(self):
        self.assertEqual(zas_render.stale(), [], "run python -m zango.apps.agent_mode.zas_render --write")

    def test_inline_round_trip(self):
        html = "<head></head><script data-zas-render>\nold</script><script>main()</script>"
        out = zas_render.inline(html, "new\n")
        self.assertEqual(zas_render.inlined(out), "new\n")
        self.assertTrue(out.endswith("</script><script>main()</script>"))

    def test_kit_does_not_redeclare_what_it_imports(self):
        page = zas_render.KIT_PAGE.read_text(encoding="utf-8")
        main = page.split("<script>\n'use strict';\n", 1)[1]
        imported = re.match(r"const \{ ([^}]+) \} = ZasRender;", main)
        self.assertIsNotNone(imported, "the kit's main script starts by importing the renderer")
        names = {n.strip() for n in imported.group(1).split(",")}
        own = set(re.findall(r"^(?:const|let|var|function)\s+([A-Za-z_$][\w$]*)", main, re.M))
        self.assertEqual(sorted(names & own), [])


SPEC = {
    "app": {"name": "Vendors", "locale": "en-US", "currency": "USD"},
    "roles": [{"name": "Admin", "menu": [{"page": "vendors"}]}],
    "modules": [{"code": "core", "entities": [{
        "code": "vendor", "name": "Vendor",
        "fields": [{"name": {"type": "text"}}, {"tier": {"type": "choice", "choices": ["gold", "silver"]}}],
        "table": {"columns": [{"name": {"searchable": True, "sortable": True}}, {"tier": {"filterable": True}}],
                  "quick_filters": [{"label": "Gold", "where": "tier == 'gold'", "count": True}]},
    }]}],
    "pages": [{"code": "vendors", "type": "crud", "entity": "vendor", "route": "/vendors"}],
}

SCRIPT = r"""
require(process.argv[1]);
const R = globalThis.ZasRender;
const spec = JSON.parse(process.argv[2]);
const S = { M: R.build(spec), role: 'Admin', users: { Admin: ['Ada'] }, me: {}, ui: { tables: {} }, views: {} };
S.db = { vendor: [
  { id: 1, name: 'Acme', tier: 'gold', status: null, tags: [], created_at: '2026-01-02T00:00:00Z' },
  { id: 2, name: 'Bolt', tier: 'silver', status: null, tags: [], created_at: '2026-01-03T00:00:00Z' },
] };
const acts = [];
R.use({ state: S, ...R.memory(), preview: false, act: (n, p) => acts.push(n) });
const p = S.M.pages.vendors, E = S.M.ents.vendor;
const html = R.renderCrud(E, p);
S.ui.tables.crud_vendor.q = 'bol';
const searched = R.renderCrud(E, p);
console.log(JSON.stringify({ html, searched }));
"""


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class NodeRenderTests(unittest.TestCase):
    def render(self):
        out = subprocess.run(["node", "-e", SCRIPT, str(zas_render.SOURCE), json.dumps(SPEC)],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_list_page_renders_through_a_host(self):
        r = self.render()
        self.assertIn("<h1>Vendors <span class=\"z-hc\" data-zas-chrome>(2)</span></h1>", r["html"])
        self.assertIn("Acme", r["html"])
        self.assertIn("<span class=\"z-qf-n\">1</span>", r["html"])  # the Gold chip's count
        self.assertNotIn("data-zas-path", r["html"])  # preview marks only when host.preview

    def test_search_goes_through_the_host_query(self):
        r = self.render()
        self.assertIn("Bolt", r["searched"])
        self.assertNotIn("Acme", r["searched"])
