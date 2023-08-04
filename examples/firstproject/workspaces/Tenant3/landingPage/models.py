from django.db import models


from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase


class LandingPageModel(DynamicModelBase):
    page = models.CharField(max_length=20)

