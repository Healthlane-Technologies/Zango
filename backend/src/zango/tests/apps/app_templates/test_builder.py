import json

from rest_framework.test import APIRequestFactory, force_authenticate

from zango.apps.shared.app_templates.seed import PACKS_DIR
from zango.apps.shared.app_templates.services import catalogue
from zango.apps.shared.app_templates.services.builder import attach_builder, compose
from zango.apps.shared.app_templates.services.packs import import_pack, lint, publish
from zango.apps.shared.app_templates.services.workspace import new_draft_from

from .test_catalogue_api import _user
from .tests import AppTemplatesTestBase


PAGE = "<html><head></head><body><script>var J={};</script></body></html>"


class BuilderTests(AppTemplatesTestBase):
    def setUp(self):
        super().setUp()
        root = self.pack()
        (root / "builder").mkdir()
        (root / "builder" / "adapter.js").write_text("window.__bridge = true;")
        manifest = json.loads((root / "template.json").read_text())
        manifest["builder"] = {"adapter": "builder/adapter.js"}
        (root / "template.json").write_text(json.dumps(manifest))
        self.root = root

    def with_builder(self):
        base, _ = import_pack(self.root, publish_now=True)
        draft = new_draft_from(base, "1.0.1")
        attach_builder(draft, PAGE)
        return publish(draft)

    def test_packs_ship_the_adapter_not_the_page(self):
        version, _ = import_pack(self.root)
        self.assertEqual(version.builder_adapter, "window.__bridge = true;")
        self.assertFalse(version.has_builder)

    def test_compose_injects_the_adapter_after_the_page_scripts(self):
        version = self.with_builder()
        html = compose(version)
        self.assertLess(html.index("var J={}"), html.index("window.__bridge"))
        self.assertLess(html.index("window.__bridge"), html.lower().rindex("</body>"))

    def test_a_page_without_an_adapter_does_not_lint(self):
        version, _ = import_pack(self.pack("plain", slug="plain"))
        attach_builder(version, PAGE)
        self.assertTrue(any(i["file"] == "builder" for i in lint(version)))

    def test_newer_packs_keep_the_attached_page(self):
        with_page = self.with_builder()
        _, created = import_pack(self.root)
        self.assertFalse(created, "re-importing the same pack must be a no-op")
        manifest = json.loads((self.root / "template.json").read_text())
        manifest["version"] = "1.1.0"
        (self.root / "template.json").write_text(json.dumps(manifest))
        (self.root / "starter.yaml").write_text("journey: v2\n")
        v2, created = import_pack(self.root, publish_now=True)
        self.assertTrue(created)
        self.assertEqual(v2.builder_html, with_page.builder_html)
        self.assertTrue(v2.has_builder)

    def _get(self, view, **kwargs):
        request = APIRequestFactory().get("/x/", HTTP_HOST="test.testserver.com")
        force_authenticate(request, user=_user())
        return view.as_view()(request, **kwargs)

    def test_builder_url_and_page(self):
        from zango.api.platform.app_templates.v1.views import (
            TemplateBuilderPageView,
            TemplateBuilderView,
        )

        version = self.with_builder()
        catalogue.clear_caches()
        body = json.loads(
            self._get(
                TemplateBuilderView, slug="demo", version_uuid=version.object_uuid
            ).content
        )
        url = body["response"]["builder_url"]
        self.assertTrue(url.endswith(f"/versions/{version.object_uuid}/builder.html"))
        page = self._get(
            TemplateBuilderPageView, slug="demo", version_uuid=version.object_uuid
        )
        self.assertEqual(page.status_code, 200)
        self.assertIn("text/html", page["Content-Type"])
        self.assertIn("sandbox", page["Content-Security-Policy"])
        self.assertIn(b"window.__bridge", page.content)

    def test_no_builder_means_no_url(self):
        from zango.api.platform.app_templates.v1.views import (
            TemplateBuilderPageView,
            TemplateBuilderView,
        )

        version, _ = import_pack(self.root, publish_now=True)
        body = json.loads(
            self._get(
                TemplateBuilderView, slug="demo", version_uuid=version.object_uuid
            ).content
        )
        self.assertIsNone(body["response"]["builder_url"])
        self.assertEqual(
            self._get(
                TemplateBuilderPageView, slug="demo", version_uuid=version.object_uuid
            ).status_code,
            404,
        )

    def test_the_psp_pack_bundles_its_adapter(self):
        adapter = (PACKS_DIR / "psp" / "builder" / "adapter.js").read_text()
        self.assertIn("zango-builder/1", adapter)
        version, _ = import_pack(PACKS_DIR / "psp")
        self.assertEqual(version.builder_adapter, adapter)
