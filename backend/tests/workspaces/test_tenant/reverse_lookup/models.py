from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class ReverseAuthor(DynamicModelBase):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ReverseBook(DynamicModelBase):
    title = models.CharField(max_length=200)
    author = ZForeignKey(ReverseAuthor, on_delete=models.CASCADE, related_name="reverse_books")

    def __str__(self):
        return self.title