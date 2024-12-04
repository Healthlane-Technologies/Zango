import os

from django_tenants.management.commands.migrate_schemas import MigrateSchemasCommand

from django.conf import settings

from zango.apps.shared.tenancy.models import TenantModel


class Command(MigrateSchemasCommand):
    # TODO: Handle package migration

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "workspace",
            help="The workspace name to be used.",
        )
        parser.add_argument("--package", help="Run the migrations for the package")

    def handle(self, *args, **options):
        tenant = options["workspace"]
        while True:
            try:
                tenant_obj = TenantModel.objects.get(name=tenant)
                break  # Exit the loop if a valid workspace is found
            except TenantModel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"The app name '{tenant}' provided as an argument is invalid. Please ensure that you have entered the correct app name and try again."
                    )
                )
                tenant = input("Please enter a valid workspace: ")
                options["workspace"] = tenant

        if options["package"] is None:
            settings.MIGRATION_MODULES = {
                "dynamic_models": f"workspaces.{ options['workspace']}.migrations"
            }
        else:
            if os.path.exists(
                f"workspaces/{options['workspace']}/packages/{options['package']}/migrations"
            ):
                settings.MIGRATION_MODULES = {
                    "dynamic_models": f"workspaces.{ options['workspace']}.packages.{options['package']}.migrations"
                }
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        f"\n\nThe package '{options['package']}' does not have any migrations. Please ensure that you have entered the correct package name and try again."
                    )
                )
                exit(0)
        options["schema_name"] = tenant_obj.schema_name
        super().handle(*args, **options)
