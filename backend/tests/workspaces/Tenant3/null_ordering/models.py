from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class NullPoll(DynamicModelBase):
    question = models.CharField(max_length=200)


class NullChoice(DynamicModelBase):
    poll = ZForeignKey(NullPoll, models.CASCADE)
    choice = models.CharField(max_length=200)


# A set of models with an inner one pointing to two outer ones.


class NullOuterA(DynamicModelBase):
    pass


class NullOuterB(DynamicModelBase):
    data = models.CharField(max_length=10)


class NullInner(DynamicModelBase):
    first = ZForeignKey(NullOuterA, models.CASCADE)
    # second would clash with the __second lookup.
    third = ZForeignKey(NullOuterB, models.SET_NULL, null=True)