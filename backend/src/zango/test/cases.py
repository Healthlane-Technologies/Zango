import json
import os
import shutil

from pathlib import Path

from django_tenants.test.cases import FastTenantTestCase, TenantTestCase

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.test import override_settings

from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.shared.tenancy.models import ThemesModel
from zango.apps.shared.tenancy.tasks import initialize_workspace
from zango.test.client import ZangoClient


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

    def setUp(self):
        super().setUp()
        self.client = ZangoClient(self.tenant)

    @classmethod
    def get_app_name(cls):
        return "testapp"

    @classmethod
    def setup_tenant(cls, tenant):
        """
        Add any additional setting to the tenant before it get saved. This is required if you have
        required fields.
        :param tenant:
        :return:
        """
        tenant.name = cls.get_app_name()
        tenant.tenant_type = "app"
        return tenant

    @classmethod
    def get_test_tenant_domain(cls):
        return f"{cls.get_app_name()}.testserver.com"

    @classmethod
    def get_test_schema_name(cls):
        return cls.get_app_name()

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
    def get_test_module_path(cls):
        """
        If the module is not present at path tests/parent/module, override this method.
        """
        return os.path.join(cls.parent, cls.module)

    @classmethod
    def setUpTestModule(cls):
        # Paths to the test module directory and the files folder within it
        test_module_dir = os.path.join(
            Path(__file__).resolve().parent.parent, "tests", cls.get_test_module_path()
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
            dst = os.path.join(base_dir, cls.get_app_name(), "migrations")
            shutil.copytree(src, dst, dirs_exist_ok=True)

    @classmethod
    def assertModuleExists(cls, module_name, expected):
        """
        tests if the module exists inside test_project/workspaces/testapp/
        """
        module_path = (
            Path(settings.BASE_DIR) / "workspaces" / cls.get_app_name() / module_name
        )
        cls.assertEqual(module_path.exists(), expected)

    @classmethod
    def setUpAppAndModule(cls, parent, module):
        if cls.initialize_workspace:
            cls.setUpTestModule()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if cls.initialize_workspace:
            cls.clean_workspaces()
        connection.set_schema_to_public()
        ThemesModel.objects.filter(tenant=cls.tenant).delete()
        cls.domain.delete()
        cls.tenant.delete(force_drop=False)
        cls.remove_allowed_test_domain()

    @classmethod
    def get_package_root(cls):
        return os.path.join(
            settings.BASE_DIR, "workspaces", cls.get_app_name(), "packages"
        )

    @classmethod
    def get_app_root(cls):
        return os.path.join(settings.BASE_DIR, "workspaces", cls.get_app_name())

    @classmethod
    def sync_packages(cls):
        """Synchronize packages from the manifest file."""
        workspace_root = os.path.abspath(cls.get_app_root())
        manifest_path = os.path.join(workspace_root, "manifest.json")

        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest file not found at: {manifest_path}")

        with open(manifest_path, "r") as f:
            updated_app_manifest = json.load(f)

        installed_packages = updated_app_manifest.get("packages", [])
        if not installed_packages:
            print("Warning: No packages found in manifest.json")
            return

        print(f"Found {len(installed_packages)} packages to migrate")
        for package in installed_packages:
            package_name = package.get("name")
            if not package_name:
                print("Warning: Package entry missing 'name' field")
                continue

            print(f"Migrating package: {package_name}")
            try:
                if os.path.exists(
                    os.path.join(cls.get_package_root(), package_name, "migrations")
                ):
                    call_command(
                        "ws_migrate",
                        cls.get_app_name(),
                        "--package",
                        package_name,
                        verbosity=1,
                    )
                print(f"Successfully migrated package: {package_name}")
            except Exception as e:
                print(f"Warning: Failed to migrate package {package_name}: {str(e)}")

    @classmethod
    def sync_policies(cls):
        """Synchronize policies for the workspace."""
        with connection.cursor() as c:
            ws = Workspace(connection.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()

    @classmethod
    @override_settings(TEST_MIGRATION_RUNNING=True)
    def sync_database(cls):
        """Synchronize the test database."""
        cls.sync_packages()
        call_command("ws_migrate", cls.get_app_name())


class ZangoPackageBaseTestCase(ZangoAppBaseTestCase):
    initialize_workspace = True

    @classmethod
    def get_test_module_path(self):
        """
        If the module is not present at path tests/parent/module, override this method.
        """
        if self.parent and self.module:
            return os.path.join(self.parent, self.module)
        return ""

    def get_test_app_path(self):
        return os.path.join(
            Path(__file__).resolve().parent.parent,
            "test_project",
            "test_project",
            "workspaces",
            self.get_test_schema_name(),
        )

    @classmethod
    def setUpTestModule(cls):
        # Paths to the test module directory and the files folder within it
        test_module_dir = os.path.join(
            Path.cwd().parent, "tests", cls.get_test_module_path()
        )
        package_src_dir = os.path.join(Path.cwd().parent, "crud")
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

        if os.path.exists(workspace_src_dir) and os.path.isdir(workspace_src_dir):
            for item in os.listdir(workspace_src_dir):
                src = os.path.join(workspace_src_dir, item)
                dst = os.path.join(base_dir, cls.get_test_schema_name(), item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

        if os.path.exists(migrations_dir) and os.path.isdir(migrations_dir):
            src = migrations_dir
            dst = os.path.join(base_dir, cls.get_test_schema_name(), "migrations")
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            # create migrations folder
            os.makedirs(
                os.path.join(base_dir, cls.get_test_schema_name(), "migrations"),
                exist_ok=True,
            )

            # add empty __init__.py file
            with open(
                os.path.join(
                    base_dir, cls.get_test_schema_name(), "migrations", "__init__.py"
                ),
                "w",
            ) as f:
                f.write("")

        # Copy package source to the test workspace
        if os.path.exists(package_src_dir) and os.path.isdir(package_src_dir):
            dst = os.path.join(base_dir, cls.get_test_schema_name(), "packages", "crud")
            shutil.copytree(package_src_dir, dst, dirs_exist_ok=True)
