"""The preview greys the menu items the YAML keeps for screens not built.

Regression (run 7): an imported mockup drew Agents, Getting started and Integrations as live menu
items, while the build shows them greyed out (``only: prototype`` with a ``menu``).
"""

import json
import re
import unittest

from zango.apps.agent_mode.prototype import assemble, soon_digest, soon_menu


SPEC = """
prototype:
  screens:
    - {id: home, maps: /pages/@home}
    - id: agents
      only: prototype
      menu: {group: AI, label: Agents, icon: bot}
    - {id: signin, only: prototype, why: "Platform sign-in."}
    - id: start
      only: prototype
      menu: {group: Help, label: Getting started, icon: flag}
"""

PARTS = {
    "manifest.json": json.dumps({"title": "T", "screens": [{"id": "home"}]}),
    "body.html": '<nav id="nav"></nav>',
}


class SoonMenuTests(unittest.TestCase):
    def test_only_prototype_screens_with_a_menu(self):
        self.assertEqual(
            soon_menu(SPEC),
            [
                {"id": "agents", "label": "Agents", "group": "AI"},
                {"id": "start", "label": "Getting started", "group": "Help"},
            ],
        )

    def test_a_draft_that_does_not_parse_greys_nothing(self):
        self.assertEqual(soon_menu("prototype: [unclosed"), [])
        self.assertEqual(soon_menu(""), [])
        self.assertEqual(soon_digest([]), "")

    def test_the_page_carries_them_and_the_digest_follows_them(self):
        soon = soon_menu(SPEC)
        html = assemble(PARTS, soon)
        found = re.search(r'<script type="application/json" id="zas-soon">(.*?)</script>', html)
        self.assertEqual(json.loads(found.group(1)), soon)
        self.assertIn('id="zas-soon">[]<', assemble(PARTS))
        self.assertNotEqual(soon_digest(soon), soon_digest(soon[:1]))
