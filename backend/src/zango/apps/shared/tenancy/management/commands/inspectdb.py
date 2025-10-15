import inspect
import json
import os

from django.conf import settings
from django.core.management.commands.inspectdb import Command as DjangoInspectDbCommand
from django.db import connection

from zango.apps.dynamic_models.models import DynamicModelBase
from zango.apps.shared.tenancy.models import TenantModel
from zango.core.custom_pluginbase import get_plugin_source


class Command(DjangoInspectDbCommand):
    help = (
        "Introspects the database tables in the given database and outputs a Django model module, "
        "with support for tenant schemas and including existing dynamic models."
    )

    def add_arguments(self, parser):
        # Add all the original Django inspectdb arguments
        super().add_arguments(parser)

        # Add workspace/tenant arguments
        parser.add_argument(
            "--workspace",
            help="The workspace name to inspect tables for (connects to tenant schema).",
        )
        parser.add_argument(
            "--include-dynamic-models",
            action="store_true",
            help="Include existing dynamic models from the workspace in the output.",
        )
        parser.add_argument(
            "--package", help="Show models for a specific package within the workspace"
        )

    def handle(self, *args, **options):
        # Store options for access in other methods
        self.options = options

        # If workspace is specified, set up tenant connection
        if options.get("workspace"):
            workspace = options["workspace"]

            # Validate workspace exists
            try:
                tenant_obj = TenantModel.objects.get(name=workspace)
            except TenantModel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"The workspace '{workspace}' does not exist. Please ensure you have entered the correct workspace name."
                    )
                )
                return

            # Set up migration modules for dynamic_models if needed
            if options.get("package"):
                package = options["package"]
                package_migrations_path = (
                    f"workspaces/{workspace}/packages/{package}/migrations"
                )

                if os.path.exists(package_migrations_path):
                    settings.MIGRATION_MODULES = {
                        "dynamic_models": f"workspaces.{workspace}.packages.{package}.migrations"
                    }
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No migrations found for package '{package}' in workspace '{workspace}'. Path: {package_migrations_path}"
                        )
                    )
            else:
                workspace_migrations_path = f"workspaces/{workspace}/migrations"
                if os.path.exists(workspace_migrations_path):
                    settings.MIGRATION_MODULES = {
                        "dynamic_models": f"workspaces.{workspace}.migrations"
                    }

            # CRITICAL: Set tenant connection context so inspection happens in the correct schema
            connection.set_tenant(tenant_obj)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Connected to tenant schema: {tenant_obj.schema_name}"
                )
            )

        # If include-dynamic-models is specified, show existing dynamic models first
        if options.get("include_dynamic_models") and options.get("workspace"):
            self.show_existing_dynamic_models(
                options["workspace"], options.get("package")
            )

        # Generate the output by collecting all lines
        output_lines = []

        # Add custom header for dynamic models
        if options.get("workspace"):
            output_lines.extend(
                [
                    "# This is an auto-generated Django model module.",
                    "# Created by Zango's inspectdb command for dynamic models.",
                    "# You'll have to do the following manually to clean this up:",
                    "#   * Rearrange models' order",
                    "#   * Make sure each model has one field with primary_key=True",
                    "#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior",
                    "#   * Consider using ZForeignKey and ZOneToOneField for dynamic model relationships",
                    "#   * Review the app_label setting in Meta class",
                    "# Feel free to rename the models, but don't rename db_table values or field names.",
                    "",
                    "from django.db import models",
                    "from zango.apps.dynamic_models.models import DynamicModelBase",
                    "from zango.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField",
                    "",
                ]
            )

        # Get the inspection output from parent command
        # We need to override the parent's handle_inspection method behavior
        try:
            # Call parent command's handle method to get the generator
            parent_output = super().handle(*args, **options)
            if parent_output:
                # If parent returns a generator, collect the lines
                if hasattr(parent_output, "__iter__"):
                    for line in parent_output:
                        # Replace models.Model with DynamicModelBase for workspace introspection
                        if options.get("workspace") and line.strip().endswith(
                            "(models.Model):"
                        ):
                            line = line.replace(
                                "(models.Model):", "(DynamicModelBase):"
                            )
                        output_lines.append(line)
                else:
                    output_lines.append(str(parent_output))
            else:
                # If parent doesn't return anything, we need to generate the output ourselves
                for line in self.handle_inspection(options):
                    # Replace models.Model with DynamicModelBase for workspace introspection
                    if options.get("workspace") and line.strip().endswith(
                        "(models.Model):"
                    ):
                        line = line.replace("(models.Model):", "(DynamicModelBase):")
                    output_lines.append(line)

        except Exception as e:
            # Fallback to our own inspection if parent fails
            self.stdout.write(
                self.style.WARNING(f"Using fallback inspection method: {e}")
            )
            for line in self.handle_inspection(options):
                # Replace models.Model with DynamicModelBase for workspace introspection
                if options.get("workspace") and line.strip().endswith(
                    "(models.Model):"
                ):
                    line = line.replace("(models.Model):", "(DynamicModelBase):")
                output_lines.append(line)

        # Output all lines
        for line in output_lines:
            self.stdout.write(line)

    def show_existing_dynamic_models(self, workspace, package=None):
        """Show existing dynamic models from the workspace."""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("EXISTING DYNAMIC MODELS"))
        self.stdout.write("=" * 80)
        self.stdout.write(
            "# The following models already exist as dynamic models in this workspace.\n"
            "# You may want to compare these with the database-introspected models below.\n"
        )

        try:
            dynamic_models = self.get_workspace_dynamic_models(workspace, package)

            if not dynamic_models:
                self.stdout.write("# No dynamic models found in the workspace.")
            else:
                self.stdout.write(f"# Found {len(dynamic_models)} dynamic model(s):\n")

                for model_class in dynamic_models:
                    self.stdout.write(f"\n# Model: {model_class.__name__}")
                    self.stdout.write(f"# Module: {model_class.__module__}")

                    # Get field information
                    fields_info = []
                    for field in model_class._meta.get_fields():
                        if hasattr(field, "name"):
                            field_info = f"{field.name} = {field.__class__.__name__}"
                            if hasattr(field, "max_length") and field.max_length:
                                field_info += f"(max_length={field.max_length})"
                            fields_info.append(field_info)

                    if fields_info:
                        self.stdout.write(f"# Fields: {', '.join(fields_info)}")

                    self.stdout.write(f"# Database table: {model_class._meta.db_table}")

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"# Warning: Could not load dynamic models from workspace: {e}"
                )
            )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("DATABASE INTROSPECTED MODELS"))
        self.stdout.write("=" * 80)

    def get_workspace_dynamic_models(self, workspace, package=None):
        """
        Get all dynamic models for the specified workspace.
        Similar to the graph_models implementation but focused on model discovery.
        """
        dynamic_models = []

        # Determine workspace path
        workspace_path = f"{settings.BASE_DIR}/workspaces/{workspace}/"

        if not os.path.exists(workspace_path):
            return dynamic_models

        # Get plugin source for dynamic loading
        plugin_source = get_plugin_source(workspace)

        if package:
            # Load models from specific package
            package_models_path = f"{workspace_path}packages/{package}"
            if os.path.exists(f"{package_models_path}/models.py"):
                try:
                    module = plugin_source.load_plugin(f"packages.{package}.models")
                    dynamic_models.extend(
                        self._extract_dynamic_models_from_module(module)
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Warning: Could not load package models from {package}: {e}"
                        )
                    )
        else:
            # Load models from workspace modules
            settings_file = f"{workspace_path}settings.json"

            if os.path.exists(settings_file):
                try:
                    with open(settings_file) as f:
                        ws_settings = json.load(f)

                    # Process workspace modules
                    for module_config in ws_settings.get("modules", []):
                        module_path = module_config["path"]
                        models_file = f"{workspace_path}{module_path}/models.py"

                        if os.path.exists(models_file):
                            try:
                                module = plugin_source.load_plugin(
                                    f"{module_path}.models"
                                )
                                dynamic_models.extend(
                                    self._extract_dynamic_models_from_module(module)
                                )
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"Warning: Could not load module {module_path}.models: {e}"
                                    )
                                )

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Warning: Could not read workspace settings: {e}"
                        )
                    )

        return dynamic_models

    def _extract_dynamic_models_from_module(self, module):
        """Extract DynamicModelBase subclasses from a loaded module."""
        models = []

        for _, obj in inspect.getmembers(module):
            if (
                isinstance(obj, type)
                and issubclass(obj, DynamicModelBase)
                and obj != DynamicModelBase
            ):
                models.append(obj)

        return models
