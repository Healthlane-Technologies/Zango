# Create your models here.

from django.db import models
from django.contrib.postgres.fields import ArrayField
from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase


class Address(DynamicModelBase):
    use = models.CharField(max_length=50)
    type = models.CharField(max_length=50, null=True)
    text = models.CharField(max_length=255, null=True)
    # line = ArrayField(models.CharField(max_length=100, null=True))
    city = models.CharField(max_length=100, null=True)
    district = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=100, null=True)
    postalCode = models.CharField(max_length=50, null=True)
    country = models.CharField(max_length=50, null=True)
    
class Patient(DynamicModelBase):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown'),
    ]
    identifier = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    name = models.CharField(max_length=200)
    telecom = models.CharField(max_length=200)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unknown')
    birthDate = models.DateField()
    deceasedBoolean = models.BooleanField(default=False)
    deceasedDateTime = models.DateTimeField(null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    address_1 = models.ManyToManyField(Address)



class TestModel1(DynamicModelBase):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=100, null=True)



class TestModel2(DynamicModelBase):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, null=True)


from zelthy3.backend.apps.tenants.appauth.models import UserRoleModel
from django.db.models import JSONField

class FrameModel(DynamicModelBase):
    role = models.ForeignKey("appauth.UserRoleModel", null=True, on_delete=models.CASCADE)
    config = JSONField()
    timestamp = models.DateField(null=True)
    many_test = models.ManyToManyField("appauth.UserRoleModel")
    test = models.CharField(max_length=100, null=True)
 