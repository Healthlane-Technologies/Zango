from django.core.management.base import BaseCommand, CommandError
import os
import shutil
from django.conf import settings
from django.db import connection
from zelthy.apps.shared.tenancy.models import TenantModel
from zelthy.apps.dynamic_models.workspace.base import Workspace


class Command(BaseCommand):
    help = "Collects assets from the specified app, including packages and copies into \
            the main django asset folder"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "workspace",
            help="The workspace name to be used.",
        )

    def copy_source_to_destination(self, source_dir, destination_dir):
        if os.path.exists(destination_dir):
            shutil.rmtree(destination_dir)
        os.makedirs(destination_dir)
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(destination_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, False, None)
            else:
                shutil.copy2(s, d)
        return

    def handle(self, *args, **options):
        wks_obj = TenantModel.objects.get(name=options["workspace"])
        connection.set_tenant(wks_obj)
        ws = Workspace(wks_obj, None, True)
        destination_path = settings.STATICFILES_DIRS[1] + "/workspaces/%s" % (
            options["workspace"]
        )
        if not os.path.exists(f"workspaces/{options['workspace']}/static"):
            os.makedirs(f"workspaces/{options['workspace']}/static")
        if not os.path.exists("./assets"):
            os.makedirs("assets")
        ws_static_path = ws.path + "static"
        self.copy_source_to_destination(ws_static_path, destination_path)

        for package in ws.packages:
            package_name = package["name"]
            package_source_dir = ws.path + "packages/%s/static" % (package_name)
            if os.path.exists(package_source_dir):
                package_destination_dir = (
                    destination_path + "/packages/%s" % package_name
                )
                self.copy_source_to_destination(
                    package_source_dir, package_destination_dir
                )
        return
