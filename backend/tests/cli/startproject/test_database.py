import unittest
import subprocess
import os
import django
import sys
from importlib import import_module
import shutil

class TestDataBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.project_name = "zel3"
        cls.db_params = {
            'host': 'localhost',
            'port': '5432',
            'database': 'zelthy1',
            'user': 'postgres',
            'password': 'zelthy3pass'
        }
        process = subprocess.Popen(
            f'zelthy3 start-project {cls.project_name} --db_name={cls.db_params["database"]} --db_user={cls.db_params["user"]} --db_password={cls.db_params["password"]} --db_host="localhost" --db_port="5432"',
            shell=True  # Use shell=True if your command is a string with shell features (e.g., pipes)
        )
        exit_code = process.wait()
        sys.path.insert(0, "zel3")
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zel3.settings')
        django.setup()
    
    def test_tenant_created(self):
        from zelthy.apps.shared.tenancy.models import TenantModel
        tenant = TenantModel.objects.first()
        assert tenant.name == "public"
    
    def test_tenant_domain_created(self):
        from zelthy.apps.shared.tenancy.models import Domain
        domain = Domain.objects.first()
        assert domain.domain == "localhost"

    
    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(f"./{cls.project_name}")
    