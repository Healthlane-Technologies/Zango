"""My Downloads: the crud package's page of finished exports, for the roles that can export.

The spec agent puts `{page: my_downloads}` in those roles' menus (and the prototype); the build agent's
platform step adds the native crud route, the menu item and the `CrudDownloadsViewAccess` policy.
"""

import sys
import unittest

from pathlib import Path
from unittest import mock

from zango.apps.agent_mode import requirements
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir


SKILLS = Path(studio_plugin_dir()) / "skills"
SKILL = SKILLS / "zango-app-studio"
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import spec_check  # noqa: E402
import zango_platform as Z  # noqa: E402


ENT = {
    "orders": {"access": {"Sales": {"actions": ["view", "export"]}, "Viewer": {"actions": ["view"]}}},
}


class ExportRoles(unittest.TestCase):
    def test_only_roles_with_view_and_export(self):
        self.assertEqual(spec_check.export_roles(ENT, ["Sales", "Viewer"]), ["Sales"])

    def test_no_access_block_means_every_action(self):
        self.assertEqual(spec_check.export_roles({"x": {"access": {}}}, ["A", "B"]), ["A", "B"])

    def test_none_is_no_export(self):
        ents = {"x": {"access": {"A": {"actions": ["view", "export"], "none": True}}}}
        self.assertEqual(spec_check.export_roles(ents, ["A"]), [])

    def test_menu_pages_reads_groups_and_flat_items(self):
        role = {"menu": [{"page": "a"}, {"group": "G", "items": [{"page": "my_downloads"}]}]}
        self.assertEqual(spec_check.menu_pages(role), ["a", "my_downloads"])


class ReservedPage(unittest.TestCase):
    """The agent once declared a custom my_downloads page and mapped its preview screen to it: a hand-built
    screen for something the platform serves. The checker now says so, with the fix."""

    SPEC = Path(__file__).with_name("test_my_downloads.py")  # placeholder so the class has a stable anchor

    def lint(self, doc):
        import io
        import yaml
        import contextlib
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s.yaml")
            with open(path, "w") as f:
                yaml.safe_dump(doc, f)
            out = os.path.join(tmp, "out")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), mock.patch.object(sys, "argv", ["spec_check", path, "--out", out]):
                try:
                    spec_check.main()
                except SystemExit:
                    pass
            return buf.getvalue()

    def test_source_has_both_checks(self):
        src = (SCRIPTS / "spec_check.py").read_text(encoding="utf-8")
        self.assertIn("is the platform's own page", src)
        self.assertIn("use `maps: /system/@", src)

    def test_the_endpoint_is_under_the_crud_package_prefix(self):
        src = (SCRIPTS / "spec_check.py").read_text(encoding="utf-8")
        self.assertIn('MY_DOWNLOADS_ENDPOINT = "/crud/downloads/my-downloads"', src)

    def test_the_build_adds_the_item_for_exporters(self):
        src = (SCRIPTS / "spec_check.py").read_text(encoding="utf-8")
        self.assertIn('r["menu"].append({**MY_DOWNLOADS_ITEM, "auto": True})', src)
        self.assertIn('not r.get("no_downloads")', src)
        schema = (Path(__file__).resolve().parents[3] / "apps/shared/app_templates/packs/zango_app/schema.json").read_text()
        self.assertIn('"no_downloads"', schema)


class SpecAgentSide(unittest.TestCase):
    """The spec agent validates against the pack's own rules and schema, and the build skill's checker. All
    three must agree that My Downloads is a reserved menu page (the agent once declared a custom page to
    clear a rule that demanded one)."""

    PACK = Path(__file__).resolve().parents[3] / "apps" / "shared" / "app_templates" / "packs" / "zango_app"

    def test_menu_rules_know_the_reserved_page(self):
        import json

        from zango.apps.shared.app_templates.services.spec import rules as rules_mod

        rules = json.loads((self.PACK / "rules.json").read_text(encoding="utf-8"))
        rules = rules["rules"] if isinstance(rules, dict) and "rules" in rules else rules
        doc = {
            "roles": [{"name": "Sales", "menu": [{"page": "my_downloads"}, {"group": "G", "items": [{"page": "my_downloads"}]}]}],
            "pages": [{"code": "orders"}],
        }
        bad = [i for i in rules_mod.evaluate(doc, rules) if "my_downloads" in i["message"]]
        self.assertEqual(bad, [])
        # and an unknown page is still an error
        doc["roles"][0]["menu"] = [{"page": "nope"}]
        self.assertTrue([i for i in rules_mod.evaluate(doc, rules) if "nope" in i["message"]])

    def test_schema_accepts_the_system_mapping_only_for_my_downloads(self):
        import json
        import re

        schema = json.loads((self.PACK / "schema.json").read_text(encoding="utf-8"))
        text = json.dumps(schema)
        pattern = re.search(r'"pattern": "(\^/\(pages\|detail_views\)[^"]*)"', text.replace("\\\\", "\\")).group(1)
        rx = re.compile(pattern.replace("\\\\", "\\"))
        self.assertTrue(rx.match("/system/@my_downloads"))
        self.assertTrue(rx.match("/pages/@orders"))
        self.assertFalse(rx.match("/system/@anything_else"))

    def test_the_pack_doc_says_it(self):
        text = (self.PACK / "SCHEMA.md").read_text(encoding="utf-8")
        self.assertIn("/system/@my_downloads", text)
        self.assertIn("not a page of the", text)


class Routes(unittest.TestCase):
    def test_a_native_crud_route_only_when_a_role_has_the_item(self):
        M = {"pages": {}, "detail_views": {}, "my_downloads": None}
        self.assertNotIn("my_downloads", [c for c, _ in Z.page_routes(M)])
        M["my_downloads"] = {"route": "/app/my-downloads", "endpoint": "/crud/downloads/my-downloads",
                             "policy": "CrudDownloadsViewAccess", "roles": ["Sales"]}
        rt = dict(Z.page_routes(M))["my_downloads"]
        self.assertEqual((rt["page_type"], rt["path"]), ("crud", "/app/my-downloads"))
        self.assertEqual(rt["extra_params"], {"api_endpoint": "/crud/downloads/my-downloads"})
        self.assertNotIn("component", rt)  # AppBuilder's own crud renderer: no React export


class FakePlatform:
    uuid = "u"

    def __init__(self, policy, roles):
        self.policy, self._roles, self.puts = policy, roles, []

    def roles(self):
        return {n: {"id": i} for n, i in self._roles.items()}

    def get(self, path, **kw):
        return {"response": {"policies": [self.policy] if self.policy else []}}

    def put(self, path, files=None, **kw):
        self.puts.append((path, [v[1] for k, v in files if k == "roles"]))


class AttachPolicy(unittest.TestCase):
    M = {"my_downloads": {"route": "/app/my-downloads", "endpoint": "/crud/downloads/my-downloads",
                          "policy": "CrudDownloadsViewAccess", "roles": ["Sales"]}}

    def run_attach(self, P):
        with mock.patch.object(Z, "records", lambda res, key: res["response"][key]):
            Z.attach_my_downloads(P, self.M, lambda m: None)

    def test_adds_the_role_and_keeps_the_ones_already_there(self):
        P = FakePlatform({"id": 9, "name": "CrudDownloadsViewAccess", "roles": [{"id": 1}]}, {"Sales": 5})
        self.run_attach(P)
        self.assertEqual(P.puts, [("/api/v1/apps/u/policies/9/", ["1", "5"])])

    def test_idempotent(self):
        P = FakePlatform({"id": 9, "name": "CrudDownloadsViewAccess", "roles": [{"id": 5}]}, {"Sales": 5})
        self.run_attach(P)
        self.assertEqual(P.puts, [])

    def test_missing_policy_fails_loudly(self):
        with self.assertRaises(Z.PlatformError):
            self.run_attach(FakePlatform(None, {"Sales": 5}))

    def test_nothing_to_do_without_the_block(self):
        P = FakePlatform(None, {})
        Z.attach_my_downloads(P, {"my_downloads": None}, lambda m: None)
        self.assertEqual(P.puts, [])


class Guidance(unittest.TestCase):
    def test_the_spec_agent_is_told(self):
        text = Path(requirements.__file__).read_text(encoding="utf-8")
        self.assertIn("My Downloads", text)
        self.assertIn("/system/@my_downloads", text)
        self.assertIn("never ask the user which columns to show", text)  # a fixed page: no design questions

    def test_the_skills_say_it(self):
        for rel in ("zango-prototype/SKILL.md", "zango-requirements-analyst/SKILL.md", "zango-app-studio/SKILL.md",
                    "zango-app-studio/references/map/pages-menus.md", "zango-app-studio/references/map/access.md"):
            self.assertIn("My Downloads", (SKILLS / rel).read_text(encoding="utf-8"), rel)


if __name__ == "__main__":
    unittest.main()


class ExportRole(unittest.TestCase):
    """An export runs in a Celery worker, where there is no session and so no current role. The table must
    use the role the crud export task hands it, or every role-scoped query is empty (the file had a header and
    no rows)."""

    def test_the_table_takes_the_role_the_export_task_passes(self):
        src = (SCRIPTS.parent / "assets" / "backend" / "zas_core" / "mixins.py").read_text(encoding="utf-8")
        self.assertIn('role = getattr(self, "user_role", None)', src)
        self.assertIn("req._zas_role_name = role.name", src)
