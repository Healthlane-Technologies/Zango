from zelthy.backend.apps.tenants.dynamic_models.models import DynamicModelBase
from django.db import models
from django.contrib.postgres.fields import ArrayField

class Address(DynamicModelBase):
    use = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    text = models.CharField(max_length=255)
    line = ArrayField(models.CharField(max_length=100))
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postalCode = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    
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
