from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField

class Foo(DynamicModelBase):
    a = models.CharField(max_length=10)
    d = models.DecimalField(max_digits=5, decimal_places=3)



class Bar(DynamicModelBase):
    b = models.CharField(max_length=10)
    a = ZForeignKey(Foo, models.CASCADE, related_name="bars")

class PrimaryKeyCharModel(DynamicModelBase):
    string = models.CharField(max_length=10, primary_key=True)

class FkToChar(DynamicModelBase):
    """Model with FK to a model with a CharField primary key, #19299"""

    out = ZForeignKey(PrimaryKeyCharModel, models.CASCADE)

class FPublisher(DynamicModelBase):
    name = models.CharField(max_length=100)
    website = models.URLField()

class FAuthor(DynamicModelBase):
    name = models.CharField(max_length=100)
    bio = models.TextField()

class FBook(DynamicModelBase):
    title = models.CharField(max_length=200)
    author = ZForeignKey(FAuthor, on_delete=models.CASCADE)
    publisher = ZForeignKey(FPublisher, on_delete=models.SET_NULL, null=True)
    publication_date = models.DateField()
