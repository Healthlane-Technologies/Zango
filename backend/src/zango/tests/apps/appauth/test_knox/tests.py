import os
from django_tenants.utils import schema_context
from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from django.db import connection
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.appauth.models import AppUserModel, UserRoleModel
from zango.test.client import ZangoClient
from django.http import HttpResponseRedirect


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class ZangoAppLoginTest(ZangoAppBaseTestCase):
    initialize_workspace = True

    @classmethod
    def get_test_module_path(self):
        return os.path.join(
            "apps/appauth/test_knox"
        )
    
    @classmethod
    def sync_policies(self):
        with connection.cursor() as c:
            ws = Workspace(connection.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()

    @classmethod
    def create_app_user(self, role="knox_user"):
        with schema_context(self.tenant.schema_name):
            UserRoleModel.objects.create(name="knox_user")
            UserRoleModel.objects.create(name="different_user")
            app_user_role = UserRoleModel.objects.filter(name=role).first()
            role_ids = [app_user_role.id]
            result = AppUserModel.create_user(
                name="John Doe",
                email="test_login_user@gmail.com",
                mobile="0000000000",
                password="#Testpass123",
                role_ids=role_ids,
                require_verification=False,
                force_password_reset=False,
            )
            if not result["success"]:
                raise Exception(result["message"])
            return result["app_user"]

    def test_app_login(self):
        app_user = self.create_app_user()
        _, token = app_user.generate_auth_token("knox_user")
        self.sync_policies()
        self.client = ZangoClient(self.tenant)
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        
        res = self.client.get("/login_app/customer/")
        self.assertEqual(res.status_code, 200)
    
    def test_app_login_with_different_user(self):
        app_user = self.create_app_user(role="different_user")
        _, token = app_user.generate_auth_token("different_user")
        self.sync_policies()
        self.client = ZangoClient(self.tenant)
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        
        res = self.client.get("/login_app/customer/")
        self.assertEqual(res.status_code, 403)
    
    def test_no_token(self):
        self.sync_policies()
        self.client = ZangoClient(self.tenant)
        
        res = self.client.get("/login_app/customer/")
        self.assertIsInstance(res, HttpResponseRedirect)
        self.assertEqual(res.url, "/login/")
    
    def test_invalid_token(self):
        self.sync_policies()
        self.client = ZangoClient(self.tenant)
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer invalid_token"
        
        res = self.client.get("/login_app/customer/")
        self.assertEqual(res.status_code, 401)
    
    def test_null_token(self):
        self.sync_policies()
        self.client = ZangoClient(self.tenant)
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer "
        
        res = self.client.get("/login_app/customer/")
        self.assertEqual(res.status_code, 401)
    
    def test_anonymous_user(self):
        self.sync_policies()
        self.client = ZangoClient(self.tenant)
        
        res = self.client.get("/login_app/dummy/")
        self.assertEqual(res.status_code, 200)
