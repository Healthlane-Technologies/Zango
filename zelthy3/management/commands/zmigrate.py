from django_tenants.management.commands.migrate_schemas import MigrateSchemasCommand
from django.conf import settings
from zelthy3.backend.apps.shared.apps.models import AppModel

class Command(MigrateSchemasCommand):

    def add_arguments(self, parser):
         super().add_arguments(parser)
         parser.add_argument(
            "workspace",
            help="The workspace name to be used.",
            )

    def handle(self, *args, **options):
        settings.MIGRATION_MODULES = { f'dynamic_models': f"workspaces.{options['workspace']}.dmigrations" }
        options['schema_name'] = options['workspace']
        super().handle(*args, **options)