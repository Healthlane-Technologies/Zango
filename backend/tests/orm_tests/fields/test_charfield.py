from django.core.exceptions import ValidationError
from django.db import models
from django.test import SimpleTestCase, TestCase

from workspaces.test_tenant.charfield.models import CPost
from zelthy.test_utils.base import BaseTestCase

class TestCharField(BaseTestCase):
    def test_max_length_passed_to_formfield(self):
        """
        CharField passes its max_length attribute to form fields created using
        the formfield() method.
        """
        cf1 = models.CharField()
        cf2 = models.CharField(max_length=1234)
        self.assertIsNone(cf1.formfield().max_length)
        self.assertEqual(1234, cf2.formfield().max_length)

    def test_lookup_integer_in_charfield(self):
        self.assertEqual(CPost.objects.filter(title=9).count(), 0)

    def test_emoji(self):
        p = CPost.objects.create(title="Smile 😀", body="Whatever.")
        p.refresh_from_db()
        self.assertEqual(p.title, "Smile 😀")

    def test_assignment_from_choice_enum(self):
        class Event(models.TextChoices):
            C = "Carnival!"
            F = "Festival!"

        p1 = CPost.objects.create(title=Event.C, body=Event.F)
        p1.refresh_from_db()
        self.assertEqual(p1.title, "Carnival!")
        self.assertEqual(p1.body, "Festival!")
        self.assertEqual(p1.title, Event.C)
        self.assertEqual(p1.body, Event.F)
        p2 = CPost.objects.get(title="Carnival!")
        self.assertEqual(p1, p2)
        self.assertEqual(p2.title, Event.C)


class TestMethods(BaseTestCase):
    def test_deconstruct(self):
        field = models.CharField()
        *_, kwargs = field.deconstruct()
        self.assertEqual(kwargs, {})
        field = models.CharField(db_collation="utf8_esperanto_ci")
        *_, kwargs = field.deconstruct()
        self.assertEqual(kwargs, {"db_collation": "utf8_esperanto_ci"})


class ValidationTests(BaseTestCase):
    class Choices(models.TextChoices):
        C = "c", "C"

    def test_charfield_raises_error_on_empty_string(self):
        f = models.CharField()
        msg = "This field cannot be blank."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("", None)

    def test_charfield_cleans_empty_string_when_blank_true(self):
        f = models.CharField(blank=True)
        self.assertEqual("", f.clean("", None))

    def test_charfield_with_choices_cleans_valid_choice(self):
        f = models.CharField(max_length=1, choices=[("a", "A"), ("b", "B")])
        self.assertEqual("a", f.clean("a", None))

    def test_charfield_with_choices_raises_error_on_invalid_choice(self):
        f = models.CharField(choices=[("a", "A"), ("b", "B")])
        msg = "Value 'not a' is not a valid choice."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("not a", None)

    def test_charfield_raises_error_on_empty_input(self):
        f = models.CharField(null=False)
        msg = "This field cannot be null."
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean(None, None)