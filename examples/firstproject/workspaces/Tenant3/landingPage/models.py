from django.db import models


from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey
# from module1.models import Address

class LandingPageModel(DynamicModelBase):
    page = models.CharField(max_length=20)
    # address = ZForeignKey(Address, on_delete=models.CASCADE, null=True)

