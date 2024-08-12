import os
import shutil
from pathlib import Path
from django.core.management import call_command
from django.db import connection
from django_tenants.test.cases import TenantTestCase
from django.test import TransactionTestCase
from django.conf import settings
from zango.test.client import ZangoClient
from django.contrib.auth import SESSION_KEY
from zango.apps.appauth.models import AppUserModel, UserRoleModel
from zango.cli.start_project import create_platform_user


class ZangoTestCase(TenantTestCase):
    @classmethod
    def tearDownClass(cls):
        connection.set_schema_to_public()
        cls.domain.delete()
        cls.tenant.delete(force_drop=False)
        cls.remove_allowed_test_domain()


class FastZangoTestCase(ZangoTestCase):
    """
    A faster variant of `ZangoTestCase`: the test schema and its migrations will only be created and ran once.

    WARNING: although this does produce significant improvements in speed it also means that these type of tests
             are not fully encapsulated and that some state will be shared between tests.

    See: https://github.com/tomturner/django-tenants/issues/100
    """

    pass


# class TestDataMixin:
#     user = None
#     @classmethod
#     def setUpTestData(cls):
#         pass


class ZangoAppBaseTestCase(ZangoTestCase):
    @classmethod
    def setup_tenant(cls, tenant):
        """
        Add any additional setting to the tenant before it get saved. This is required if you have
        required fields.
        :param tenant:
        :return:
        """
        tenant.name = "testapp"
        tenant.tenant_type = "app"
        return tenant

    @classmethod
    def get_test_tenant_domain(cls):
        return "testapp.testserver.com"

    @classmethod
    def get_test_schema_name(cls):
        return "testapp"

    @classmethod
    def login_platform_user(cls):
        cls.client = ZangoClient(cls.tenant)
        res = cls.client.post(
            "auth/login/",
            {"username": "test_user@gmail.com", "password": "Testpassword@123"},
        )
        print(res.__dict__)

    @classmethod
    def setUpClass(cls):
        if ".testserver.com" not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS += [".testserver.com"]

        super().setUpClass()
        # cls.login_platform_user()

    @classmethod
    def clean_workspaces(cls):
        workspaces_dir = os.path.join(settings.BASE_DIR, "workspaces")

        if os.path.exists(workspaces_dir) and os.path.isdir(workspaces_dir):
            shutil.rmtree(workspaces_dir)
            print("workspaces have been deleted.")
        else:
            print("workspaces does not exist.")
    
    @classmethod
    def setUpTestModule(self, module_name):
        # Paths to the test module directory and the files folder within it
        test_module_dir = os.path.join(
            Path(__file__).resolve().parent.parent, module_name
        )
        if not os.path.exists(test_module_dir):
            raise FileNotFoundError(f"Test app module '{test_module_dir}' does not exist.")

        # Define the source directory for copying
        workspace_src_dir = os.path.join(test_module_dir, "workspace")
        
        # Define the destination directory
        base_dir = os.path.join(settings.BASE_DIR, "workspaces")

        # Ensure the destination directory exists
        os.makedirs(base_dir, exist_ok=True)

        # Copy the entire 'workspace' directory to BASE_DIR/workspaces
        if os.path.exists(workspace_src_dir) and os.path.isdir(workspace_src_dir):
            for item in os.listdir(workspace_src_dir):
                src = os.path.join(workspace_src_dir, item)
                dst = os.path.join(base_dir, "testapp", item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

    @classmethod
    def assertModuleExists(cls, module_name, expected):
        """
        tests if the module exists insidev test_project/workspaces/testapp/
        """
        instance = cls()
        module_path = Path(settings.BASE_DIR) / "workspaces" / "testapp" / module_name
        instance.assertEqual(module_path.exists(), expected)

    @classmethod
    def tearDownClass(cls):
        cls.clean_workspaces()
        connection.set_schema_to_public()
        cls.domain.delete()
        cls.tenant.delete(force_drop=False)
        cls.remove_allowed_test_domain()
