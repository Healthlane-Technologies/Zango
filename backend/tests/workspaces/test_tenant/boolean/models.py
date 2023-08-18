from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey

class NullBooleanModel(DynamicModelBase):
    nbfield = models.BooleanField(null=True, blank=True)


class BooleanModel(DynamicModelBase):
    bfield = models.BooleanField()

class FksToBooleans(DynamicModelBase):
    """Model with FKs to models with {Null,}BooleanField's, #15040"""

    bf = ZForeignKey(BooleanModel, models.CASCADE)
    nbf = ZForeignKey(NullBooleanModel, models.CASCADE)