from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from django.db import connection
from zango.apps.appauth.models import UserRoleModel
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.core.utils import get_current_request
from django.http import HttpRequest
import ipaddress
from zango.test.client import ZangoClient


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class RolePolicyMappingTest(ZangoAppBaseTestCase):

    @classmethod
    def sync_policies(self):
        with connection.cursor() as c:
            ws = Workspace(self.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()
    
    def test_role_ip_permissions(self):
        self.setUpAppAndModule("policy_tests", "test_policy_ip_permission")
        self.sync_policies()

        self.client = ZangoClient(self.tenant)
        res = self.client.get("/customers/customer/",**{
            'REMOTE_ADDR': '1.2.3.4'
        })
        self.assertHTMLEqual(res.content.decode(), "<h1>Hey! This is IP testing response</h1>")

        # Permission denied for IP not listed in policies.json.
        res = self.client.get("/customers/customer/",**{
            'REMOTE_ADDR': '1.2.3.5'
        })
        self.assertEqual(res.status_code, 403)

    def test_cidr_ip_permissions(self):

        self.setUpAppAndModule("policy_tests", "test_policy_ip_permission")
        self.sync_policies()

        self.client = ZangoClient(self.tenant)
        res = self.client.get("/customers/cidr/",**{
            'REMOTE_ADDR': '10.0.0.2'
        })
        self.assertHTMLEqual(res.content.decode(), "<h1>Hey! This is CIDR IP testing response</h1>")

        # Permission denied for IP outside the range of "10.0.0.0/24" as listed in policies.json.
        res = self.client.get("/customers/cidr/",**{
            'REMOTE_ADDR': '10.0.0.256'
        })
        self.assertEqual(res.status_code, 403)