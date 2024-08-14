from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from django.db import connection
from zango.apps.permissions.models import PolicyModel
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.appauth.models import AppUserModel, UserRoleModel
from zango.test.client import ZangoClient
from django.http import HttpResponseRedirect,HttpResponseForbidden


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class ZangoAppLoginTest(ZangoAppBaseTestCase):
    
    @classmethod
    def sync_policies(self):
        with connection.cursor() as c:
            ws = Workspace(connection.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()

    @classmethod
    def create_app_user(self):

        app_user_role = UserRoleModel.objects.filter(name="app_login_user").first()
        app_user_role.policies.add(PolicyModel.objects.get(name="AllowFromAnywhere"))
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
        self.setUpAppAndModule("auth_tests", "test_app_login")
        self.sync_policies()
        app_user = self.create_app_user()
        self.client = ZangoClient(self.tenant)
        self.client.user = app_user
        session = self.client.session
        
        if len(app_user.roles.all()) == 1:
            session["role_id"] = app_user.roles.all().values_list("id", flat=True)[0]
            session.save()

        logged_in = self.client.login(username="test_login_user@gmail.com", password="#Testpass123")
        
        if not logged_in:
            raise Exception("Unable to login user.")
        
        res = self.client.get("/login_app/customer/")
        self.assertEqual(res.status_code, 200)

        self.client.logout()
        # View forbidden after logout
        res = self.client.get("/login_app/customer/")
        self.assertIsInstance(res, HttpResponseForbidden)