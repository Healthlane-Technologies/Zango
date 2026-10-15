from django.db import models
from zango.apps.dynamic_models.models import DynamicModelBase


class ZasSequence(DynamicModelBase):
    """One counter per auto-sequence field (key = "<entity>.<field>[.<period>]")."""

    key = models.CharField(max_length=200, unique=True)
    value = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.key}={self.value}"
