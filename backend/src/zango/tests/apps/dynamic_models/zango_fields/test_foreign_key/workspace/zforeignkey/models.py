from django.db import models
from zango.apps.dynamic_models.fields import ZForeignKey
from zango.apps.dynamic_models.models import DynamicModelBase

class Foo(DynamicModelBase):
    a = models.CharField(max_length=10)
    d = models.DecimalField(max_digits=5, decimal_places=3)

class Bar(DynamicModelBase):
    b = models.CharField(max_length=10)
    a = ZForeignKey(Foo, models.CASCADE, related_name="bars")

class FKUser(DynamicModelBase):
    name = models.CharField(max_length=200)

class Poll(DynamicModelBase):
    question = models.CharField(max_length=200)
    creator = ZForeignKey(FKUser, models.CASCADE)
