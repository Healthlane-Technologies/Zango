from django.db import models
from zelthy3.backend.apps.tenants.dynamic_models.fields import ZForeignKey, ZOneToOneField
from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase

class Foo(DynamicModelBase):
    a = models.CharField(max_length=10)
    d = models.DecimalField(max_digits=5, decimal_places=3)


def get_foo():
    return Foo.objects.get(id=1).pk


class Bar(DynamicModelBase):
    b = models.CharField(max_length=10)
    a = ZForeignKey(Foo, models.CASCADE, default=get_foo, related_name="bars")