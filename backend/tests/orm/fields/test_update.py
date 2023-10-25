import unittest
from decimal import Decimal
from workspaces.Tenant3.update.models import (
    A,
    B,
    D,
    DataPoint,
    RelatedPoint,
    UniqueNumber,
    UniqueNumberChild,
)
from zelthy3.backend.apps.tenants.dynamic_models.workspace.base import Workspace
from django_tenants.utils import get_tenant_model
from django.db import connection, models
from zelthy3.backend.apps.tenants.dynamic_models.fields import ZForeignKey
from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase
from django.core.exceptions import FieldError

class TestForeignKey(unittest.TestCase):

    def setUp(self) -> None:
        tenant_model = get_tenant_model()
        env = tenant_model.objects.get(name="Tenant3")
        connection.set_tenant(env)
        ws = Workspace(connection.tenant)
        ws.ready()
        with connection.cursor() as c:
            self.a1 = A.objects.create()
            self.a2 = A.objects.create()
            for x in range(20):
                B.objects.create(a=self.a1)
                D.objects.create(a=self.a1)
    
    def test_nonempty_update(self):
        """
        Update changes the right number of rows for a nonempty queryset
        """
        num_updated = self.a1.b_set.update(y=100)
        self.assertEqual(num_updated, 20)
        cnt = B.objects.filter(y=100).count()
        self.assertEqual(cnt, 20)

    def test_empty_update(self):
        """
        Update changes the right number of rows for an empty queryset
        """
        num_updated = self.a2.b_set.update(y=100)
        self.assertEqual(num_updated, 0)
        cnt = B.objects.filter(y=100).count()
        self.assertEqual(cnt, 0)

    def test_nonempty_update_with_inheritance(self):
        """
        Update changes the right number of rows for an empty queryset
        when the update affects only a base table
        """
        num_updated = self.a1.d_set.update(y=100)
        self.assertEqual(num_updated, 20)
        cnt = D.objects.filter(y=100).count()
        self.assertEqual(cnt, 20)

    def test_empty_update_with_inheritance(self):
        """
        Update changes the right number of rows for an empty queryset
        when the update affects only a base table
        """
        num_updated = self.a2.d_set.update(y=100)
        self.assertEqual(num_updated, 0)
        cnt = D.objects.filter(y=100).count()
        self.assertEqual(cnt, 0)

    def test_foreign_key_update_with_id(self):
        """
        Update works using <field>_id for foreign keys
        """
        num_updated = self.a1.d_set.update(a_id=self.a2)
        self.assertEqual(num_updated, 20)
        self.assertEqual(self.a2.d_set.count(), 20)