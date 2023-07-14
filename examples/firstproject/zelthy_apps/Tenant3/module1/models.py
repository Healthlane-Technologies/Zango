from django.db import models
from zelthy3.backend.apps.tenants.datamodel.fields import DataModelForeignKey
from zelthy3.backend.apps.tenants.datamodel.models import SimpleMixim

class TenantUser(SimpleMixim):
    name = models.CharField(max_length=10)

    class Meta:
        db_table = "datamodel_tenantuser"

class TenantRole(SimpleMixim):
    usr = models.ForeignKey("TenantUser", on_delete=models.PROTECT)
    role = models.CharField(max_length=30)
    foreign_key_1 = DataModelForeignKey(related_model="datamodel_tenantuser", field_name="usr")


    class Meta:
        db_table = "datamodel_tenantrole"