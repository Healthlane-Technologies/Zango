"""
One-to-one relationships

To define a one-to-one relationship, use ``OneToOneField()``.

In this example, a ``Place`` optionally can be a ``Restaurant``.
"""
from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class Place(DynamicModelBase):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=80)

    def __str__(self):
        return "%s the place" % self.name


class Restaurant(DynamicModelBase):
    place = ZOneToOneField(Place, models.CASCADE, primary_key=True)
    serves_hot_dogs = models.BooleanField(default=False)
    serves_pizza = models.BooleanField(default=False)

    def __str__(self):
        return "%s the restaurant" % self.place.name


class OBar(DynamicModelBase):
    place = ZOneToOneField(Place, models.CASCADE)
    serves_cocktails = models.BooleanField(default=True)


class UndergroundBar(DynamicModelBase):
    place = ZOneToOneField(Place, models.SET_NULL, null=True)
    serves_cocktails = models.BooleanField(default=True)


class Waiter(DynamicModelBase):
    restaurant = ZForeignKey(Restaurant, models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return "%s the waiter at %s" % (self.name, self.restaurant)


# class Favorites(DynamicModelBase):
#     name = models.CharField(max_length=50)
#     restaurants = models.ManyToManyField(Restaurant)


class ManualPrimaryKey(DynamicModelBase):
    primary_key = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=50)


class RelatedModel(DynamicModelBase):
    link = ZOneToOneField(ManualPrimaryKey, models.CASCADE)
    name = models.CharField(max_length=50)


class MultiModel(DynamicModelBase):
    link1 = ZOneToOneField(Place, models.CASCADE)
    link2 = ZOneToOneField(ManualPrimaryKey, models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return "Multimodel %s" % self.name


class Target(DynamicModelBase):
    name = models.CharField(max_length=50, unique=True)


class Pointer(DynamicModelBase):
    other = ZOneToOneField(Target, models.CASCADE, primary_key=True)


class Pointer2(DynamicModelBase):
    other = ZOneToOneField(Target, models.CASCADE, related_name="second_pointer")


class HiddenPointer(DynamicModelBase):
    target = ZOneToOneField(Target, models.CASCADE, related_name="hidden+")


class ToFieldPointer(DynamicModelBase):
    target = ZOneToOneField(
        Target, models.CASCADE, to_field="name", primary_key=True
    )


# Test related objects visibility.
class SchoolManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_public=True)


class School(DynamicModelBase):
    is_public = models.BooleanField(default=False)
    objects = SchoolManager()


class DirectorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_temp=False)


class Director(DynamicModelBase):
    is_temp = models.BooleanField(default=False)
    school = ZOneToOneField(School, models.CASCADE)
    objects = DirectorManager()

class OneUsr(DynamicModelBase):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)

class OneProfile(DynamicModelBase):
    user = ZOneToOneField(OneUsr, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)