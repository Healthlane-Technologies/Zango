from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from django.db import connection
from zango.apps.permissions.models import PolicyModel
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.test.client import ZangoClient


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class RolePolicyMappingTest(ZangoAppBaseTestCase):

    def test_app_login(self):
        self.setUpAppAndModule("auth_tests", "app_login")
        pass