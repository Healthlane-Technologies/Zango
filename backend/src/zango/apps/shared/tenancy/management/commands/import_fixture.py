from django.core.management.commands.loaddata import Command as LoadDataCommand
from django.db import connection

from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.shared.tenancy.models import TenantModel


class Command(LoadDataCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--workspace",
            help="The workspace name to be used.",
        )

    def handle(self, *args, **options):
        tenant = options["workspace"]
        options["app_label"] = "dynamic_models"
        while True:
            try:
                tenant_obj = TenantModel.objects.get(name=tenant)
                connection.set_tenant(tenant_obj)
                break  # Exit the loop if a valid workspace is found
            except TenantModel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"The app name '{tenant}' provided as an argument is invalid. Please ensure that you have entered the correct app name and try again."
                    )
                )
                tenant = input("Please enter a valid workspace: ")
                options["workspace"] = tenant

        w = Workspace(tenant_obj, None, True)
        w.ready()
        super().handle(*args, **options)
