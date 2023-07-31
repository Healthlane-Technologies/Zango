from django_tenants.management.commands.migrate_schemas import MigrateSchemasCommand
from django.conf import settings

class Command(MigrateSchemasCommand):
    

    def handle(self, *args, **options):
        #TODO: temp migration folder will be created which will have migrations of packages also added
        settings.MIGRATION_MODULES = { 'dynamic_models': "zelthy_apps.Tenant3.dmigrations" }
        super().handle(*args, **options)
