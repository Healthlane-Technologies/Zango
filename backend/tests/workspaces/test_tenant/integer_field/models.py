from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class IntegerModel(DynamicModelBase):
    value = models.IntegerField()


class BigIntegerModel(DynamicModelBase):
    value = models.BigIntegerField()
    null_value = models.BigIntegerField(null=True, blank=True)


class PositiveBigIntegerModel(DynamicModelBase):
    value = models.PositiveBigIntegerField()


class PositiveSmallIntegerModel(DynamicModelBase):
    value = models.PositiveSmallIntegerField()


class PositiveIntegerModel(DynamicModelBase):
    value = models.PositiveIntegerField()

class SmallIntegerModel(DynamicModelBase):
    value = models.SmallIntegerField()


