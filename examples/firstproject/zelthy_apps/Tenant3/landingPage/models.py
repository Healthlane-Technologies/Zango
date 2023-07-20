from zelthy3.backend.apps.tenants.datamodel.models import SimpleMixim
from django.db import models

class TestDdm(SimpleMixim):
    name = models.CharField(max_length=100)



