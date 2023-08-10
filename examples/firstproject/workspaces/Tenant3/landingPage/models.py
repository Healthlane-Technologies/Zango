from django.db import models


from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase
from zelthy3.backend.apps.tenants.dynamic_models.fields import ZForeignKey
# from module1.models import Address

class LandingPageModel(DynamicModelBase):
    page = models.CharField(max_length=20)
    # address = ZForeignKey(Address, on_delete=models.CASCADE, null=True)

