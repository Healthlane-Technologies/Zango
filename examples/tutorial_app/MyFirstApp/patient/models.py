from django.db import models

from zango.apps.dynamic_models.models import DynamicModelBase


class Patient(DynamicModelBase):
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=255)
    dob = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name
