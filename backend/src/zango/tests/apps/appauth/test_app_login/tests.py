import os
from django_tenants.utils import schema_context
from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from django.db import connection
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.appauth.models import AppUserModel, UserRoleModel
from zango.test.client import ZangoClient
from django.http import HttpResponseRedirect
from zango.test.client import BaseZangoRequestFactory


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class ZangoAppLoginTest(ZangoAppBaseTestCase):
    initialize_workspace = True

    @classmethod
    def get_test_module_path(cls):
        return os.path.join(
            "apps/appauth/test_app_login"
        )
    
    def setUp(self):
        super().setUp()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        client = ZangoClient(cls.tenant)
        client.create_roles(tenant=cls.tenant, names = ["app_login_user", "different_view_user"])
        cls.app_user = BaseZangoRequestFactory.create_user(
            tenant=cls.tenant,
            name="John Doe",
            email="test_login_user@gmail.com",
            mobile="0000000000",
            password="#Testpass123",
            roles=["app_login_user"],
            require_verification=False,
            force_password_reset=False,
        )
        client.user = cls.app_user
        cls.sync_policies()

    def test_app_login(self):
        session = self.client.session
        session["role_id"] = self.app_user.roles.filter(name="app_login_user").values_list("id", flat=True)[0]
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
        # add app_login_user role to app user.
        session = self.client.session
        session["role_id"] = self.app_user.roles.filter(name="app_login_user").values_list("id", flat=True)[0]
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
        self.app_user.add_roles(new_role_ids)

        # set role_id as per the view permissions.
        session = self.client.session
        session["role_id"] = self.app_user.roles.filter(name="different_view_user").values_list("id", flat=True)[0]  
        session.save()

        # now user has permission to this view.
        res = self.client.get("/login_app/dummy/")
        self.assertEqual(res.status_code, 200)
