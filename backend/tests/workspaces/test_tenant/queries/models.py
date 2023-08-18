from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class Article(DynamicModelBase):
    name = models.CharField(max_length=20)
    created = models.DateTimeField()

    def __str__(self):
        return self.name

class CustomPk(DynamicModelBase):
    name = models.CharField(max_length=10, primary_key=True)
    extra = models.CharField(max_length=10)

class Detail(models.Model):
    data = models.CharField(max_length=10)

class Food(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name
class JSONFieldNullable(models.Model):
    json_field = models.JSONField(blank=True, null=True)

class MemberManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("details")

class Member(models.Model):
    name = models.CharField(max_length=10)
    details = models.OneToOneField(Detail, models.CASCADE, primary_key=True)

    objects = MemberManager()

class Order(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=12, null=True, default="")

class NamedCategory(DynamicModelBase):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(
        "self",
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="children",
    )
    category = models.ForeignKey(
        NamedCategory, models.SET_NULL, null=True, default=None
    )

class Note(models.Model):
    note = models.CharField(max_length=100)
    misc = models.CharField(max_length=25)
    tag = models.ForeignKey(Tag, models.SET_NULL, blank=True, null=True)
    negate = models.BooleanField(default=True)
