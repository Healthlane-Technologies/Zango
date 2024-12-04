import os

from django_tenants.utils import schema_context
from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from django.db import connection
from zango.apps.permissions.models import PolicyModel
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.test.client import ZangoClient


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class RolePolicyMappingTest(ZangoAppBaseTestCase):
    initialize_workspace = True

    @classmethod
    def get_test_module_path(self):
        return os.path.join(
            "apps/permissions/policy_framework/test_policy_ip_permission"
        )

    @classmethod
    def sync_policies(self):
        with schema_context(self.tenant.schema_name):
            ws = Workspace(self.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()

    def test_role_ip_permissions(self):

        self.sync_policies()
        # delete the all ip view policy as we have to check for specific IPs.
        PolicyModel.objects.get(name="AllIPGetViewAccess").delete()
        PolicyModel.objects.get(name="AllowFromAnywhere").delete()

        self.client = ZangoClient(self.tenant)
        res = self.client.get("/customers/customer/", **{"REMOTE_ADDR": "1.2.3.4"})
        self.assertHTMLEqual(
            res.content.decode(), "<h1>Hey! This is IP testing response</h1>"
        )

        # Permission denied for IP not listed in policies.json.
        res = self.client.get("/customers/customer/", **{"REMOTE_ADDR": "1.2.3.5"})
        self.assertEqual(res.status_code, 403)

    def test_cidr_ip_permissions(self):

        self.sync_policies()
        # delete the all ip view policy as we have to check for specific IPs.
        PolicyModel.objects.get(name="AllIPGetViewAccess").delete()
        PolicyModel.objects.get(name="AllowFromAnywhere").delete()

        self.client = ZangoClient(self.tenant)
        res = self.client.get("/customers/cidr/", **{"REMOTE_ADDR": "10.0.0.2"})
        self.assertHTMLEqual(
            res.content.decode(), "<h1>Hey! This is CIDR IP testing response</h1>"
        )

        # Permission denied for IP outside the range of "10.0.0.0/24" as listed in policies.json.
        res = self.client.get("/customers/cidr/", **{"REMOTE_ADDR": "10.0.1.252"})
        self.assertEqual(res.status_code, 403)

    def test_all_ip_permissions(self):

        self.sync_policies()

        self.client = ZangoClient(self.tenant)

        # returns a response to all IPs.
        res = self.client.get("/customers/all-ip/", **{"REMOTE_ADDR": "1.2.3.9"})
        self.assertHTMLEqual(
            res.content.decode(), "<h1>Hey! This view can be viewed from all IPs.</h1>"
        )

        res = self.client.get("/customers/all-ip/", **{"REMOTE_ADDR": "10.0.4.2"})
        self.assertHTMLEqual(
            res.content.decode(), "<h1>Hey! This view can be viewed from all IPs.</h1>"
        )

        res = self.client.get("/customers/all-ip/", **{"REMOTE_ADDR": "10.0.3.1"})
        self.assertHTMLEqual(
            res.content.decode(), "<h1>Hey! This view can be viewed from all IPs.</h1>"
        )
