import os

import cookiecutter.main
from celery import shared_task

from django.conf import settings
from django.core.management import call_command

from .utils import assign_policies_to_anonymous_user, DEFAULT_THEME_CONFIG


@shared_task
def initialize_workspace(tenant_uuid):
    try:
        from zelthy.apps.shared.tenancy.models import TenantModel, ThemesModel

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

        # Creating app folder with the initial files
        template_directory = os.path.join(
            os.path.dirname(__file__), "workspace_folder_template"
        )
        cookiecutter_context = {"app_name": tenant.name}

        cookiecutter.main.cookiecutter(
            template_directory,
            extra_context=cookiecutter_context,
            output_dir=workspace_dir,
            no_input=True,
        )

        tenant.status = "deployed"
        tenant.save()

        assign_policies_to_anonymous_user(tenant.schema_name)
        theme = ThemesModel.objects.create(
            name="Default", tenant=tenant, config=DEFAULT_THEME_CONFIG
        )
        if tenant.status == "deployed":
            return {"result": "success"}
        else:
            return {"result": "failure", "error": "Failed, see error logs"}
    except Exception as e:
        return {
            "result": "failure",
            "error": str(e),
        }
