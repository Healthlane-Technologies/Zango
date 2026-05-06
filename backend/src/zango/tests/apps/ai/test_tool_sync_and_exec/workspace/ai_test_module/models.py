from django.db import models
from zango.apps.dynamic_models.models import DynamicModelBase


class Patient(DynamicModelBase):
    name = models.CharField(max_length=200)
    age = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} (age {self.age})"
