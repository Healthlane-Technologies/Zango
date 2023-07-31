
import sys
import warnings
from django.conf import settings
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError, no_translations

from django.db.migrations.loader import MigrationLoader
from django.db.migrations.autodetector import MigrationAutodetector
from django.db import connection
from django.db.migrations import Migration
from django.db.migrations.state import ProjectState
from django.db import DEFAULT_DB_ALIAS, OperationalError, connections, router

from django.db.migrations.questioner import (
    InteractiveMigrationQuestioner,
    MigrationQuestioner,
    NonInteractiveMigrationQuestioner,
)


        
from django.core.management.commands.makemigrations import Command as MakeMigrationsCommand

class Command(MakeMigrationsCommand):

    help = "Creates new migration(s) for tenants."

    def add_arguments(self, parser):
         super().add_arguments(parser)
         parser.add_argument(
            "--tenant_name",
            action="store_true",
            help="Just show what migrations would be made; don't actually write them.",
        )
         
    @no_translations
    def handle(self, *app_labels, **options):
        settings.MIGRATION_MODULES = { 'dynamic_models': "zelthy_apps.Tenant3.dmigrations" }
        # load models of all modules of the tenant; packages are ignored as they will come with prepackaged migrations
        model_path = settings.BASE_DIR / "zelthy_apps/Tenant3/module1/models.py"
        with model_path.open() as f:
            model_py = f.read()
        exec(model_py, globals(), globals())
        super().handle(*app_labels, **options)        



