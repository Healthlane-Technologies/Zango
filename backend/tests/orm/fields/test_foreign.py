from decimal import Decimal
from workspaces.Tenant3.foreign_key.models import Foo, Bar, FkToChar, PrimaryKeyCharModel
from django.core.exceptions import FieldError
from django.test import skipIfDBFeature
from django.db import models
from django.core import checks

from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey
from zelthy.test.base import BaseTestCase

class TestForeignKey(BaseTestCase):

    def test_callable_default(self):
        """A lazy callable may be used for ForeignKey.default."""
        a = Foo.objects.create(id=1, a="abc", d=Decimal("12.34"))
        b = Bar.objects.create(b="bcd")
        self.assertEqual(b.a, a)

    @skipIfDBFeature("interprets_empty_strings_as_nulls")
    def test_empty_string_fk(self):
        """
        Empty strings foreign key values don't get converted to None (#19299).
        """
        char_model_empty = PrimaryKeyCharModel.objects.create(string="")
        fk_model_empty = FkToChar.objects.create(out=char_model_empty)
        fk_model_empty = FkToChar.objects.select_related("out").get(
            id=fk_model_empty.pk
        )
        self.assertEqual(fk_model_empty.out, char_model_empty)

    def test_warning_when_unique_true_on_fk(self):
        class Foo(DynamicModelBase):
            pass

        class FKUniqueTrue(DynamicModelBase):
            fk_field = ZForeignKey(Foo, models.CASCADE, unique=True)

        model = FKUniqueTrue()
        expected_warnings = [
            checks.Warning(
                "Setting unique=True on a ForeignKey has the same effect as using a "
                "OneToOneField.",
                hint=(
                    "ForeignKey(unique=True) is usually better served by a "
                    "OneToOneField."
                ),
                obj=FKUniqueTrue.fk_field.field,
                id="fields.W342",
            )
        ]
        warnings = model.check()
        self.assertEqual(warnings, expected_warnings)

    def test_related_name_converted_to_text(self):
        rel_name = Bar._meta.get_field("a").remote_field.related_name
        self.assertIsInstance(rel_name, str)


    def test_to_python(self):
        class Foo(DynamicModelBase):
            pass

        class FBar(DynamicModelBase):
            fk = ZForeignKey(Foo, models.CASCADE)

        self.assertEqual(FBar._meta.get_field("fk").to_python("1"), 1)

    def test_fk_to_fk_get_col_output_field(self):
        class Foo(DynamicModelBase):
            pass

        class Bar(DynamicModelBase):
            foo = ZForeignKey(Foo, models.CASCADE, primary_key=True)

        class Baz(DynamicModelBase):
            bar = ZForeignKey(Bar, models.CASCADE, primary_key=True)

        col = Baz._meta.get_field("bar").get_col("alias")
        self.assertIs(col.output_field, Foo._meta.pk)

    # def test_recursive_fks_get_col(self):
    #     class Foo(DynamicModelBase):
    #         bar = ZForeignKey("Bar", models.CASCADE, primary_key=True)

    #     class Bar(DynamicModelBase):
    #         foo = ZForeignKey(Foo, models.CASCADE, primary_key=True)

    #     with self.assertRaisesMessage(ValueError, "Cannot resolve output_field"):
    #         Foo._meta.get_field("bar").get_col("alias")


    # def test_non_local_to_field(self):
    #     class Parent(DynamicModelBase):
    #         key = models.IntegerField(unique=True)

    #     class Child(Parent):
    #         pass

    #     class Related(DynamicModelBase):
    #         child = ZForeignKey(Child, on_delete=models.CASCADE, to_field="key")

    #     msg = (
    #         "'model_fields.Related.child' refers to field 'key' which is not "
    #         "local to model 'model_fields.Child'."
    #     )
    #     with self.assertRaisesMessage(FieldError, msg):
    #         Related._meta.get_field("child").related_fields

    def test_invalid_to_parameter(self):
        msg = (
            "ForeignKey(1) is invalid. First parameter to ForeignKey must be "
            "either a model, a model name, or the string 'self'"
        )
        with self.assertRaisesMessage(TypeError, msg):

            class MyModel(DynamicModelBase):
                child = ZForeignKey(1, models.CASCADE)

    def test_manager_class_getitem(self):
        self.assertIs(ZForeignKey["Foo"], ZForeignKey)