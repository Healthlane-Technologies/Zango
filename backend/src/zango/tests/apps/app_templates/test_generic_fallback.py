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
