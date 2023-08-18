from decimal import Decimal
from workspaces.test_tenant.foreign_key.models import Foo, Bar, FkToChar, PrimaryKeyCharModel
from django.core.exceptions import FieldError
from django.test import skipIfDBFeature
from django.db import models
from django.core import checks

from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey
from zelthy.test_utils.base import BaseTestCase

class TestForeignKey(BaseTestCase):


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