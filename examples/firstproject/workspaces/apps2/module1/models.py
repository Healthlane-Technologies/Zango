# Create your models here.

from django.db import models
from django.contrib.postgres.fields import ArrayField
from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase
from zelthy3.backend.apps.tenants.dynamic_models.fields import ZForeignKey, ZManyToManyField, ZOneToOneField


class Address(DynamicModelBase):
    use = models.CharField(max_length=50)
    type = models.CharField(max_length=50, null=True)
    text = models.CharField(max_length=255, null=True)
    


 