from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField

class ForceInsertAuthor(DynamicModelBase):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ForceInsertBook(DynamicModelBase):
    title = models.CharField(max_length=200)
    author = ZForeignKey(ForceInsertAuthor, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title