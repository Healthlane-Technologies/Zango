from django.test import TestCase
from django.core.management import call_command
from django_tenants.utils import get_tenant_model, get_tenant_domain_model, get_public_schema_name
from django.db import connection

class TenantTestCase(TestCase):
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
        print("here")
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
    def tearDownClass(cls):
        connection.set_schema_to_public()
        cls.domain.delete()
        cls.tenant.delete(force_drop=True)
        cls.remove_allowed_test_domain()

    @classmethod
    def get_verbosity(cls):
        return 0

    # @classmethod
    # def add_allowed_test_domain(cls):
    #     tenant_domain = cls.get_test_tenant_domain()

    #     # ALLOWED_HOSTS is a special setting of Django setup_test_environment so we can't modify it with helpers
    #     if tenant_domain not in settings.ALLOWED_HOSTS:
    #         settings.ALLOWED_HOSTS += [tenant_domain]

    # @classmethod
    # def remove_allowed_test_domain(cls):
    #     tenant_domain = cls.get_test_tenant_domain()

    #     if tenant_domain in settings.ALLOWED_HOSTS:
    #         settings.ALLOWED_HOSTS.remove(tenant_domain)

    @classmethod
    def sync_shared(cls):
        call_command('migrate_schemas',
                     schema_name=get_public_schema_name(),
                     interactive=False,
                     verbosity=0)
    
    @classmethod
    def zoperations(cls):
        print("Z op")
        call_command('zmakemigrations',
                     interactive=False,
                     verbosity=0)
        call_command('zmigrate',
                     interactive=False,
                     verbosity=0)
        pass

    @classmethod
    def get_test_tenant_domain(cls):
        return 'localhost'

    @classmethod
    def get_test_schema_name(cls):
        return 'Tenant3'
    

