import json
import os
import shutil
import subprocess

import cookiecutter.main

from celery import shared_task

from django.conf import settings
from django.core.management import call_command
from django.utils import timezone

import zango

from .utils import DEFAULT_THEME_CONFIG, assign_policies_to_anonymous_user


@shared_task
def initialize_workspace(tenant_uuid, app_template_path=None, run_migrations=False):
    try:
        from zango.apps.shared.tenancy.models import TenantModel, ThemesModel

        tenant = TenantModel.objects.get(uuid=tenant_uuid)

        # Creating schema
        tenant.create_schema(check_if_exists=True)
        # migrating schema
        call_command(
            "migrate_schemas",
            tenant=True,
            schema_name=tenant.schema_name,
            interactive=False,
        )
        # Create workspace Folder
        project_base_dir = settings.BASE_DIR

        workspace_dir = os.path.join(project_base_dir, "workspaces")
        if not os.path.exists(workspace_dir):
            os.makedirs(workspace_dir)

        if app_template_path is not None:
            app_dir = os.path.join(workspace_dir, tenant.name)
            if not os.path.exists(app_dir):
                os.makedirs(app_dir)

            shutil.copytree(app_template_path, app_dir, dirs_exist_ok=True)

            shutil.rmtree(app_template_path)

            if os.path.exists(os.path.join(app_dir, "packages")):
                shutil.rmtree(os.path.join(app_dir, "packages"))
        else:
            # Creating app folder with the initial files
            template_directory = os.path.join(
                os.path.dirname(__file__), "workspace_folder_template"
            )
            cookiecutter_context = {
                "app_name": tenant.name,
                "zango_version": zango.__version__,
            }

            cookiecutter.main.cookiecutter(
                template_directory,
                extra_context=cookiecutter_context,
                output_dir=workspace_dir,
                no_input=True,
            )

        tenant.status = "deployed"
        tenant.deployed_on = timezone.now()
        tenant.save(update_fields=["status", "deployed_on"])

        if run_migrations:
            manifest = json.load(open(f"workspaces/{tenant.name}/manifest.json", "r"))
            os.remove(f"workspaces/{tenant.name}/manifest.json")
            with open(f"workspaces/{tenant.name}/manifest.json", "w") as f:
                f.write(json.dumps({"packages": []}))
            subprocess.run(["python", "manage.py", "ws_makemigration", tenant.name])
            with open(f"workspaces/{tenant.name}/manifest.json", "w") as f:
                f.write(json.dumps(manifest, indent=4))
        theme = ThemesModel.objects.create(
            name="Default", tenant=tenant, config=DEFAULT_THEME_CONFIG
        )

        if not app_template_path:
            assign_policies_to_anonymous_user(tenant.schema_name)
        else:
            try:
                subprocess.run(
                    ["zango", "update-apps", "--app_name", tenant.name], check=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Failed to update app: {e}")
        if tenant.status == "deployed":
            return {"result": "success"}
        else:
            return {"result": "failure", "error": "Failed, see error logs"}
    except Exception as e:
        import traceback

        return {
            "result": "failure",
            "error": traceback.format_exc(),
        }
