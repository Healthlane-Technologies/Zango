import subprocess
from zelthy3.backend.apps.tenants.dynamic_models.workspace.base import Workspace
from django_tenants.utils import get_tenant_model, get_tenant_domain_model, get_public_schema_name
from django.test import TestCase
from django.core.management import call_command
from django.db import connection
from django.conf import settings


class BaseTestCase(TestCase):

    """
        Setup a test database, creates test workspace and also migrates models 
        into the data to support the tests. The test database is destroyed after
        tests are finished

    """

    @classmethod
    def setUpClass(cls):
        cls.sync_shared()
        # cls.add_allowed_test_domain()
        cls.tenant = get_tenant_model()(schema_name=cls.get_test_schema_name(), name="Tenant3", app_type="tenant")
        cls.setup_tenant(cls.tenant)
        cls.tenant.save()
        cls.zoperations()
        # Set up domain
        tenant_domain = cls.get_test_tenant_domain()
        cls.domain = get_tenant_domain_model()(tenant=cls.tenant, domain=tenant_domain)
        cls.setup_domain(cls.domain)
        cls.domain.save()
        connection.set_tenant(cls.tenant)

    
    @classmethod
    def sync_shared(cls):
        call_command('migrate_schemas',
                     schema_name=get_public_schema_name(),
                     interactive=False,
                     verbosity=0)
        
    @classmethod
    def zoperations(cls):
        settings.TEST_MIGRATION_RUNNING = True
        tenant = "Tenant3"
        command1 = f"python manage.py zmakemigrations {tenant} --test"
        subprocess.run(command1, shell=True)
        command2 = f"python manage.py zmigrate {tenant} --test"
        subprocess.run(command2, shell=True)