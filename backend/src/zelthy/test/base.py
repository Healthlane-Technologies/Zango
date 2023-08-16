import subprocess
from zelthy.apps.dynamic_models.workspace.base import Workspace
from django_tenants.utils import get_tenant_model, get_tenant_domain_model, get_public_schema_name
from django.test import TestCase
from django.core.management import call_command
from django.db import connection
from django.conf import settings


class BaseTestCase(TestCase):

    tenant = None
    domain = None

    @classmethod
    def setup_tenant(cls, tenant):
        """
        Add any additional setting to the tenant before it get saved. This is required if you have
        required fields.
        :param tenant:
        :return:
        """
        pass

    @classmethod
    def setup_domain(cls, domain):
        """
        Add any additional setting to the domain before it get saved. This is required if you have
        required fields.
        :param domain:
        :return:
        """
        pass

    @classmethod
    def setUpClass(cls):
        cls.sync_shared()
        # cls.add_allowed_test_domain()
        tenant_model = get_tenant_model()
        try:
            cls.tenant = tenant_model.objects.get(name="Tenant3")
            cls.zoperations()
        except Exception:
            cls.tenant = get_tenant_model()(schema_name=cls.get_test_schema_name(), name="Tenant3", description="desc")
            cls.setup_tenant(cls.tenant)
            cls.tenant.save()
            cls.zoperations()
            # Set up domain
            tenant_domain = cls.get_test_tenant_domain()
            cls.domain = get_tenant_domain_model()(tenant=cls.tenant, domain=tenant_domain)
            cls.setup_domain(cls.domain)
            cls.domain.save()
        connection.set_tenant(cls.tenant)
        cls.setUpTestData()

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def get_verbosity(cls):
        return 0

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
        command1 = f"python manage.py ws_makemigrate {tenant} --test"
        subprocess.run(command1, shell=True)  
        command2 = f"python manage.py ws_migrate {tenant} --test"
        subprocess.run(command2, shell=True)
        

    @classmethod
    def get_test_tenant_domain(cls):
        return 'localhost'

    @classmethod
    def get_test_schema_name(cls):
        return 'Tenant3'
    
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()