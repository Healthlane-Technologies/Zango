from collections import OrderedDict

from django.apps import apps
from django.core.management.base import CommandError
from django.core.management.commands.shell import Command as ShellCommand
from django.db import connection

from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.shared.tenancy.models import TenantModel


class Command(ShellCommand):
    help = "Enhanced shell with auto-imported models and utilities for multi-tenant workspace"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--workspace",
            help="The workspace name to be used.",
            required=True,
        )
        parser.add_argument(
            "--print-sql",
            action="store_true",
            help="Print SQL queries as they execute",
        )
        parser.add_argument(
            "--dont-load",
            action="append",
            dest="dont_load",
            default=[],
            help="Ignore autoloading of django model classes from the given app",
        )

    def get_models_for_import(self, dont_load_list):
        """Get all models that should be auto-imported"""
        imported_objects = OrderedDict()

        # Get all installed apps
        for app_config in apps.get_app_configs():
            if app_config.label in dont_load_list:
                continue

            try:
                # Get all models from the app
                for model in app_config.get_models():
                    model_name = model.__name__

                    # Handle name collisions by prefixing with app name
                    if model_name in imported_objects:
                        # Rename the existing one
                        existing_model = imported_objects[model_name]
                        existing_app = existing_model._meta.app_label
                        imported_objects[f"{existing_app}_{model_name}"] = (
                            existing_model
                        )
                        del imported_objects[model_name]

                        # Add the new one with app prefix
                        imported_objects[f"{app_config.label}_{model_name}"] = model
                    else:
                        imported_objects[model_name] = model

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Could not load models from {app_config.label}: {e}"
                    )
                )

        return imported_objects

    def get_workspace_models(self, workspace_obj):
        """Get dynamic models from the workspace"""
        imported_objects = OrderedDict()

        try:
            w = Workspace(workspace_obj, None, True)
            w.ready()

            # Get dynamic models
            models = w.get_models()
            for model_path in models:
                try:
                    # Load the model dynamically
                    split = model_path.split(".")[2:]
                    module = w.plugin_source.load_plugin(".".join(split))

                    # Import models from the module
                    for name in dir(module):
                        obj = getattr(module, name)
                        if (
                            hasattr(obj, "_meta")
                            and hasattr(obj._meta, "app_label")
                            and name not in imported_objects
                        ):
                            imported_objects[name] = obj

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Could not load model from {model_path}: {e}"
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Could not load workspace models: {e}")
            )

        return imported_objects

    def setup_sql_printing(self):
        """Setup SQL query printing if requested"""
        from django.conf import settings

        if hasattr(settings, "DEBUG") and settings.DEBUG:
            # Enable SQL logging
            import logging

            logger = logging.getLogger("django.db.backends")
            logger.setLevel(logging.DEBUG)
            logger.addHandler(logging.StreamHandler())

    def handle(self, *args, **options):
        workspace = options["workspace"]
        print_sql = options.get("print_sql", False)
        dont_load = options.get("dont_load", [])

        # Validate and set workspace
        try:
            tenant_obj = TenantModel.objects.get(name=workspace)
            connection.set_tenant(tenant_obj)
        except TenantModel.DoesNotExist:
            raise CommandError(
                f"Workspace '{workspace}' does not exist. "
                "Please provide a valid workspace name."
            )

        # Setup SQL printing if requested
        if print_sql:
            self.setup_sql_printing()

        # Get models to import
        self.stdout.write("Loading models...")
        imported_objects = self.get_models_for_import(dont_load)

        # Get workspace-specific dynamic models
        workspace_models = self.get_workspace_models(tenant_obj)
        imported_objects.update(workspace_models)

        # Add common imports
        imported_objects.update(
            {
                "apps": apps,
                "connection": connection,
                "TenantModel": TenantModel,
                "Workspace": Workspace,
            }
        )

        # Store imported objects for the shell
        options["imported_objects"] = imported_objects

        # Print what was imported
        self.stdout.write(self.style.SUCCESS(f"Workspace: {workspace}"))
        self.stdout.write(
            self.style.SUCCESS(f"Auto-imported {len(imported_objects)} objects:")
        )

        # Group imports by type for better display
        models = []
        utils = []

        for name, obj in imported_objects.items():
            if hasattr(obj, "_meta"):
                models.append(name)
            else:
                utils.append(name)

        if models:
            self.stdout.write(f"Models: {', '.join(sorted(models))}")
        if utils:
            self.stdout.write(f"Utils: {', '.join(sorted(utils))}")

        # Call the parent shell command
        super().handle(*args, **options)

    def python(self, options):
        """Enhanced python shell with auto-imports"""
        import code

        # Prepare the namespace with imported objects
        imported_objects = options.get("imported_objects", {})

        # Try to use IPython if available
        try:
            from IPython import start_ipython
            from IPython.terminal.ipapp import load_default_config

            config = load_default_config()
            config.TerminalInteractiveShell.banner1 = (
                "Enhanced Django shell with auto-imported models\n"
                "Type 'help()' for more information.\n"
            )

            # Start IPython with pre-loaded namespace
            start_ipython(argv=[], user_ns=imported_objects, config=config)
            return

        except ImportError:
            pass

        # Fallback to standard Python shell
        imported_objects.update(
            {
                "help": "Type help() for more information.",
            }
        )

        console = code.InteractiveConsole(imported_objects)
        console.interact(
            banner="Enhanced Django shell with auto-imported models\n"
            "Type 'help()' for more information.\n"
        )
