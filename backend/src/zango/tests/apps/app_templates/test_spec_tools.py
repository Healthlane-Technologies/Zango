import asyncio

from unittest import mock

from django.db import connection

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack

from .tests import AppTemplatesTestBase


def _handlers(bench):
    from zango.apps.agent_mode.spec_tools import make_handler, tool_specs

    return {name: make_handler(bench, fn) for name, _, _, fn in tool_specs(bench)}


def _call(handler, args):
    return asyncio.run(handler(args))


class _NoQueries:
    """Fail the test if anything inside touches the database."""

    def __enter__(self):
        def blocker(*args, **kwargs):
            raise AssertionError("a spec tool handler queried the database")

        self._cm = connection.execute_wrapper(blocker)
        self._cm.__enter__()
        return self

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


class SpecToolTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "psp", publish_now=True)
        catalogue.clear_caches()
        self.template = catalogue.get_template("psp")
        self.emitted = []

    def bench(self, text=None):
        from zango.apps.agent_mode.spec_tools import SpecWorkbench

        text = self.template.starter_yaml if text is None else text
        return SpecWorkbench(text, self.template, emit=self.emitted.append)

    def test_a_valid_edit_is_applied_and_emitted_with_its_path(self):
        bench = self.bench()
        comments = bench.text.count("#")
        result = bench.set("/name", "Oncology PAP")
        self.assertIn("/name", result)
        self.assertEqual(len(self.emitted), 1)
        self.assertEqual(self.emitted[0]["changed_paths"], ["/name"])
        self.assertIn("name: Oncology PAP", self.emitted[0]["yaml"])
        self.assertEqual(
            bench.text.count("#"), comments, "guidance comments must survive edits"
        )

    def test_a_change_that_breaks_the_structure_is_refused(self):
        from zango.apps.agent_mode.spec_tools import ToolRefused

        bench = self.bench()
        before = bench.text
        with self.assertRaises(ToolRefused) as ctx:
            bench.set("/roles", ["Manager"])
        self.assertIn("/roles", str(ctx.exception))
        self.assertEqual(bench.text, before)
        self.assertEqual(self.emitted, [])

    def test_selectors_reach_items_by_code(self):
        bench = self.bench((PACKS_DIR / "psp" / "example.yaml").read_text())
        bench.set("/masters/@city/plural", "Towns")
        self.assertEqual(self.emitted[-1]["changed_paths"], ["/masters/0/plural"])
        self.assertIn("Towns", bench.get("/masters/@city"))

    def test_replace_section_and_mark_ready(self):
        from zango.apps.agent_mode.spec_tools import ToolRefused

        bench = self.bench("journey: x\n")
        with self.assertRaises(ToolRefused):
            bench.mark_ready("done")  # strict: required sections missing
        bench.replace_section("", (PACKS_DIR / "psp" / "example.yaml").read_text())
        self.assertIn("Marked ready", bench.mark_ready("Enhertu PAP"))
        self.assertEqual(bench.ready_summary, "Enhertu PAP")

    def test_outline_lists_every_section(self):
        outline = self.bench().outline()
        for section in self.template.ui_schema["sections"]:
            self.assertIn(section["id"], outline)

    def test_handlers_never_touch_the_database(self):
        bench = self.bench()
        handlers = _handlers(bench)
        with _NoQueries():
            ok = _call(handlers["spec_set"], {"path": "/name", "value": "X"})
            bad = _call(handlers["spec_set"], {"path": "/roles", "value": [1]})
            _call(handlers["spec_outline"], {})
            _call(handlers["spec_validate"], {})
            missing = _call(handlers["spec_remove"], {"path": "/masters/@nowhere"})
        self.assertNotIn("is_error", ok)
        self.assertTrue(bad["is_error"])
        self.assertTrue(missing["is_error"])

    def test_the_sdk_server_builds(self):
        from zango.apps.agent_mode.spec_tools import build_spec_server

        server = build_spec_server(self.bench())
        self.assertEqual(server["name"], "spec")

    def test_analyst_options_expose_the_tools(self):
        from zango.apps.agent_mode.requirements import build_analyst_options
        from zango.apps.agent_mode.spec_tools import (
            ALLOWED_TOOL_NAMES,
            build_spec_server,
        )

        class Ctx:
            workspace_path = "/tmp"

        class Req:
            session_id = ""

        with mock.patch("zango.apps.agent_mode.options.build_env", return_value={}):
            opts = build_analyst_options(
                ctx=Ctx(),
                creds=object(),
                requirement=Req(),
                spec_server=build_spec_server(self.bench()),
            )
        self.assertIn("spec", opts.mcp_servers)
        for name in ALLOWED_TOOL_NAMES:
            self.assertIn(name, opts.allowed_tools)
        self.assertNotIn("Write", opts.allowed_tools)
        self.assertGreaterEqual(opts.max_turns, 80)
        self.assertIn("mcp__spec__", opts.system_prompt["append"])


class ManualEditTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "psp", publish_now=True)
        catalogue.clear_caches()

    def requirement(self):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.template_binding import seed_template_requirement

        requirement = AgentRequirement(initial_prompt="go")
        seed_template_requirement(requirement, catalogue.get_template("psp"))
        requirement.save = lambda *a, **k: None  # no tenant schema in this test
        return requirement

    def test_put_saves_a_draft_and_records_what_changed(self):
        from zango.apps.agent_mode.template_spec import save_manual

        r = self.requirement()
        text = r.spec_markdown.replace("journey: my_psp", "journey: onc_pap", 1)
        self.assertNotEqual(text, r.spec_markdown)
        code, payload = save_manual(r, text, r.draft_revision)
        self.assertEqual(code, 200, payload)
        self.assertEqual(payload["draft_revision"], 2)
        self.assertTrue(payload["is_draft"])
        self.assertEqual(payload["changed_paths"], ["/journey"])

    def test_stale_or_busy_saves_conflict(self):
        from zango.apps.agent_mode.template_spec import save_manual

        r = self.requirement()
        code, payload = save_manual(r, r.spec_markdown, r.draft_revision - 1)
        self.assertEqual(code, 409)
        self.assertEqual(payload["current"]["draft_revision"], r.draft_revision)
        r.is_thinking = True
        self.assertEqual(save_manual(r, r.spec_markdown, r.draft_revision)[0], 409)

    def test_structural_errors_are_refused_but_gaps_are_not(self):
        from zango.apps.agent_mode.template_spec import save_manual

        r = self.requirement()
        code, payload = save_manual(r, "journey: x\nroles: [a, b]\n", r.draft_revision)
        self.assertEqual(code, 400)
        self.assertTrue(payload["issues"])
        code, _ = save_manual(r, "journey: x\n", r.draft_revision)
        self.assertEqual(code, 200)

    def test_patch_keeps_comments(self):
        from zango.apps.agent_mode.template_spec import patch_manual

        r = self.requirement()
        comments = r.spec_markdown.count("#")
        code, payload = patch_manual(
            r, [{"op": "set", "path": "/name", "value": "Onc PAP"}], r.draft_revision
        )
        self.assertEqual(code, 200, payload)
        self.assertIn("name: Onc PAP", r.spec_markdown)
        self.assertEqual(r.spec_markdown.count("#"), comments)
        self.assertEqual(payload["changed_paths"], ["/name"])

    def test_finalize_needs_a_complete_spec(self):
        from zango.apps.agent_mode.template_spec import finalize, save_manual

        r = self.requirement()
        code, _ = save_manual(r, "journey: x\n", r.draft_revision)
        self.assertEqual(finalize(r, r.draft_revision)[0], 400)
        example = (PACKS_DIR / "psp" / "example.yaml").read_text()
        with mock.patch(
            "zango.apps.agent_mode.models.AgentRequirementVersion.objects.create"
        ):
            save_manual(r, example, r.draft_revision)
            code, payload = finalize(r, r.draft_revision)
        self.assertEqual(code, 200, payload)
        self.assertFalse(payload["is_draft"])
        self.assertEqual(payload["status"], "ready")


class OpenModeSpecTests(AppTemplatesTestBase):
    """Free design: app.design follows the prototype, custom pages carry a reason."""

    def setUp(self):
        super().setUp()
        import_pack(PACKS_DIR / "zango_app", publish_now=True)
        catalogue.clear_caches()
        self.template = catalogue.get_template("zango-app")

    def bench(self):
        from zango.apps.agent_mode.prototype import PrototypeBench
        from zango.apps.agent_mode.spec_tools import SpecWorkbench

        from .test_prototype import EXAMPLE

        parts = {
            str(p.relative_to(EXAMPLE)): p.read_text()
            for p in EXAMPLE.rglob("*")
            if p.is_file() and p.suffix in (".css", ".js", ".json")
        }
        return SpecWorkbench(
            (PACKS_DIR / "zango_app" / "example.yaml").read_text(),
            self.template,
            emit=lambda e: None,
            proto=PrototypeBench(parts, lambda e: None),
        )

    def test_proto_design_sets_app_design_and_ready_checks_it(self):
        from zango.apps.agent_mode.spec_tools import ToolRefused

        bench = self.bench()
        with self.assertRaisesRegex(ToolRefused, "no app.design"):
            bench._check_open_mode_ready()
        out = _call(_handlers(bench)["proto_design"], {})
        self.assertIn("/app/design", str(out))
        design = bench._plain(bench.doc)["app"]["design"]
        self.assertEqual(design["source"], "prototype")
        self.assertTrue(design["tokens"].get("brand", "").startswith("#"))
        self.assertIn("body", design.get("fonts", {}))
        bench.set("/app/design/tokens/brand", "#000000")
        with self.assertRaisesRegex(ToolRefused, "no longer matches"):
            bench._check_open_mode_ready()

    def test_custom_page_needs_a_reason_in_open_mode(self):
        from zango.apps.agent_mode.spec_tools import ToolRefused

        bench = self.bench()
        bench.apply_design()
        pages = bench._plain(bench.doc).get("pages") or []
        bench.add("/pages", {"code": "visit_map", "type": "custom", "title": "Visit map",
                             "acceptance": ["Shows visits on a map."]})
        with self.assertRaisesRegex(ToolRefused, "/pages/@visit_map"):
            bench._check_open_mode_ready()
        bench.set("/pages/@visit_map/reason", "A map; no declared page draws one.")
        for p in pages:
            if p.get("type") == "custom":
                bench.set(f"/pages/@{p['code']}/reason", "Example reason.")
        note = bench._check_open_mode_ready()
        self.assertIn("visit_map: A map", note)
        self.assertTrue(pages)
        # reason is only for custom pages
        crud = next(p["code"] for p in pages if p.get("type") == "crud")
        with self.assertRaises(ToolRefused):
            bench.set(f"/pages/@{crud}/reason", "no")
