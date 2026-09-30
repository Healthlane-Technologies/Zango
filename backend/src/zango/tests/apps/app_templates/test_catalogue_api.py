import json

from pathlib import Path
from unittest import mock

from rest_framework.test import APIRequestFactory, force_authenticate

from zango.apps.shared.app_templates.models import AppTemplateBinding, BindingSource
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.packs import import_pack
from zango.cli.start_project import create_platform_user

from .tests import AppTemplatesTestBase


class _Ctx:
    app_name = "clinic"
    workspace_path = "/w"
    packages = []
    modules = []
    roles = []


def _user():
    from zango.apps.shared.platformauth.models import PlatformUserModel

    pu = PlatformUserModel.objects.filter(email="tpl_user@example.com").first()
    if pu is None:
        create_platform_user(
            "tpl_user@example.com", "Testpassword@123"
        )  # pragma: allowlist secret
        pu = PlatformUserModel.objects.get(email="tpl_user@example.com")
    return pu.user


class CatalogueApiTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        self.version, _ = import_pack(self.pack(), publish_now=True)
        catalogue.clear_caches()
        self.factory = APIRequestFactory()

    def _get(self, view, path, **kwargs):
        request = self.factory.get(path, HTTP_HOST="test.testserver.com")
        force_authenticate(request, user=_user())
        response = view.as_view()(request, **kwargs)
        return response.status_code, json.loads(response.content)

    def test_list_returns_published_templates_with_catalogue(self):
        from zango.api.platform.app_templates.v1.views import TemplateListView

        status, body = self._get(
            TemplateListView, "/api/v1/platform/app-templates/templates/"
        )
        self.assertEqual(status, 200)
        demo = next(t for t in body["response"]["templates"] if t["slug"] == "demo")
        self.assertEqual(demo["version"], "1.0.0")
        self.assertEqual(demo["catalogue"]["description"], "Only for tests.")
        self.assertEqual(
            demo["sections"], [{"id": "roles", "title": "Roles", "hint": ""}]
        )
        self.assertEqual(demo["apps_using"], 0)

    def test_list_counts_bound_apps(self):
        from zango.api.platform.app_templates.v1.views import TemplateListView

        AppTemplateBinding.objects.create(
            tenant=self.tenant,
            template=self.version.template,
            version=self.version,
            source=BindingSource.SCAFFOLD,
        )
        _, body = self._get(
            TemplateListView, "/api/v1/platform/app-templates/templates/"
        )
        demo = next(t for t in body["response"]["templates"] if t["slug"] == "demo")
        self.assertEqual(demo["apps_using"], 1)

    def test_detail_and_404(self):
        from zango.api.platform.app_templates.v1.views import TemplateDetailView

        status, body = self._get(TemplateDetailView, "/x/", slug="demo")
        self.assertEqual(status, 200)
        detail = body["response"]["template"]
        self.assertEqual([v["version"] for v in detail["versions"]], ["1.0.0"])
        self.assertIn("journey: demo", detail["starter_yaml"])
        status, _ = self._get(TemplateDetailView, "/x/", slug="nope")
        self.assertEqual(status, 404)

    def test_drafts_are_not_listed(self):
        from zango.api.platform.app_templates.v1.views import TemplateListView

        import_pack(self.pack("other", slug="other"))
        _, body = self._get(
            TemplateListView, "/api/v1/platform/app-templates/templates/"
        )
        self.assertNotIn("other", [t["slug"] for t in body["response"]["templates"]])


class ScaffoldTemplateTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        self.version, _ = import_pack(self.pack(), publish_now=True)
        catalogue.clear_caches()
        self.factory = APIRequestFactory()

    def _post(self, data):
        from zango.api.platform.agent_mode_admin.v1.views import (
            AgentAppScaffoldCreateView,
        )

        request = self.factory.post(
            "/api/v1/platform/agent-mode/scaffolds/",
            data,
            format="json",
            HTTP_HOST="test.testserver.com",
        )
        force_authenticate(request, user=_user())
        with (
            mock.patch(
                "zango.apps.agent_mode.availability.probe",
                return_value={"available": True, "reasons": []},
            ),
            mock.patch(
                "zango.apps.agent_mode.tasks.agent_app_scaffold.apply_async"
            ) as dispatch,
        ):
            dispatch.return_value = mock.Mock(id="task-1")
            response = AgentAppScaffoldCreateView.as_view()(request)
        return response.status_code, json.loads(response.content)

    def test_template_pins_the_current_version_and_prompt_is_optional(self):
        from zango.apps.shared.agent_mode.models import AgentAppScaffold

        status, body = self._post({"template_slug": "demo"})
        self.assertIn(status, (200, 201), body)
        scaffold = AgentAppScaffold.objects.order_by("-created_at").first()
        self.assertEqual(scaffold.template_version_id, self.version.pk)
        self.assertTrue(scaffold.prompt)
        self.assertEqual(
            body["response"]["template"],
            {"slug": "demo", "name": "Demo Program", "version": "1.0.0"},
        )

    def test_unknown_template_is_refused(self):
        status, _ = self._post({"template_slug": "nope", "prompt": "x"})
        self.assertEqual(status, 400)

    def test_brief_only_still_needs_a_prompt(self):
        status, _ = self._post({})
        self.assertEqual(status, 400)


class TemplateRequirementTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        self.version, _ = import_pack(self.pack(), publish_now=True)
        catalogue.clear_caches()

    def test_seeding_pins_the_version_and_starts_from_the_starter(self):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.template_binding import seed_template_requirement

        requirement = AgentRequirement(initial_prompt="go")
        seed_template_requirement(requirement, catalogue.get_template("demo"))
        self.assertEqual(requirement.template_slug, "demo")
        self.assertEqual(requirement.template_version, "1.0.0")
        self.assertEqual(
            str(requirement.template_version_uuid), str(self.version.object_uuid)
        )
        self.assertEqual(requirement.spec_format, "yaml")
        self.assertTrue(requirement.spec_is_draft)
        self.assertEqual(requirement.spec_markdown, "journey: demo")
        self.assertEqual(requirement.draft_revision, 1)

    def test_pinned_requirement_keeps_its_version_after_a_new_publish(self):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.template_binding import seed_template_requirement

        requirement = AgentRequirement(initial_prompt="go")
        seed_template_requirement(requirement, catalogue.get_template("demo"))
        import_pack(
            self.pack(version="2.0.0", starter="journey: v2\n"), publish_now=True
        )
        catalogue.clear_caches()
        self.assertEqual(requirement.template.version, "1.0.0")
        self.assertEqual(catalogue.get_template("demo").version, "2.0.0")

    def test_first_turn_on_a_template_skips_the_offer(self):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.requirements import compose_analyst_prompt
        from zango.apps.agent_mode.template_binding import seed_template_requirement

        requirement = AgentRequirement(initial_prompt="go")
        seed_template_requirement(requirement, catalogue.get_template("demo"))
        text = compose_analyst_prompt(requirement, _Ctx(), "a demo program")
        self.assertIn("This app is built on a template", text)
        self.assertIn("slug `demo`, version 1.0.0", text)
        self.assertNotIn("Templates available for this ask", text)
        view = requirement.template
        self.assertIn(view.file_path("interview"), text)
        self.assertIn(view.file_path("starter"), text)
        self.assertTrue(Path(view.file_path("interview")).is_file())

    def test_change_request_carries_the_approved_journey(self):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.requirements import compose_analyst_prompt
        from zango.apps.agent_mode.template_binding import seed_template_requirement

        requirement = AgentRequirement(initial_prompt="add a role")
        seed_template_requirement(
            requirement,
            catalogue.get_template("demo"),
            "journey: demo\nroles:\n  - name: Doctor\n",
        )
        text = compose_analyst_prompt(requirement, _Ctx(), "add a role")
        self.assertIn("already runs on the template", text)
        self.assertIn("name: Doctor", text)

    def test_from_scratch_requirements_still_get_the_catalogue(self):
        from zango.apps.agent_mode.models import AgentRequirement
        from zango.apps.agent_mode.requirements import compose_analyst_prompt

        text = compose_analyst_prompt(
            AgentRequirement(initial_prompt="x"), _Ctx(), "a demo program"
        )
        self.assertIn("Templates available for this ask", text)
        self.assertIn("slug: demo", text)

    def test_binding_is_kept_on_rebind(self):
        from zango.apps.agent_mode.template_binding import bind_app, binding_for

        bind_app(self.tenant, self.version, BindingSource.SCAFFOLD)
        v2, _ = import_pack(
            self.pack(version="2.0.0", starter="journey: v2\n"), publish_now=True
        )
        bind_app(self.tenant, v2, BindingSource.REQUIREMENT)
        self.assertEqual(binding_for(self.tenant).version_id, self.version.pk)
