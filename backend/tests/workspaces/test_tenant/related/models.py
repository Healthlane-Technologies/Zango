from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class RelatedAuthor(DynamicModelBase):
    name = models.CharField(max_length=100)
    bio = models.TextField()

class RelatedPublisher(DynamicModelBase):
    name = models.CharField(max_length=100)
    website = models.URLField()

class RelatedBook(DynamicModelBase):
    title = models.CharField(max_length=200)
    author = ZOneToOneField(RelatedAuthor, on_delete=models.CASCADE)
    publisher = ZForeignKey(RelatedPublisher, on_delete=models.CASCADE)
    publication_date = models.DateField()

class RelatedChapter(DynamicModelBase):
    book = ZForeignKey(RelatedBook, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()