import io
from zango.test.cases import ZangoAppBaseTestCase
from django.db import connection
from zango.apps.dynamic_models.workspace.base import Workspace
from django.core.management import call_command
from django.test import override_settings

class ZangoMigrationsTest(ZangoAppBaseTestCase):
    initialize_workspace = True 
    parent = "migrations"
    module = "test_ws_makemigration"

    @classmethod
    def sync_workspace(self):
        with connection.cursor() as c:
            ws = Workspace(self.tenant, request=None, as_systemuser=True)
            ws.ready()
        
    @override_settings(TEST_MIGRATION_RUNNING=True)
    def test_ws_makemigration(self):
        self.sync_workspace()
        out = io.StringIO()
        call_command(
            'ws_makemigration',
            'testapp',
            stdout=out
        )
        self.assertIn("0001_initial", out.getvalue())
