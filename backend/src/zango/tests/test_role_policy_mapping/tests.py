import os
from pathlib import Path
import shutil
from zango.test.cases import ZangoAppBaseTestCase
from zango.apps.shared.tenancy.tasks import initialize_workspace
from django.conf import settings
from django.test import override_settings


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class ZangoModulesTest(ZangoAppBaseTestCase):

    @classmethod
    def setUpAppAndModule(self, module):
        initialize_workspace(self.tenant.uuid)
        self.setUpTestModule(module)
    
    def test_role_policy_mapping(self):
        # passing same module name in this class again will throw error.
        self.setUpAppAndModule("test_role_policy_mapping")