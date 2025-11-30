import os
import shutil

from pathlib import Path

from django_tenants.test.cases import FastTenantTestCase, TenantTestCase

from django.conf import settings
from django.db import connection

from zango.apps.shared.tenancy.models import ThemesModel
from zango.apps.shared.tenancy.schema import DEFAULT_AUTH_CONFIG
from zango.apps.shared.tenancy.tasks import initialize_workspace


class ZangoTestCase(TenantTestCase):
    @classmethod
    def tearDownClass(cls):
        connection.set_schema_to_public()
        cls.domain.delete()
        cls.tenant.delete(force_drop=False)
        cls.remove_allowed_test_domain()


class ZangoAppBaseTestCase(FastTenantTestCase):
    initialize_workspace = False
    parent = None
    module = None

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
        tenant.auth_config = DEFAULT_AUTH_CONFIG
        return tenant

    @classmethod
    def get_test_tenant_domain(cls):
        return "testapp.testserver.com"

    @classmethod
    def get_test_schema_name(cls):
        return "testapp"

    @classmethod
    def setUpClass(cls):
        if ".testserver.com" not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS += [".testserver.com"]

        super().setUpClass()
        if cls.initialize_workspace:
            res = initialize_workspace(cls.tenant.uuid)
            if not res["result"] == "success":
                raise Exception(res["error"])
            cls.setUpAppAndModule(cls.parent, cls.module)
        connection.set_tenant(cls.tenant)

    @classmethod
    def clean_workspaces(cls):
        workspaces_dir = os.path.join(settings.BASE_DIR, "workspaces")

        if os.path.exists(workspaces_dir) and os.path.isdir(workspaces_dir):
            shutil.rmtree(workspaces_dir)
            print("test workspaces have been deleted.")
        else:
            print("test workspaces does not exist.")

    @classmethod
    def get_test_module_path(self):
        """
        If the module is not present at path tests/parent/module, override this method.
        """
        return os.path.join(self.parent, self.module)

    @classmethod
    def setUpTestModule(self):
        # Paths to the test module directory and the files folder within it
        test_module_dir = os.path.join(
            Path(__file__).resolve().parent.parent, "tests", self.get_test_module_path()
        )

        if not os.path.exists(test_module_dir):
            raise FileNotFoundError(
                f"Test app module '{test_module_dir}' does not exist."
            )

        # Define the source directory for copying
        workspace_src_dir = os.path.join(test_module_dir, "workspace")
        migrations_dir = os.path.join(test_module_dir, "migrations")

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

        if os.path.exists(migrations_dir) and os.path.isdir(migrations_dir):
            src = migrations_dir
            dst = os.path.join(base_dir, "testapp", "migrations")
            shutil.copytree(src, dst, dirs_exist_ok=True)

    @classmethod
    def assertModuleExists(cls, module_name, expected):
        """
        tests if the module exists inside test_project/workspaces/testapp/
        """
        instance = cls()
        module_path = Path(settings.BASE_DIR) / "workspaces" / "testapp" / module_name
        instance.assertEqual(module_path.exists(), expected)

    @classmethod
    def setUpAppAndModule(cls, parent, module):
        if cls.initialize_workspace:
            cls.setUpTestModule()

    @classmethod
    def tearDownClass(cls):
        if cls.initialize_workspace:
            cls.clean_workspaces()
        connection.set_schema_to_public()
        ThemesModel.objects.filter(tenant=cls.tenant).delete()
        cls.domain.delete()
        cls.tenant.delete(force_drop=False)
        cls.remove_allowed_test_domain()
