from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class Tournament(DynamicModelBase):
    name = models.CharField(max_length=30)


class Organiser(DynamicModelBase):
    name = models.CharField(max_length=30)


class Pool(DynamicModelBase):
    name = models.CharField(max_length=30)
    tournament = ZForeignKey(Tournament, models.CASCADE)
    organiser = ZForeignKey(Organiser, models.CASCADE)


class PoolStyle(DynamicModelBase):
    name = models.CharField(max_length=30)
    pool = ZOneToOneField(Pool, models.CASCADE)
    another_pool = ZOneToOneField(
        Pool, models.CASCADE, null=True, related_name="another_style"
    )