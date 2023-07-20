from django.db import models
from zelthy3.backend.apps.tenants.datamodel.fields import DataModelForeignKey, DataModelForeignKeyRef
from zelthy3.backend.apps.tenants.datamodel.models import SimpleMixim

class TenantUser(SimpleMixim):
    name = models.CharField(max_length=10, unique=True, null=True)
    jame = models.IntegerField(unique=True, null=True)

    class Meta:
        app_label = 'zelthy3.backend.apps.tenants.datamodel'
        db_table = "datamodel_tenantuser"

class TenantDetails(SimpleMixim):
    fame = models.CharField(max_length=100, default="dota", null=True)

    class Meta:
        app_label = 'zelthy3.backend.apps.tenants.datamodel'
        db_table = "datamodel_tenantdetails"

# class TenantRole(SimpleMixim):
#     usr = DataModelForeignKey(TenantUser, on_delete=models.PROTECT)
#     admin = DataModelForeignKey(TenantUser, on_delete=models.PROTECT)
#     role = models.CharField(max_length=30)
#     foreign_key_1 = DataModelForeignKeyRef(related_model="datamodel_tenantuser", field_name="usr")
#     foreign_key_2 = DataModelForeignKeyRef(related_model="datamodel_tenantuser", field_name= "admin")


#     class Meta:
#         app_label = 'zelthy3.backend.apps.tenants.datamodel'
#         db_table = "datamodel_tenantrole"