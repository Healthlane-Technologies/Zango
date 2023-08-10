from django.db import models
from zelthy3.backend.apps.tenants.dynamic_models.fields import ZForeignKey, ZOneToOneField
from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase

class DataPoint(DynamicModelBase):
    name = models.CharField(max_length=20)
    value = models.CharField(max_length=20)
    another_value = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)


class RelatedPoint(DynamicModelBase):
    name = models.CharField(max_length=20)
    data = ZForeignKey(DataPoint, models.CASCADE)


class A(DynamicModelBase):
    x = models.IntegerField(default=10)


class B(DynamicModelBase):
    a = ZForeignKey(A, models.CASCADE)
    y = models.IntegerField(default=10)


class C(DynamicModelBase):
    y = models.IntegerField(default=10)


# class D(C):
#     a = ZForeignKey(A, models.CASCADE)


# class Foo(DynamicModelBase):
#     target = models.CharField(max_length=10, unique=True)


# class Bar(DynamicModelBase):
#     foo = ZForeignKey(Foo, models.CASCADE, to_field="target")
#     m2m_foo = models.ManyToManyField(Foo, related_name="m2m_foo")
#     x = models.IntegerField(default=0)


class UniqueNumber(DynamicModelBase):
    number = models.IntegerField(unique=True)


class UniqueNumberChild(UniqueNumber):
    pass