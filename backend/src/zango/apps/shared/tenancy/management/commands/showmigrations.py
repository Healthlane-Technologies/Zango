import os

from django.conf import settings
from django.core.management.commands.showmigrations import (
    Command as DjangoShowMigrationsCommand,
)
from django.db import connection
from django.db.migrations.loader import MigrationLoader

from zango.apps.shared.tenancy.models import TenantModel


class Command(DjangoShowMigrationsCommand):
    help = "Shows all available migrations for the current project, including dynamic_models migrations for specified workspace."

    def add_arguments(self, parser):
        # Add all the original Django showmigrations arguments
        super().add_arguments(parser)

        # Add workspace argument for dynamic models
        parser.add_argument(
            "--workspace",
            help="The workspace name to include dynamic_models migrations for.",
        )
        parser.add_argument(
            "--package",
            help="Show migrations for a specific package within the workspace",
        )

    def handle(self, *args, **options):
        # If workspace is specified, set up dynamic_models migration path
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

            # Set up migration modules for dynamic_models
            if options.get("package"):
                package = options["package"]
                package_migrations_path = (
                    f"workspaces/{workspace}/packages/{package}/migrations"
                )

                if os.path.exists(package_migrations_path):
                    settings.MIGRATION_MODULES = {
                        "dynamic_models": f"workspaces.{workspace}.packages.{package}.migrations"
                    }
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Including dynamic_models migrations for workspace '{workspace}', package '{package}'"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No migrations found for package '{package}' in workspace '{workspace}'. Path: {package_migrations_path}"
                        )
                    )
                    return
            else:
                workspace_migrations_path = f"workspaces/{workspace}/migrations"

                if os.path.exists(workspace_migrations_path):
                    settings.MIGRATION_MODULES = {
                        "dynamic_models": f"workspaces.{workspace}.migrations"
                    }
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Including dynamic_models migrations for workspace '{workspace}'"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No migrations found for workspace '{workspace}'. Path: {workspace_migrations_path}"
                        )
                    )
                    # Don't return here - still show other migrations

            # CRITICAL: Set tenant connection context so migration status is checked in the correct schema
            connection.set_tenant(tenant_obj)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Connected to tenant schema: {tenant_obj.schema_name}"
                )
            )

        # Call the parent Django command to handle the actual migration display
        super().handle(*args, **options)

        # If workspace was specified, provide additional information
        if options.get("workspace"):
            self.show_dynamic_models_info(options["workspace"], options.get("package"))

    def show_dynamic_models_info(self, workspace, package=None):
        """Show additional information about dynamic_models migrations for the workspace."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Dynamic Models Migration Information"))
        self.stdout.write("=" * 60)

        if package:
            migration_path = f"workspaces/{workspace}/packages/{package}/migrations"
            self.stdout.write(f"Workspace: {workspace} (Package: {package})")
        else:
            migration_path = f"workspaces/{workspace}/migrations"
            self.stdout.write(f"Workspace: {workspace}")

        self.stdout.write(f"Migration Path: {migration_path}")

        # Check if migration directory exists and list migration files
        if os.path.exists(migration_path):
            migration_files = [
                f
                for f in os.listdir(migration_path)
                if f.endswith(".py") and f != "__init__.py"
            ]
            if migration_files:
                self.stdout.write(f"\nFound {len(migration_files)} migration file(s):")
                for migration_file in sorted(migration_files):
                    self.stdout.write(f"  - {migration_file}")
            else:
                self.stdout.write("\nNo migration files found in this directory.")
        else:
            self.stdout.write(f"\nMigration directory does not exist: {migration_path}")

        # Show current MIGRATION_MODULES setting for dynamic_models
        if (
            hasattr(settings, "MIGRATION_MODULES")
            and "dynamic_models" in settings.MIGRATION_MODULES
        ):
            self.stdout.write(
                f"\nCurrent dynamic_models migration module: {settings.MIGRATION_MODULES['dynamic_models']}"
            )

        self.stdout.write("=" * 60)

    def show_list(self, connection, app_names=None):
        """
        Show migrations in list format, with enhanced display for dynamic_models.
        This overrides the parent method to provide better output for dynamic models.
        """
        # Call parent method for standard behavior
        super().show_list(connection, app_names)

        # If dynamic_models is in the output and we have workspace info, add context
        loader = MigrationLoader(connection, ignore_no_migrations=True)

        # Check if dynamic_models app has migrations
        if "dynamic_models" in loader.migrated_apps:
            # Show additional context if available
            if (
                hasattr(settings, "MIGRATION_MODULES")
                and "dynamic_models" in settings.MIGRATION_MODULES
            ):
                module_path = settings.MIGRATION_MODULES["dynamic_models"]
                self.stdout.write(
                    f"\nNote: dynamic_models migrations are loaded from: {module_path}"
                )
