from django.db import models
from django.contrib.postgres.fields import JSONField
# from django.utils.translation import ugettext_lazy as _

from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField, ZManyToManyField


class SupplyChainNodes(DynamicModelBase):  
  label = models.CharField(
                       "Supply Chain Node Label",
                       max_length=50,
                       )  
#   therapy_role = models.ForeignKey(
#                     TherapyUserRoles,
#                     related_name='sn_therapy_role',
#                     null=True,
#                     blank=True,
#                     limit_choices_to=Qcurrent_therapy
#                     )
#   permission_to_userrole = models.ManyToManyField(
#                                     TherapyUserRoles,
#                                     related_name='sn_permission_therapy_roles',
#                                     limit_choices_to=Qcurrent_therapy,
#                                     blank=True
#                                     ) # these therapyroles have permission to access respective supply chain nodes 
  is_active = models.BooleanField(
                      "Is active",
                      default=True
                      )
  track_inventory = models.BooleanField(
                      "Track Inventory",
                      default=True
                      )


  def __str__(self):
    return self.label