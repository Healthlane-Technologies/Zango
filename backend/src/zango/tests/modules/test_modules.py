import os
from pathlib import Path
import shutil
from zango.test.cases import ZangoAppBaseTestCase
from zango.apps.shared.tenancy.tasks import initialize_workspace
from django.conf import settings


class ZangoModulesTest(ZangoAppBaseTestCase):
    @classmethod
    def setUpTestModule(self, module_name):
        # Paths to the test module directory and the files folder within it
        test_module_dir = os.path.join(
            Path(__file__).resolve().parent.parent, "modules", module_name
        )
        if not os.path.exists(test_module_dir):
            raise FileNotFoundError(f"Test app module '{test_module_dir}' does not exist.")
        files_dir = os.path.join(test_module_dir, "files")

        base_dir = os.path.join(settings.BASE_DIR, "workspaces")
        app_dir = os.path.join(base_dir, "testapp")
        app_module_dir = os.path.join(base_dir, "testapp", module_name)

        # Ensure the BASE_DIR and testapp directories exist
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(app_dir, exist_ok=True)
        os.makedirs(app_module_dir, exist_ok=True)

        

        # Copy settings.json and manifest.json to BASE_DIR (workspaces)
        for filename in ["settings.json", "manifest.json"]:
            src = os.path.join(test_module_dir, filename)
            dst = os.path.join(base_dir, app_dir)
            if os.path.exists(src):
                shutil.copy2(src, dst)

        # Copy all files from files_dir to BASE_DIR/testapp/customers
        if os.path.exists(files_dir) and os.path.isdir(files_dir):
            for file_name in os.listdir(files_dir):
                src_file = os.path.join(files_dir, file_name)
                dst_file = os.path.join(app_module_dir, file_name)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)

    @classmethod
    def setUpAppAndModule(self, module):
        initialize_workspace(self.tenant.uuid)
        self.setUpTestModule(module)
    
    def test_app_module_exist(self):
        self.setUpAppAndModule("customers")
        self.assertModuleExists("customers", True)
