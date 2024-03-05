"""
One-to-one relationships

To define a one-to-one relationship, use ``OneToOneField()``.

In this example, a ``Place`` optionally can be a ``Restaurant``.
"""
from django.db import models
from zelthy3.backend.apps.tenants.dynamic_models.fields import ZForeignKey, ZOneToOneField
from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase


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


class OneBar(DynamicModelBase):
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


class Favorites(DynamicModelBase):
    name = models.CharField(max_length=50)


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









class OUser(DynamicModelBase):
    username = models.CharField(max_length=100)
    email = models.EmailField()


class UserProfile(DynamicModelBase):
    user = ZOneToOneField(OUser, models.CASCADE)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)


class UserStatResult(DynamicModelBase):
    results = models.CharField(max_length=50)


class UserStat(DynamicModelBase):
    user = ZOneToOneField(OUser, models.CASCADE, primary_key=True)
    posts = models.IntegerField()
    results = ZForeignKey(UserStatResult, models.CASCADE)


class StatDetails(DynamicModelBase):
    base_stats = ZOneToOneField(UserStat, models.CASCADE)
    comments = models.IntegerField()


# class AdvancedUserStat(UserStat):
#     karma = models.IntegerField()


class Image(DynamicModelBase):
    name = models.CharField(max_length=100)


class Product(DynamicModelBase):
    name = models.CharField(max_length=100)
    image = ZOneToOneField(Image, models.SET_NULL, null=True)


class Parent1(DynamicModelBase):
    name1 = models.CharField(max_length=50)


class Parent2(DynamicModelBase):
    # Avoid having two "id" fields in the Child1 subclass
    id2 = models.AutoField(primary_key=True)
    name2 = models.CharField(max_length=50)


# class Child1(Parent1, Parent2):
#     value = models.IntegerField()


# class Child2(Parent1):
#     parent2 = ZOneToOneField(Parent2, models.CASCADE)
#     value = models.IntegerField()


# class Child3(Child2):
#     value3 = models.IntegerField()


# class Child4(Child1):
#     value4 = models.IntegerField()


# class LinkedList(DynamicModelBase):
#     name = models.CharField(max_length=50)
#     previous_item = ZOneToOneField(
#         "self",
#         models.CASCADE,
#         related_name="next_item",
#         blank=True,
#         null=True,
#     )