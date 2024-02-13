import os

from django.conf import settings
from django.db import connection

from django.core.management.commands.makemigrations import (
    Command as MakeMigrationsCommand,
)
from zelthy.apps.shared.tenancy.models import TenantModel
from zelthy.apps.dynamic_models.workspace.base import Workspace


class Command(MakeMigrationsCommand):
    """
    Custom makemigration to generate migration files for dynamic_models. The
    workspace name is a mandatory argument with this command. The workspace is
    initialized and the models are loaded after which the migrations are
    generated. The migrations for the workspace and all the packages are
    generated through this command.

    Known issues:
        - Migrations generated for relational tables where the referred table
        is not migrated already causes an issue in the migration. In such
        cases, the migration file has to be manually edited to move the
        relational field out of the CreateModel block to a ModifyField block.
    """

    help = "Creates new migration(s) for a workspace."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "workspace",
            help="The workspace name to be used.",
        )
        parser.add_argument(
            "--test", action="store_true", help="Run the migration for test database"
        )
        parser.add_argument(
            "--is_package_migration",
            action="store_true",
            help="Run makemigration on package models",
        )

    def handle(self, *app_labels, **options):
        is_test_mode = options["test"]
        tenant = options["workspace"]
        tenant_obj = TenantModel.objects.get(name=tenant)
        connection.set_tenant(tenant_obj)
        if is_test_mode:
            connection.settings_dict["NAME"] = (
                "test_" + connection.settings_dict["NAME"]
            )
        migrations_dir = (
            f"{settings.BASE_DIR}/workspaces/{options['workspace']}/migrations/"
        )
        # Create the migration directory if it doesn't exist
        os.makedirs(migrations_dir, exist_ok=True)

        # Add an __init__.py file in the folder if it doesn't exist
        init_file = os.path.join(migrations_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w"):
                pass  # Creates an empty __init__.py file

        settings.MIGRATION_MODULES = {
            f"dynamic_models": f"workspaces.{options['workspace']}.migrations"
        }
        w = Workspace(tenant_obj, None, True)
        if options["is_package_migration"]:
            w.load_models()
        else:
            w.load_models(migration=True)
        super().handle("dynamic_models", **options)
