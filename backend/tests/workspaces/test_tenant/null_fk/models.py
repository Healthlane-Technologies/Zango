"""
Regression tests for proper working of ForeignKey(null=True).
"""

from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class SystemDetails(DynamicModelBase):
    details = models.TextField()


class SystemInfo(DynamicModelBase):
    system_details = ZForeignKey(SystemDetails, models.CASCADE)
    system_name = models.CharField(max_length=32)


class Forum(DynamicModelBase):
    system_info = ZForeignKey(SystemInfo, models.CASCADE)
    forum_name = models.CharField(max_length=32)


class NPost(DynamicModelBase):
    forum = ZForeignKey(Forum, models.SET_NULL, null=True)
    title = models.CharField(max_length=32)

    # def __str__(self):
    #     return self.title


class Comment(DynamicModelBase):
    post = ZForeignKey(NPost, models.SET_NULL, null=True)
    comment_text = models.CharField(max_length=250)

    # class Meta:
    #     ordering = ("comment_text",)


# Ticket 15823


class Item(DynamicModelBase):
    title = models.CharField(max_length=100)


class PropertyValue(DynamicModelBase):
    label = models.CharField(max_length=100)


class Property(DynamicModelBase):
    item = ZForeignKey(Item, models.CASCADE, related_name="props")
    key = models.CharField(max_length=100)
    value = ZForeignKey(PropertyValue, models.SET_NULL, null=True)

class Zywoo(DynamicModelBase):
    a = models.IntegerField(unique=True)

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