import os

from django.conf import settings
from django.http import HttpResponseRedirect
from django.test import RequestFactory

from zango.apps.shared.platformauth.models import PlatformUserModel
from zango.apps.shared.platformauth.views import PlatformUserLoginView
from zango.apps.shared.tenancy.views import ConsoleView
from zango.cli.start_project import create_platform_user
from zango.test.cases import ZangoTestCase
from zango.test.client import ZangoClient


class ZangoConsoleTests(ZangoTestCase):
    """
    The console is served at /console/ on the public tenant, alongside the App Panel.
    """

    @classmethod
    def get_test_module_path(cls):
        return os.path.join("apps/console")

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.name = "testserver"
        tenant.tenant_type = "public"
        return tenant

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.testserver.com"

    @classmethod
    def get_test_schema_name(cls):
        return "public"

    @classmethod
    def setUpClass(cls):
        if "test.testserver.com" not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS += ["test.testserver.com"]

        create_platform_user("console_user@gmail.com", "Testpassword@123")

        super().setUpClass()

    def test_anonymous_redirects_to_login_with_next(self):
        self.client = ZangoClient(self.tenant)

        response = self.client.get("/console/apps")
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, "/auth/login/?next=/console/apps")

    def test_login_returns_to_console(self):
        self.client = ZangoClient(self.tenant)

        response = self.client.post(
            "/auth/login/?next=/console/apps",
            {
                "username": "console_user@gmail.com",
                "password": "Testpassword@123",  # pragma: allowlist secret
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/console/apps")

    def test_console_renders_for_platform_user(self):
        # Called directly: an authenticated request through the full middleware stack
        # needs allauth's usersessions table, which the public test schema lacks.
        request = RequestFactory().get("/console/apps")
        request.user = PlatformUserModel.objects.get(
            email="console_user@gmail.com"
        ).user

        response = ConsoleView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, ["console.html"])
        self.assertIn("platform_version", response.context_data)

    def test_login_without_console_next_goes_to_app_panel(self):
        factory = RequestFactory()
        for next_url in [
            "",
            "/platform/apps/",
            "https://evil.com/console/",
            "//evil.com/console/",
        ]:
            with self.subTest(next_url=next_url):
                request = factory.post(
                    f"/auth/login/?next={next_url}", HTTP_HOST="test.testserver.com"
                )
                self.assertEqual(
                    PlatformUserLoginView._post_login_url(request), "/platform"
                )
