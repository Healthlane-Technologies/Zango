import inspect

from django.core.management.commands.dumpdata import Command as DumpDataCommand
from django.db import connection

from zango.apps.dynamic_models.models import DynamicModelBase
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.shared.tenancy.models import TenantModel


class Command(DumpDataCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--workspace",
            help="The workspace name to be used.",
        )
        parser.add_argument(
            "--release_version",
            help="Fixture for the given version",
            required=False,
            type=str,
        )
        fixtrue_group = parser.add_mutually_exclusive_group(required=True)
        fixtrue_group.add_argument(
            "--package",
            action="store_true",
            help="Package fixtures",
        )
        fixtrue_group.add_argument(
            "--app",
            action="store_true",
            help="App fixtures",
        )
        fixtrue_group.add_argument(
            "--framework",
            action="store_true",
            help="Framework fixtures",
        )

    def get_dynamic_config_models(self, w):
        models_list = []

        # app_config = apps.get_app_config("dynamic_models")
        models = w.get_models()

        for m in models:
            if (self.app_fixtures and not w.is_package_model(m)) or (
                self.package_fixtures and w.is_package_model(m)
            ):
                split = m.split(".")[2:]
                module = w.plugin_source.load_plugin(".".join(split))

                for name, obj in inspect.getmembers(module):
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, DynamicModelBase)
                        and obj != DynamicModelBase
                    ):
                        dynamic_meta = getattr(obj, "DynamicModelMeta", None)
                        if dynamic_meta:
                            is_config_model = getattr(
                                dynamic_meta, "is_config_model", False
                            )

                            if is_config_model:
                                model_name = obj.__name__
                                models_list.append(f"dynamic_models.{model_name}")

        return models_list

    def handle(self, *app_labels, **options):
        tenant = options["workspace"]
        self.package_fixtures = options["package"]
        self.app_fixtures = options["app"]
        self.framework_fixtures = options["framework"]

        options["use_natural_foreign_keys"] = True
        options["use_natural_primary_keys"] = True

        if not options.get("indent"):
            options["indent"] = 4

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

        if self.package_fixtures or self.app_fixtures:
            w = Workspace(tenant_obj, None, True)
            w.ready()
            models_list = self.get_dynamic_config_models(w)
            if len(models_list) < 1:
                self.stdout.write("No fixtures found.")
                return
        elif self.framework_fixtures:
            models_list = ["appauth.UserRoleModel"]

        # Saving fixture in release folder under particular version
        import os

        from django.conf import settings

        workspace_dir = os.path.join(settings.BASE_DIR, "workspaces", tenant)

        release_dir = os.path.join(workspace_dir, "release")
        if not os.path.exists(release_dir):
            os.makedirs(release_dir)

        version = options["release_version"]
        if version:
            version_dir = os.path.join(release_dir, version, "fixtures")
            if not os.path.exists(version_dir):
                os.makedirs(version_dir)

            fixture_file_name = ""
            if self.app_fixtures:
                fixture_file_name = "app_fixtures.json"
            elif self.package_fixtures:
                fixture_file_name = "package_fixtures.json"
            elif self.framework_fixtures:
                fixture_file_name = "framework_fixtures.json"

            options["output"] = os.path.join(version_dir, fixture_file_name)

        super().handle(*models_list, **options)
