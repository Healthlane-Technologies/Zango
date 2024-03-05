import os

from django_tenants.management.commands.migrate_schemas import MigrateSchemasCommand
from django.conf import settings
from django.db import connection
from zelthy.apps.shared.tenancy.models import TenantModel


class Command(MigrateSchemasCommand):
    # TODO: Handle package migration

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "workspace",
            help="The workspace name to be used.",
        )
        parser.add_argument(
            "--test", action="store_true", help="Run the migration for test database"
        )
        parser.add_argument("--package", help="Run the migrations for the package")

    def handle(self, *args, **options):
        tenant_obj = TenantModel.objects.get(name=options["workspace"])
        is_test_mode = options["test"]
        if is_test_mode:
            connection.settings_dict["NAME"] = (
                "test_" + connection.settings_dict["NAME"]
            )
        if options["package"] is None:
            settings.MIGRATION_MODULES = {
                f"dynamic_models": f"workspaces.{ options['workspace']}.migrations"
            }
        else:
            settings.MIGRATION_MODULES = {
                f"dynamic_models": f"workspaces.{ options['workspace']}.packages.{options['package']}.migrations"
            }
        options["schema_name"] = tenant_obj.schema_name
        super().handle(*args, **options)
