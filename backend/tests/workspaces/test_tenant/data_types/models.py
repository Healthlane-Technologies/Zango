from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase

class Donut(DynamicModelBase):
    name = models.CharField(max_length=100)
    is_frosted = models.BooleanField(default=False)
    has_sprinkles = models.BooleanField(null=True)
    baked_date = models.DateField(null=True)
    baked_time = models.TimeField(null=True)
    consumed_at = models.DateTimeField(null=True)
    review = models.TextField()


class RumBaba(DynamicModelBase):
    baked_date = models.DateField(auto_now_add=True)
    baked_timestamp = models.DateTimeField(auto_now_add=True)