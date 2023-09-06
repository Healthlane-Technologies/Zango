from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
# from django.utils.translation import ugettext_lazy as _


class SystemDetails(DynamicModelBase):
    details = models.TextField()
    # label = models.CharField(
    #                    _("My Test Label"),
    #                    max_length=50,
    #                 ) 


class CityModel(DynamicModelBase):
    city_name = models.CharField(
        "City Name",
        max_length=255
    )