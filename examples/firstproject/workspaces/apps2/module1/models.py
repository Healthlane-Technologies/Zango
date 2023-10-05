import uuid
from django.db import models
from zelthy.apps.appauth.models import UserRoleModel
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey


from django.db import models

class FHIRPatient(DynamicModelBase):
    identifier = models.CharField(max_length=200, unique=True)
    family = models.CharField(max_length=200, blank=True)  # Last name
    given = models.CharField(max_length=200, blank=True)   # First name
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown')
    ])
    birth_date = models.DateField(null=True, blank=True)
    address_line = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    user_role = ZForeignKey(UserRoleModel, null=True, blank=True, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.given} {self.family}"

