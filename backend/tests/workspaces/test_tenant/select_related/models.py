from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class SelectAuthor(DynamicModelBase):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class SelectBook(DynamicModelBase):
    title = models.CharField(max_length=200)
    author = ZForeignKey(SelectAuthor, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class SelectUserProfile(DynamicModelBase):
    author = ZOneToOneField(SelectAuthor, on_delete=models.CASCADE)
    bio = models.TextField()

    def __str__(self):
        return self.author.name