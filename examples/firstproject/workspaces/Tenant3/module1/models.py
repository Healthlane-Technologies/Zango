# Create your models here.

from django.db import models
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField, ZManyToManyField
from zelthy.apps.dynamic_models.models import DynamicModelBase


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

from ..landingPage.models import LandingPageModel
class Property(DynamicModelBase):
    item = ZForeignKey(Item, models.CASCADE, related_name="props")
    key = models.CharField(max_length=100)
    value = ZForeignKey(PropertyValue, models.SET_NULL, null=True)
    pg = ZForeignKey(LandingPageModel, null=True, on_delete=models.CASCADE)

    


class Tag(DynamicModelBase):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(
        "self",
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="children",
    )


class StateModel(DynamicModelBase):
    name = models.CharField(max_length=20)

class City(DynamicModelBase):
    name = models.CharField(max_length=20)
    state = ZForeignKey(StateModel, null=True, on_delete=models.CASCADE)