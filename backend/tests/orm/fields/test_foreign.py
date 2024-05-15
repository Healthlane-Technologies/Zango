import unittest
from decimal import Decimal
from workspaces.Tenant3.foreign_key.models import Foo, Bar, Test, FUser, Poll, Choice
from zango.backend.apps.tenants.dynamic_models.workspace.base import Workspace
from django_tenants.utils import get_tenant_model
from django.db import connection, models
from zango.backend.apps.tenants.dynamic_models.fields import ZForeignKey
from zango.backend.apps.tenants.dynamic_models.models import DynamicModelBase
from django.core.exceptions import FieldError


class TestForeignKey(unittest.TestCase):
    def setUp(self) -> None:
        tenant_model = get_tenant_model()
        env = tenant_model.objects.get(name="Tenant3")
        connection.set_tenant(env)
        ws = Workspace(connection.tenant)
        ws.ready()
        with connection.cursor() as c:
            john = FUser.objects.create(name="John Doe")
            jim = FUser.objects.create(name="Jim Bo")
            first_poll = Poll.objects.create(
                question="What's the first question?", creator=john
            )
            second_poll = Poll.objects.create(
                question="What's the second question?", creator=jim
            )
            Choice.objects.create(
                poll=first_poll, related_poll=second_poll, name="This is the answer."
            )

    def test_callable_default(self):
        """A lazy callable may be used for ForeignKey.default."""
        with connection.cursor() as c:
            a = Foo.objects.create(a="abc", d=Decimal("12.34"))
            b = Bar.objects.create(b="bcd", a=a)
            self.assertEqual(b.a, a)

    def test_related_name_converted_to_text(self):
        rel_name = Bar._meta.get_field("a").remote_field.related_name
        self.assertIsInstance(rel_name, str)

    def test_to_python(self):
        class Foo(DynamicModelBase):
            pass

        class Bar(DynamicModelBase):
            fk = ZForeignKey(Foo, models.CASCADE)

        self.assertEqual(Bar._meta.get_field("fk").to_python("1"), 1)

    def test_fk_to_fk_get_col_output_field(self):
        class Foo(DynamicModelBase):
            pass

        class Bar(DynamicModelBase):
            foo = ZForeignKey(Foo, models.CASCADE, primary_key=True)

        class Baz(DynamicModelBase):
            bar = ZForeignKey(Bar, models.CASCADE, primary_key=True)

        col = Baz._meta.get_field("bar").get_col("alias")
        self.assertIs(col.output_field, Foo._meta.pk)

    def test_recursive_fks_get_col(self):
        class Foo(DynamicModelBase):
            bar = ZForeignKey("Bar", models.CASCADE, primary_key=True)

        class Bar(DynamicModelBase):
            foo = ZForeignKey(Foo, models.CASCADE, primary_key=True)

        with self.assertRaises(ValueError):
            Foo._meta.get_field("bar").get_col("alias")

    def test_non_local_to_field(self):
        class Parent(DynamicModelBase):
            key = models.IntegerField(unique=True)

        class Child(Parent):
            pass

        class Related(DynamicModelBase):
            child = ZForeignKey(Child, on_delete=models.CASCADE, to_field="key")

        with self.assertRaises(FieldError):
            Related._meta.get_field("child").related_fields

    def test_invalid_to_parameter(self):
        msg = (
            "ForeignKey(1) is invalid. First parameter to ForeignKey must be "
            "either a model, a model name, or the string 'self'"
        )
        with self.assertRaises(TypeError):

            class MyModel(DynamicModelBase):
                child = ZForeignKey(1, models.CASCADE)

    def test_reverse_by_field(self):
        with connection.cursor() as c:
            u1 = FUser.objects.get(poll__question__exact="What's the first question?")
            self.assertEqual(u1.name, "John Doe")

            u2 = FUser.objects.get(poll__question__exact="What's the second question?")
            self.assertEqual(u2.name, "Jim Bo")

    def test_reverse_by_related_name(self):
        with connection.cursor() as c:
            p1 = Poll.objects.get(poll_choice__name__exact="This is the answer.")
            self.assertEqual(p1.question, "What's the first question?")

            p2 = Poll.objects.get(related_choice__name__exact="This is the answer.")
            self.assertEqual(p2.question, "What's the second question?")

    def test_reverse_field_name_disallowed(self):
        """
        If a related_name is given you can't use the field name instead
        """
        msg = (
            "Cannot resolve keyword 'choice' into field. Choices are: "
            "creator, creator_id, id, poll_choice, question, related_choice"
        )
        with self.assertRaises(FieldError):
            Poll.objects.get(choice__name__exact="This is the answer")
