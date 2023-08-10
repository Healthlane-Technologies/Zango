import unittest
from decimal import Decimal
from tests.workspaces.Tenant3.foreign_key.models import Foo, Bar
from zelthy3.backend.apps.tenants.dynamic_models.workspace.base import Workspace
from django_tenants.utils import get_tenant_model
from django.db import connection

class TestForeignKey(unittest.TestCase):

    def setUp(self) -> None:
        tenant_model = get_tenant_model()
        env = tenant_model.objects.get(name="Tenant3")
        connection.set_tenant(env)
        ws = Workspace(connection.tenant)

    def test_callable_default(self):
        """A lazy callable may be used for ForeignKey.default."""
        tenant_model = get_tenant_model()
        env = tenant_model.objects.get(name="Tenant3")
        connection.set_tenant(env)
        with connection.cursor() as c:
            a = Foo.objects.create(id=1, a="abc", d=Decimal("12.34"))
            b = Bar.objects.create(b="bcd")
            self.assertEqual(b.a, a)