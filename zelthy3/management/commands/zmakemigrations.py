
import os
from django.conf import settings
from django.core.management.base import no_translations
from django.db import connection

from django.core.management.commands.makemigrations import Command as MakeMigrationsCommand
from zelthy3.backend.apps.shared.apps.models import AppModel
from zelthy3.backend.apps.tenants.dynamic_models.workspace.base import Workspace
from importlib import import_module
from zelthy3.backend.apps.tenants.dynamic_models.views import tenant_sys_path
import sys


class Command(MakeMigrationsCommand):
    """
        Custom makemigration to generate migration files for dynamic_models. The workspace name
        is a mandatory argument with this command. The workspace is initialized and the models 
        are loaded after which the migrations are generated. The migrations for the workspace and
        all the plugins are generated through this command. 

        Known issues:
            - Migrations generated for relational tables where the referred table is not migrated 
              already causes an issue in the migration. In such cases, the migration file has to
              be manually edited to move the relational field out of the CreateModel block to a
              ModifyField block.             
    
    """

    help = "Creates new migration(s) for a workspace."

    def add_arguments(self, parser):
         super().add_arguments(parser)
         parser.add_argument(
            "workspace",
            help="The workspace name to be used.",
        )
                  
    @no_translations
    def handle(self, *app_labels, **options):        
        settings.MIGRATION_MODULES = { f'dynamic_models': f"workspaces.{options['workspace']}.dmigrations" }
        wks_obj = AppModel.objects.get(name=options['workspace'])        
        with tenant_sys_path(options['workspace']):
            w = Workspace(wks_obj, None,  True)
            w.load_models()
            # print(sys.path)
            super().handle('dynamic_models', **options)        



