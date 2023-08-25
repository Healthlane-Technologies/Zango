from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase


class CompanyAccount(DynamicModelBase):
  short_name = models.CharField(
        'Company code name',
        max_length=15,
        unique=True
        )
  full_name = models.CharField(
       'Company Legal Name',
       max_length=100,
       unique=True
       )
  company_logo = models.FileField(
        upload_to='company_logo/',
        verbose_name="Company Logo",
        null=True,
        blank=True
        )

  def __str__(self):
    return self.short_name