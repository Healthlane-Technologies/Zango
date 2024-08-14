from zango.apps.dynamic_models.models import DynamicModelBase
from django.db import models


class TestModel(DynamicModelBase):
    name = models.CharField(max_length=100)
    description = models.TextField()
