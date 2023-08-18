from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField

class Manager(DynamicModelBase):
    name = models.CharField(max_length=50)


class Employee(DynamicModelBase):
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    salary = models.IntegerField(blank=True, null=True)
    manager = ZForeignKey(Manager, models.CASCADE, null=True)

    def __str__(self):
        return "%s %s" % (self.firstname, self.lastname)

class Company(DynamicModelBase):
    name = models.CharField(max_length=100)
    num_employees = models.PositiveIntegerField()
    num_chairs = models.PositiveIntegerField()
    ceo = ZForeignKey(
        Employee,
        models.CASCADE,
        related_name="company_ceo_set",
    )
    point_of_contact = ZForeignKey(
        Employee,
        models.SET_NULL,
        related_name="company_point_of_contact_set",
        null=True,
    )
    based_in_eu = models.BooleanField(default=False)

    def __str__(self):
        return self.name