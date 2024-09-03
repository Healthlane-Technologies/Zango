import os
from django.http import HttpResponseRedirect

from zango.test.cases import ZangoTestCase
from zango.test.client import ZangoClient
from django.test import override_settings
from django.conf import settings
from zango.cli.start_project import create_platform_user


@override_settings(ROOT_URLCONF="zango.tests.test_client.urls")
class ZangoPlatformLoginTests(ZangoTestCase):
    """
    This test class is configured to use public tenant.
    """
    @classmethod
    def get_test_module_path(self):
        return os.path.join(
            "apps/appauth/test_platform_login"
        )

    @classmethod
    def setup_tenant(cls, tenant):
        """
        Add any additional setting to the tenant before it get saved. This is required if you have
        required fields.
        :param tenant:
        :return:
        """
        tenant.name = "testserver"
        tenant.tenant_type = "public"  # set this to app for app level tenants
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

        create_platform_user("test_user@gmail.com", "Testpassword@123")

        super().setUpClass()

    def test_platform_direct_response(self):
        self.client = ZangoClient(self.tenant)

        response = self.client.get("/auth/login/")
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "app_panel/app_panel_login.html")

    def test_platform_redirect_response(self):
        self.client = ZangoClient(self.tenant)

        response = self.client.get("/platform/")
        self.assertIsInstance(response, HttpResponseRedirect)

        self.assertEqual(response.url, "/auth/login/?next=/platform/")

        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "app_panel/app_panel_login.html")

    def test_client_login(self):
        self.client = ZangoClient(self.tenant)
        res = self.client.login(
            username="test_user@gmail.com", password="Testpassword@123" #pragma: allowlist secret
        )
        self.assertTrue(res)
