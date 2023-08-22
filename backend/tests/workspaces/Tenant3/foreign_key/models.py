from django.db import models
from zelthy3.backend.apps.tenants.dynamic_models.fields import ZForeignKey, ZOneToOneField
from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase

class Foo(DynamicModelBase):
    a = models.CharField(max_length=10)
    d = models.DecimalField(max_digits=5, decimal_places=3)


def get_foo():
    return Foo.objects.get(id=1).pk


class Bar(DynamicModelBase):
    b = models.CharField(max_length=10)
    a = ZForeignKey(Foo, models.CASCADE, default=get_foo, related_name="bars")

class Test(DynamicModelBase):
    b = models.IntegerField()

class FUser(DynamicModelBase):
    name = models.CharField(max_length=200)


class Poll(DynamicModelBase):
    question = models.CharField(max_length=200)
    creator = ZForeignKey(FUser, models.CASCADE)


class Choice(DynamicModelBase):
    name = models.CharField(max_length=100)
    poll = ZForeignKey(Poll, models.CASCADE, related_name="poll_choice")
    related_poll = ZForeignKey(
        Poll, models.CASCADE, related_name="related_choice"
    )

class Domain(DynamicModelBase):
    name = models.CharField(max_length=50)


class Kingdom(DynamicModelBase):
    name = models.CharField(max_length=50)
    domain = ZForeignKey(Domain, models.CASCADE)


class Phylum(DynamicModelBase):
    name = models.CharField(max_length=50)
    kingdom = ZForeignKey(Kingdom, models.CASCADE)


class Klass(DynamicModelBase):
    name = models.CharField(max_length=50)
    phylum = ZForeignKey(Phylum, models.CASCADE)


class Order(DynamicModelBase):
    name = models.CharField(max_length=50)
    klass = ZForeignKey(Klass, models.CASCADE)


class Family(DynamicModelBase):
    name = models.CharField(max_length=50)
    order = ZForeignKey(Order, models.CASCADE)


class Genus(DynamicModelBase):
    name = models.CharField(max_length=50)
    family = ZForeignKey(Family, models.CASCADE)


class Species(DynamicModelBase):
    name = models.CharField(max_length=50)
    genus = ZForeignKey(Genus, models.CASCADE)


# and we'll invent a new thing so we have a model with two foreign keys


class HybridSpecies(DynamicModelBase):
    name = models.CharField(max_length=50)
    parent_1 = ZForeignKey(Species, models.CASCADE, related_name="child_1")
    parent_2 = ZForeignKey(Species, models.CASCADE, related_name="child_2")

class Topping(DynamicModelBase):
    name = models.CharField(max_length=30)