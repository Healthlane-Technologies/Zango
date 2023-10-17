from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator
from django.core.exceptions import ValidationError


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




def age_validator(value):
    if value < 0:
        raise ValidationError("Age should be +ve only.")
    
    if value > 100:
        raise ValidationError("Age should not greater that 100")
    print("value =>", value)
    return value


class TempProfile(DynamicModelBase):
    name = models.CharField(max_length=100, validators=[MinLengthValidator])
    email = models.EmailField(max_length=200)
    age = models.IntegerField(validators=[age_validator]) #validators=[age_validator] <--- custom validators not worked

