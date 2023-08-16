from django_tenants.management.commands.migrate_schemas import MigrateSchemasCommand
from django.conf import settings
from django.db import connection
from zelthy.apps.shared.tenancy.models import TenantModel

class Command(MigrateSchemasCommand):

    def add_arguments(self, parser):
         super().add_arguments(parser)
         parser.add_argument(
            "workspace",
            help="The workspace name to be used.",
            )
         parser.add_argument(
             "--test",
             action='store_true',
             help="Run the migration for test database"
         )

    def handle(self, *args, **options):
        print("Inside ws_migrate...")
        is_test_mode = options['test']
        if is_test_mode:
            connection.settings_dict['NAME'] = "test_"+ connection.settings_dict['NAME']
        print("here")
        # get sorted plugins and migrate plugins' migrations then the main workspace migration
        settings.MIGRATION_MODULES = { f'dynamic_models': f"workspaces.{options['workspace']}.dmigrations" }
        # print(options['workspace'])
        options['schema_name'] = "tenant3" #options['workspace']
        
        super().handle(*args, **options)
        # settings.MIGRATION_MODULES = { f'dynamic_models': f"workspaces.{options['workspace']}.plugins.crud.migrations" }
        # print(settings.MIGRATION_MODULES)
        # super().handle(*args, **options)