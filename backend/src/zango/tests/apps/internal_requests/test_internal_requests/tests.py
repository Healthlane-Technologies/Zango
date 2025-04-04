import os
import json

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
            "apps/internal_requests/test_internal_requests"
        )
    
    @classmethod
    def sync_policies(self):
        with connection.cursor() as c:
            ws = Workspace(connection.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()
    
    def test_internal_request(self):
        self.sync_policies()
        self.client = ZangoClient(self.tenant)

        res = self.client.post("/app/view/")
        self.assertEqual(res.status_code, 200)
    
    def test_internal_request_headers(self):
        self.sync_policies()
        self.client = ZangoClient(self.tenant)

        res = self.client.post("/app/view/?action=get_headers")
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/app/view/?action=post_headers")
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/app/view/?action=put_headers")
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/app/view/?action=delete_headers")
        self.assertEqual(res.status_code, 200)


    def test_internal_request_query_params(self):
        self.sync_policies()
        self.client = ZangoClient(self.tenant)

        res = self.client.post("/app/view/?action=get_query_params")
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/app/view/?action=post_query_params")
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/app/view/?action=put_query_params")
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/app/view/?action=delete_query_params")
        self.assertEqual(res.status_code, 200)

    def test_internal_request_path_params(self):
        pass

    def test_internal_request_json_data(self):
        pass

    def test_internal_request_files(self):
        pass

    def test_internal_request_multiple_files(self):
        pass

    def test_internal_request_form_data(self):
        pass

    def test_internal_request_cookies(self):
        pass
