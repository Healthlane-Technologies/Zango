"""
Regression tests for proper working of ForeignKey(null=True).
"""

from django.db import models
from zelthy3.backend.apps.tenants.dynamic_models.fields import ZForeignKey, ZOneToOneField
from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase

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

    def __str__(self):
        return self.title


class Comment(DynamicModelBase):
    post = ZForeignKey(NPost, models.SET_NULL, null=True)
    comment_text = models.CharField(max_length=250)



# Ticket 15823


class Item(DynamicModelBase):
    title = models.CharField(max_length=100)


class PropertyValue(DynamicModelBase):
    label = models.CharField(max_length=100)


class Property(DynamicModelBase):
    item = ZForeignKey(Item, models.CASCADE, related_name="props")
    key = models.CharField(max_length=100)
    value = ZForeignKey(PropertyValue, models.SET_NULL, null=True)