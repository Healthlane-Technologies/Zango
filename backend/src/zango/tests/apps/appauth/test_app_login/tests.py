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
            "apps/appauth/test_app_login"
        )
    
    @classmethod
    def sync_policies(self):
        with connection.cursor() as c:
            ws = Workspace(connection.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()

    @classmethod
    def create_app_user(self):
        with schema_context(self.tenant.schema_name):
            UserRoleModel.objects.create(name="app_login_user")
            UserRoleModel.objects.create(name="different_view_user")
            app_user_role = UserRoleModel.objects.filter(name="app_login_user").first()
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
        self.sync_policies()
        self.client = ZangoClient(self.tenant)
        self.client.user = app_user
        session = self.client.session
        
        session["role_id"] = app_user.roles.filter(name="app_login_user").values_list("id", flat=True)[0]
        session.save()
        
        logged_in = self.client.login(username="test_login_user@gmail.com", password="#Testpass123")
        
        if not logged_in:
            raise Exception("Unable to login user.")
        
        res = self.client.get("/login_app/customer/")
        self.assertEqual(res.status_code, 200)

        self.client.logout()
        # View forbidden after logout
        res = self.client.get("/login_app/customer/")
        self.assertIsInstance(res, HttpResponseRedirect)
        self.assertEqual(res.url, "/login/")

    def test_logged_in_user_policy_map(self):
        app_user = self.create_app_user()
        self.sync_policies()
        self.client = ZangoClient(self.tenant)
        self.client.user = app_user

        # add app_login_user role to app user.
        session = self.client.session
        session["role_id"] = app_user.roles.filter(name="app_login_user").values_list("id", flat=True)[0]
        session.save()

        # login app user.
        logged_in = self.client.login(username="test_login_user@gmail.com", password="#Testpass123")
        
        if not logged_in:
            raise Exception("Unable to login user.")
        
        # app user does not have permission as different_view_user role is not assigned to app user.
        res = self.client.get("/login_app/dummy/")
        self.assertEqual(res.status_code, 403)

        # app_login_user has permission app_login_user is assigned to user.
        res = self.client.get("/login_app/customer/")
        self.assertEqual(res.status_code, 200)

        # assign app_login_user role and different_view_user role to user.
        new_role_ids = UserRoleModel.objects.filter(name__in=["app_login_user", "different_view_user"]).values_list("id", flat=True)
        app_user.add_roles(new_role_ids)

        # set role_id as per the view permissions.
        session = self.client.session
        session["role_id"] = app_user.roles.filter(name="different_view_user").values_list("id", flat=True)[0]  
        session.save()

        # now user has permission to this view.
        res = self.client.get("/login_app/dummy/")
        self.assertEqual(res.status_code, 200)
