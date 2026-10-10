import json

from pathlib import Path

from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.generic import (
    GENERIC_DIALECT,
    GENERIC_SLUG,
)
from zango.apps.shared.app_templates.services.packs import import_pack, lint

from .tests import AppTemplatesTestBase, write_pack


ADAPTER = "window.parent.postMessage({source:'zango-builder',type:'ready'},'*');"


class GenericFallbackTests(AppTemplatesTestBase):
    """A zango-app/1 template borrows what it leaves out from the generic one."""

    def edit_manifest(self, root: Path, **changes):
        manifest = json.loads((root / "template.json").read_text())
        manifest.update(changes)
        for key in [k for k, v in changes.items() if v is None]:
            manifest.pop(key)
        (root / "template.json").write_text(json.dumps(manifest))
        return root

    def generic(self):
        root = write_pack(
            Path(self.tmp.name) / "generic",
            slug=GENERIC_SLUG,
            version="9.0.0",
            skill_name="",
        )
        (root / "DRAFTING.md").write_text("# Draft the app\n")
        (root / "builder").mkdir()
        (root / "builder" / "studio.html").write_text("<html><body>studio</body></html>")
        (root / "builder" / "adapter.js").write_text(ADAPTER)
        for f in (root / "skill").rglob("*"):
            if f.is_file():
                f.unlink()
        self.edit_manifest(
            root,
            spec_dialect=GENERIC_DIALECT,
            drafting="DRAFTING.md",
            builder={"adapter": "builder/adapter.js", "html": "builder/studio.html"},
            build_skill_name=None,
            skill_dir=None,
        )
        version, _ = import_pack(root, publish_now=True)
        return version

    def lean(self, dialect=GENERIC_DIALECT):
        """A template that ships only its catalogue entry and a starter spec."""
        root = self.pack("lean", slug="crm-lite")
        for name in ("INTERVIEW.md", "SCHEMA.md", "schema.json", "ui.json", "rules.json"):
            (root / name).unlink()
        self.edit_manifest(
            root,
            spec_dialect=dialect,
            interview=None,
            schema=None,
            json_schema=None,
            ui_schema=None,
            rules=None,
        )
        return root

    def test_a_lean_template_borrows_docs_schema_and_preview(self):
        generic = self.generic()
        version, _ = import_pack(self.lean(), publish_now=True)
        self.assertEqual(
            [i for i in lint(version) if i["level"] == "error"], []
        )

        catalogue.clear_caches()
        view = catalogue.get_template("crm-lite")
        self.assertEqual(view.spec_dialect, GENERIC_DIALECT)
        self.assertEqual(view.borrowed_from, f"{GENERIC_SLUG}@9.0.0")
        self.assertEqual(view.json_schema, generic.json_schema)
        self.assertEqual(view.sections, (("roles", "Roles"),))
        self.assertTrue(view.file_path("interview").endswith("INTERVIEW.md"))
        self.assertIn(f"/{GENERIC_SLUG}/", view.file_path("drafting"))
        self.assertTrue(Path(view.file_path("schema")).is_file())
        # Its own starter is still its own.
        self.assertEqual(view.starter_yaml, "journey: demo\n")

        from zango.apps.shared.app_templates.services.spec.validate import (
            validate_text,
        )

        _, issues = validate_text("roles: oops\n", view)
        self.assertTrue(any(i["level"] == "error" for i in issues))

        from rest_framework.test import APIRequestFactory, force_authenticate

        from zango.api.platform.app_templates.v1.views import TemplateBuilderView

        from .test_catalogue_api import _user

        request = APIRequestFactory().get("/x/", HTTP_HOST="test.testserver.com")
        force_authenticate(request, user=_user())
        response = TemplateBuilderView.as_view()(
            request, slug="crm-lite", version_uuid=view.version_uuid
        )
        data = json.loads(response.content)["response"]
        self.assertEqual(data["preview_source"], "generic")
        self.assertIn(str(generic.object_uuid), data["preview_url"])
        self.assertIsNone(data["builder_url"])
        self.assertEqual(data["json_schema"], generic.json_schema)

    def test_own_pieces_win_and_other_dialects_never_borrow(self):
        self.generic()
        own = self.edit_manifest(self.pack("own", slug="own-app"), spec_dialect=GENERIC_DIALECT)
        version, _ = import_pack(own, publish_now=True)
        view = catalogue.get_template("own-app")
        # Everything but the drafting guide is its own.
        self.assertTrue(view.file_path("interview").startswith(view.path))
        self.assertTrue(view.file_path("schema").startswith(view.path))
        self.assertIn(f"/{GENERIC_SLUG}/", view.file_path("drafting"))

        version, _ = import_pack(self.lean(dialect=""), publish_now=False)
        problems = {i["file"] for i in lint(version) if i["level"] == "error"}
        self.assertIn("schema.json", problems)
        self.assertIn("INTERVIEW.md", problems)

    def test_without_a_generic_template_lint_says_so(self):
        from zango.apps.shared.app_templates.models import AppTemplate

        AppTemplate.objects.filter(slug=GENERIC_SLUG).delete()
        version, _ = import_pack(self.lean(), publish_now=False)
        issues = lint(version)
        self.assertTrue(any(GENERIC_SLUG in i["message"] for i in issues))
        self.assertTrue(any(i["file"] == "schema.json" for i in issues))


class AdoptMidConversationTests(AppTemplatesTestBase):
    """A plain requirement whose user accepts the generic template in chat."""

    def setUp(self):
        super().setUp()
        from zango.apps.shared.app_templates.seed import PACKS_DIR

        import_pack(PACKS_DIR / "zango_app", publish_now=True)
        catalogue.clear_caches()

    def test_markdown_never_replaces_the_yaml_and_the_next_turn_gets_the_template(self):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.requirements import compose_analyst_prompt
        from zango.apps.agent_mode.tasks import _record_analyst_reply

        req = AgentRequirement(initial_prompt="a policy document manager")
        req.spec_markdown = ""
        req.session_id = "s1"
        req.save = lambda *a, **k: None
        reply = (
            "Building this on the ready-made toolkit.\n\n"
            "```zango-template\nzango-app\n```\n\n"
            "```zango-spec-draft\n## Policy manager\n\n- **Policy Document** — title\n```\n"
        )
        from unittest import mock

        messages = mock.MagicMock()
        messages.order_by.return_value.values_list.return_value.first.return_value = 2
        patches = [
            mock.patch.object(
                AgentRequirement, "messages", new_callable=mock.PropertyMock, return_value=messages
            ),
            mock.patch("zango.apps.agent_mode.models.AgentRequirementMessage.objects.create"),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        _record_analyst_reply(req, [reply], "s1", None)

        self.assertEqual(req.template_slug, GENERIC_SLUG)
        self.assertEqual(req.spec_format, "yaml")
        self.assertEqual(req.mode, "adopted")
        self.assertIn("spec_version", req.spec_markdown)  # the starter, not the Markdown
        self.assertNotIn("Policy Document", req.spec_markdown)
        self.assertFalse(
            [i for i in req.validation_issues or [] if i.get("code") == "yaml"]
        )

        class Ctx:
            app_name, workspace_path, packages, modules, roles = "x", "/w", [], [], []

        prompt = compose_analyst_prompt(req, Ctx(), "Approver is the department head")
        self.assertIn("has just chosen this template", prompt)
        self.assertIn("spec_replace_section", prompt)
        self.assertTrue(prompt.endswith("Approver is the department head"))

        # Once that turn has run, later turns are just the reply again.
        _record_analyst_reply(req, ["Noted."], "s1", None)
        self.assertEqual(req.mode, "interview")
        self.assertEqual(
            compose_analyst_prompt(req, Ctx(), "ok"), "ok"
        )


class CommitForBuildTests(AdoptMidConversationTests):
    def requirement(self, text):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.template_binding import seed_template_requirement

        r = AgentRequirement(initial_prompt="go")
        seed_template_requirement(r, catalogue.get_template(GENERIC_SLUG))
        r.spec_markdown, r.draft_revision = text, 3
        r.save = lambda *a, **k: None
        return r

    def test_markdown_never_replaces_the_yaml_and_the_next_turn_gets_the_template(self):
        pass  # covered by the parent class

    def test_a_valid_draft_is_finalized_and_a_broken_one_refused(self):
        from unittest import mock

        from zango.apps.agent_mode.models import RequirementStatus
        from zango.apps.agent_mode.template_spec import approval_problem, commit_draft

        example = catalogue.get_template(GENERIC_SLUG).example_yaml
        r = self.requirement(example)
        with mock.patch.object(type(r), "record_spec", lambda self, text, source=None: setattr(self, "spec_is_draft", False)), \
                mock.patch("zango.apps.agent_mode.template_spec._documents", return_value=[]):
            self.assertIsNone(commit_draft(r, 3))
        self.assertFalse(r.spec_is_draft)
        self.assertEqual(r.status, RequirementStatus.READY)
        self.assertIsNone(approval_problem(r))

        stale = self.requirement(example)
        code, _ = commit_draft(stale, 1)
        self.assertEqual(code, 409)

        broken = self.requirement(example.replace("spec_version: 1", "spec_version: one"))
        code, payload = commit_draft(broken, 3)
        self.assertEqual(code, 400)
        self.assertTrue(payload["issues"])

        decided = self.requirement(example)
        decided.open_decisions = [{"id": "d1", "question": "?"}]
        self.assertIsNone(commit_draft(decided, 3))  # left to approval_problem
        self.assertEqual(approval_problem(decided)[0], 409)


class SeedOrderTests(AppTemplatesTestBase):
    def test_the_generic_pack_is_seeded_before_the_packs_that_borrow_from_it(self):
        from zango.apps.shared.app_templates.seed import bundled_packs

        slugs = [json.loads((p / "template.json").read_text())["slug"] for p in bundled_packs()]
        self.assertEqual(slugs[0], GENERIC_SLUG)
        self.assertEqual(len(slugs), len(set(slugs)))


class StudioSkillTests(AppTemplatesTestBase):
    """The generic template's build skill, binary files included, and who borrows it."""

    def setUp(self):
        super().setUp()
        from zango.apps.shared.app_templates.seed import PACKS_DIR

        self.generic, _ = import_pack(PACKS_DIR / "zango_app", publish_now=True)
        catalogue.clear_caches()

    def test_binary_skill_files_round_trip_to_disk(self):
        rows = {r.path: r for r in self.generic.files.all()}
        self.assertIn("SKILL.md", rows)
        golden = rows["assets/goldens/badges.png"]
        self.assertTrue(golden.is_binary)
        self.assertTrue(golden.raw.startswith(b"\x89PNG"))
        self.assertFalse(any("__pycache__" in p or p.endswith(".pyc") for p in rows))
        self.assertEqual([i for i in lint(self.generic) if i["level"] == "error"], [])

        view = catalogue.get_template(GENERIC_SLUG)
        self.assertEqual(view.qualified_skill, "zango-tpl-zango-app:zango-app-studio")
        skill = Path(view.plugin_dir) / "skills" / "zango-app-studio"
        on_disk = (skill / "assets" / "goldens" / "badges.png").read_bytes()
        self.assertEqual(on_disk, golden.raw)
        self.assertTrue((skill / "scripts" / "spec_check.py").stat().st_mode & 0o100)

        from zango.apps.shared.app_templates.services.packs import export_pack, read_pack

        again = read_pack(export_pack(self.generic))
        self.assertEqual(again.skill_files["assets/goldens/badges.png"], golden.raw)

    def test_a_lean_template_is_built_with_the_generic_skill(self):
        from zango.apps.shared.app_templates.seed import PACKS_DIR

        import_pack(PACKS_DIR / "ordering_portal", publish_now=True)
        view = catalogue.get_template("ordering-portal")
        self.assertEqual(view.build_skill_name, "zango-app-studio")
        self.assertEqual(view.qualified_skill, "zango-tpl-zango-app:zango-app-studio")
        self.assertIn(f"/{GENERIC_SLUG}/", view.build_plugin_dir)
        self.assertNotEqual(view.build_plugin_dir, view.plugin_dir)

        from zango.apps.agent_mode.template_build import TemplateBuild

        build = TemplateBuild(template=view, spec_path="/tmp/spec/app_spec.yaml")
        self.assertTrue(Path(build.skill_dir, "SKILL.md").is_file())
        self.assertEqual(build.plugin_dir, view.plugin_dir)


class PinnedGenericTests(StudioSkillTests):
    def test_an_app_pinned_to_an_old_generic_version_builds_with_the_current_skill(self):
        from zango.apps.shared.app_templates.models import AppTemplateVersion

        # An older generic version, from before the template had a build skill.
        old = AppTemplateVersion.objects.create(
            template=self.generic.template,
            version="0.9.0",
            spec_format="yaml",
            spec_root="app_spec",
            spec_dialect=GENERIC_DIALECT,
            json_schema=self.generic.json_schema,
            starter_yaml=self.generic.starter_yaml,
        )
        catalogue.clear_caches()
        view = catalogue.get_template(GENERIC_SLUG, version_uuid=str(old.object_uuid))
        self.assertEqual(view.version, "0.9.0")
        self.assertEqual(view.qualified_skill, "zango-tpl-zango-app:zango-app-studio")
        self.assertTrue((Path(view.build_plugin_dir) / "skills" / "zango-app-studio" / "SKILL.md").is_file())

        current = catalogue.get_template(GENERIC_SLUG)
        self.assertEqual(current.build_plugin_dir, current.plugin_dir)  # its own


class BuildCheckTests(StudioSkillTests):
    def test_the_build_checker_findings_become_issues(self):
        from zango.apps.shared.app_templates.services.spec import yamlio
        from zango.apps.shared.app_templates.services.spec.build_check import build_issues

        view = catalogue.get_template(GENERIC_SLUG)
        doc = yamlio.load(view.example_yaml)
        found = build_issues(doc, view)
        self.assertFalse([i for i in found if i["level"] == "error"])
        warnings = [i for i in found if i["level"] == "warning"]
        self.assertTrue(warnings)  # lowercase warn/intent lines are read
        self.assertTrue(any("(fix: " in i["message"] for i in warnings))

        # Prose cut at an unquoted comma is a build error the schema can't see.
        broken = yamlio.load(
            view.example_yaml.replace(
                'computed: "Sum of po_line.amount, recalculated on every line save/delete."',
                "computed: Sum of po_line.amount, recalculated on every line save/delete.",
            )
        )
        errors = [i for i in build_issues(broken, view) if i["level"] == "error"]
        self.assertTrue(any("cut at a comma" in i["message"] for i in errors), errors)
        self.assertTrue(all(i["code"] == "build_check" and not i["structural"] for i in errors))
