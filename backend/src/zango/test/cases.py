from django.core.management import call_command
from django.db import connection
from django_tenants.test.cases import TenantTestCase
from django.test import TransactionTestCase


class ZangoTestCase(TenantTestCase):
    @classmethod
    def tearDownClass(cls):
        connection.set_schema_to_public()
        cls.domain.delete()
        cls.tenant.delete(force_drop=False)
        cls.remove_allowed_test_domain()

class FastZangoTestCase(ZangoTestCase):
    """
    A faster variant of `ZangoTestCase`: the test schema and its migrations will only be created and ran once.

    WARNING: although this does produce significant improvements in speed it also means that these type of tests
             are not fully encapsulated and that some state will be shared between tests.

    See: https://github.com/tomturner/django-tenants/issues/100
    """
    pass


class ZangoAppBaseTestCase(TransactionTestCase):
    pass