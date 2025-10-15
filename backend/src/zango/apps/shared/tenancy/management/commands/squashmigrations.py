import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connection, connections
from django.db.migrations import Migration
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.optimizer import MigrationOptimizer
from django.db.migrations.writer import MigrationWriter

from zango.apps.shared.tenancy.models import TenantModel


class Command(BaseCommand):
    help = (
        "Squashes a range of migrations for dynamic_models in a specified workspace. "
        "Similar to Django's squashmigrations but works with Zango's multi-tenant architecture."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "workspace",
            help="The workspace name containing the migrations to squash.",
        )
        parser.add_argument(
            "start_migration_name",
            nargs="?",
            help=(
                "The migration to start squashing from. If not provided, squashes from the first migration."
            ),
        )
        parser.add_argument(
            "migration_name",
            help="The migration to squash until (inclusive).",
        )
        parser.add_argument(
            "--no-optimize",
            action="store_true",
            help="Do not try to optimize the squashed operations.",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do not prompt the user for input of any kind.",
        )
        parser.add_argument(
            "--squashed-name",
            help="Set the name of the new squashed migration.",
        )
        parser.add_argument(
            "--no-header",
            action="store_true",
            help="Do not add a header comment to the new squashed migration.",
        )
        parser.add_argument(
            "--package",
            help="Squash migrations for a specific package within the workspace.",
        )

    def handle(self, *args, **options):
        workspace = options["workspace"]
        start_migration_name = options.get("start_migration_name")
        migration_name = options["migration_name"]
        no_optimize = options.get("no_optimize", False)
        squashed_name = options.get("squashed_name")
        no_header = options.get("no_header", False)
        package = options.get("package")

        # Validate workspace exists
        try:
            tenant_obj = TenantModel.objects.get(name=workspace)
        except TenantModel.DoesNotExist:
            raise CommandError(f"Workspace '{workspace}' does not exist.")

        # Set up migration path and connect to tenant
        if package:
            package_migrations_path = (
                f"workspaces/{workspace}/packages/{package}/migrations"
            )
            if not os.path.exists(package_migrations_path):
                raise CommandError(
                    f"Package '{package}' migrations not found at {package_migrations_path}"
                )

            settings.MIGRATION_MODULES = {
                "dynamic_models": f"workspaces.{workspace}.packages.{package}.migrations"
            }
            self.stdout.write(f"Using package migrations: {package}")
        else:
            workspace_migrations_path = f"workspaces/{workspace}/migrations"
            if not os.path.exists(workspace_migrations_path):
                raise CommandError(
                    f"Workspace migrations not found at {workspace_migrations_path}"
                )

            settings.MIGRATION_MODULES = {
                "dynamic_models": f"workspaces.{workspace}.migrations"
            }

        # Connect to tenant schema for migration status tracking
        connection.set_tenant(tenant_obj)
        self.stdout.write(
            self.style.SUCCESS(f"Connected to tenant schema: {tenant_obj.schema_name}")
        )

        # Load migrations using Django's MigrationLoader
        loader = MigrationLoader(connections[DEFAULT_DB_ALIAS])

        # Validate that dynamic_models app has migrations
        if "dynamic_models" not in loader.migrated_apps:
            raise CommandError(
                "App 'dynamic_models' does not have migrations in this workspace. "
                "Ensure the workspace has migration files."
            )

        # Get migration objects
        try:
            migration = loader.get_migration("dynamic_models", migration_name)
        except KeyError:
            raise CommandError(
                f"Cannot find migration '{migration_name}' in dynamic_models for workspace '{workspace}'"
            )

        start_migration = None
        if start_migration_name:
            try:
                start_migration = loader.get_migration(
                    "dynamic_models", start_migration_name
                )
            except KeyError:
                raise CommandError(
                    f"Cannot find migration '{start_migration_name}' in dynamic_models for workspace '{workspace}'"
                )

        # Get the migration plan from start to end
        if start_migration:
            # Find migrations between start and end (inclusive)
            plan = loader.graph.forwards_plan((migration.app_label, migration.name))
            start_index = None
            end_index = None

            for i, (app_label, migration_name_item) in enumerate(plan):
                if app_label == "dynamic_models":
                    if migration_name_item == start_migration.name:
                        start_index = i
                    if migration_name_item == migration.name:
                        end_index = i
                        break

            if start_index is None:
                raise CommandError(
                    f"Start migration '{start_migration.name}' not found in plan"
                )
            if end_index is None:
                raise CommandError(
                    f"End migration '{migration.name}' not found in plan"
                )
            if start_index >= end_index:
                raise CommandError("Start migration must come before end migration")

            # Get the subset of plan from start to end
            migrations_to_squash = []
            for app_label, migration_name_item in plan[start_index : end_index + 1]:
                if app_label == "dynamic_models":
                    migrations_to_squash.append(
                        loader.get_migration(app_label, migration_name_item)
                    )
        else:
            # Squash from beginning to specified migration
            plan = loader.graph.forwards_plan((migration.app_label, migration.name))
            migrations_to_squash = []
            for app_label, migration_name_item in plan:
                if app_label == "dynamic_models":
                    migrations_to_squash.append(
                        loader.get_migration(app_label, migration_name_item)
                    )

        if not migrations_to_squash:
            raise CommandError("No migrations found to squash")

        # Check for already squashed migrations
        for smigration in migrations_to_squash:
            if smigration.replaces:
                raise CommandError(
                    f"Migration '{smigration.name}' is already a squashed migration. "
                    "You cannot squash squashed migrations."
                )

        self.stdout.write(f"Will squash {len(migrations_to_squash)} migration(s):")
        for smigration in migrations_to_squash:
            self.stdout.write(f"  - {smigration.name}")

        # Collect operations and dependencies
        operations = []
        dependencies = set()
        replaces = []

        for i, smigration in enumerate(migrations_to_squash):
            operations.extend(smigration.operations)
            replaces.append((smigration.app_label, smigration.name))

            # For the first migration, include all its dependencies
            # For subsequent migrations, only include external dependencies
            for dependency in smigration.dependencies:
                if dependency[0] != smigration.app_label or i == 0:
                    dependencies.add(dependency)

        # Optimize operations if requested
        if not no_optimize:
            self.stdout.write("Optimizing operations...")
            optimizer = MigrationOptimizer()
            operations = optimizer.optimize(operations, "dynamic_models")
            self.stdout.write(
                f"Optimized from {len([op for migration in migrations_to_squash for op in migration.operations])} operations to {len(operations)} operations."
            )

        # Generate new migration name
        if start_migration:
            new_name = f"{start_migration.name}_squashed_{migration.name}"
        else:
            if squashed_name:
                new_name = f"0001_{squashed_name}"
            else:
                new_name = f"0001_squashed_{migration.name}"

        # Create new migration class
        new_migration = type(
            "Migration",
            (Migration,),
            {
                "dependencies": list(dependencies),
                "operations": operations,
                "replaces": replaces,
            },
        )

        # Determine output path
        if package:
            migration_dir = f"{settings.BASE_DIR}/workspaces/{workspace}/packages/{package}/migrations"
        else:
            migration_dir = f"{settings.BASE_DIR}/workspaces/{workspace}/migrations"

        # Write the new migration file
        writer = MigrationWriter(new_migration, include_header=not no_header)
        migration_file_path = os.path.join(migration_dir, f"{new_name}.py")

        # Custom header for Zango dynamic models
        if not no_header:
            from datetime import datetime

            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

            header_lines = [
                f"# Generated by Zango's squashmigrations command on {current_date}",
                f"# Squashes migrations for workspace: {workspace}",
            ]
            if package:
                header_lines.append(f"# Package: {package}")
            header_lines.extend(
                [
                    f"# Replaces: {', '.join([name for app, name in replaces])}",
                    "",
                ]
            )

            # Get the migration content and add custom header
            migration_content = writer.as_string()

            # Find where to insert custom header (after the initial comment but before imports)
            lines = migration_content.split("\n")
            insert_index = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("from django.db import migrations"):
                    insert_index = i
                    break

            # Insert custom header
            lines = lines[:insert_index] + header_lines + lines[insert_index:]
            migration_content = "\n".join(lines)
        else:
            migration_content = writer.as_string()

        # Write the file
        with open(migration_file_path, "w", encoding="utf-8") as fh:
            fh.write(migration_content)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created squashed migration {new_name} in {migration_file_path}"
            )
        )

        # Show next steps
        self.stdout.write(
            "\nNext steps:\n"
            "  1. Review the squashed migration for correctness\n"
            "  2. Test the squashed migration in a development environment\n"
            f"  3. Run: python manage.py ws_migrate {workspace} --fake-initial (if this is the initial migration)\n"
            f"  4. Run: python manage.py ws_migrate {workspace} (to apply the squashed migration)\n"
            "  5. Remove the old migration files that were squashed\n"
        )

        # Show warning about manual steps
        if replaces:
            self.stdout.write(
                self.style.WARNING(
                    "\nIMPORTANT: This squashed migration replaces the following migrations:\n"
                    + "\n".join([f"  - {name}" for app, name in replaces])
                    + "\n\nYou should delete these migration files after verifying the squashed migration works correctly."
                )
            )

    def get_workspace_migrations(self, workspace, package=None):
        """
        Get list of migration files for the workspace.
        This is a utility method for future enhancements.
        """
        if package:
            migration_dir = f"{settings.BASE_DIR}/workspaces/{workspace}/packages/{package}/migrations"
        else:
            migration_dir = f"{settings.BASE_DIR}/workspaces/{workspace}/migrations"

        if not os.path.exists(migration_dir):
            return []

        migration_files = []
        for filename in os.listdir(migration_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                migration_files.append(filename[:-3])  # Remove .py extension

        return sorted(migration_files)

    def validate_migration_sequence(self, migrations_to_squash):
        """
        Validate that migrations can be squashed together.
        This is a utility method for future enhancements.
        """
        # Check for circular dependencies
        for i, migration in enumerate(migrations_to_squash):
            for dependency in migration.dependencies:
                # Check if any later migration in our sequence is a dependency
                for j, later_migration in enumerate(
                    migrations_to_squash[i + 1 :], i + 1
                ):
                    if (
                        dependency[0] == later_migration.app_label
                        and dependency[1] == later_migration.name
                    ):
                        return (
                            False,
                            f"Circular dependency detected: {migration.name} depends on {later_migration.name}",
                        )

        return True, "Sequence is valid"
