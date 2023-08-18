from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class OneUser(DynamicModelBase):
    username = models.CharField(max_length=100)
    email = models.EmailField()


class UserProfile(DynamicModelBase):
    user = ZOneToOneField(OneUser, models.CASCADE)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)


class UserStatResult(DynamicModelBase):
    results = models.CharField(max_length=50)


class UserStat(DynamicModelBase):
    user = ZOneToOneField(OneUser, models.CASCADE, primary_key=True)
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


class Child1(DynamicModelBase):
    parent1 = ZOneToOneField(Parent1, on_delete=models.CASCADE)
    parent2 = ZOneToOneField(Parent2, on_delete=models.CASCADE)
    value = models.IntegerField()


class Child2(DynamicModelBase):
    parent1 = ZOneToOneField(Parent1, on_delete=models.CASCADE)
    parent2 = ZOneToOneField(Parent2, models.CASCADE)
    value = models.IntegerField()


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