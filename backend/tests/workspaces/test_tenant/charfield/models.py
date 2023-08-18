from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey


class CPost(DynamicModelBase):
    title = models.CharField(max_length=100)
    body = models.TextField()