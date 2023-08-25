from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase


class SystemDetails(DynamicModelBase):
    details = models.TextField()