import os
from django.core.management import call_command
from django.test import override_settings
from zango.apps.dynamic_models.workspace.base import Workspace
from decimal import Decimal
from django_tenants.utils import schema_context
from django.core.exceptions import FieldError
from django.db import  models
from zango.apps.dynamic_models.fields import ZForeignKey
from zango.apps.dynamic_models.models import DynamicModelBase


from zango.test.cases import ZangoAppBaseTestCase

class ZangoForeignKeyTest(ZangoAppBaseTestCase):
    initialize_workspace = True
    
    @classmethod
    def get_test_module_path(self):
        return os.path.join(
            "apps/dynamic_models/zango_fields/test_foreign_key"
        )

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.syn_db()
        self.ws = Workspace(self.tenant, request=None, as_systemuser=True)
        self.ws.ready()
        self.zforeignkey = self.ws.plugin_source.load_plugin("zforeignkey.models")
        self.Foo = self.zforeignkey.Foo
        self.Bar = self.zforeignkey.Bar
        self.FKUser = self.zforeignkey.FKUser
        self.Poll = self.zforeignkey.Poll
        with schema_context(self.tenant.schema_name):
            john = self.FKUser.objects.create(name="John Doe")
            jim = self.FKUser.objects.create(name="Jim Bo")
            first_poll = self.Poll.objects.create(
                question="What's the first question?", creator=john
            )
            second_poll = self.Poll.objects.create(
                question="What's the second question?", creator=jim
            )

    @classmethod
    @override_settings(TEST_MIGRATION_RUNNING=True)
    def syn_db(self):
        call_command(
            'ws_migrate',
            'testapp'
        )

    def test_callable_default(self):
        """A lazy callable may be used for ForeignKey.default."""
        with schema_context(self.tenant.schema_name):
            a = self.Foo.objects.create(a="abc", d=Decimal("12.34"))
            b = self.Bar.objects.create(b="bcd", a=a)
            self.assertEqual(b.a, a)

    def test_related_name_converted_to_text(self):
        with schema_context(self.tenant.schema_name):
            rel_name = self.Bar._meta.get_field("a").remote_field.related_name
            self.assertIsInstance(rel_name, str)
    
    def test_non_local_to_field(self):
        class Parent(DynamicModelBase):
            key = models.IntegerField(unique=True)

        class Child(Parent):
            pass

        class Related(DynamicModelBase):
            child = ZForeignKey(Child, on_delete=models.CASCADE, to_field="key")

        
        with self.assertRaises(FieldError):
            Related._meta.get_field("child").related_fields
    
    def test_reverse_by_field(self):
        with schema_context(self.tenant.schema_name):
            u1 = self.FKUser.objects.get(poll__question__exact="What's the first question?")
            self.assertEqual(u1.name, "John Doe")

            u2 = self.FKUser.objects.get(poll__question__exact="What's the second question?")
            self.assertEqual(u2.name, "Jim Bo") 

    def test_reverse_field_name_disallowed(self):
        """
        If a related_name is given you can't use the field name instead
        """
        msg = (
            "Cannot resolve keyword 'choice' into field. Choices are: "
            "creator, creator_id, id, poll_choice, question, related_choice"
        )
        with schema_context(self.tenant.schema_name):
            with self.assertRaises(FieldError, msg=msg):
                self.Poll.objects.get(choice__name__exact="This is the answer")
