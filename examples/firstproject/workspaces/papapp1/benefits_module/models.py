from django.db import models
from django.contrib.postgres.fields import JSONField
# from django.utils.translation import ugettext_lazy as _

from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField, ZManyToManyField

from .global_config import ORDER_STATUS, BENEFIT_TYPE, CREDIT_UPDATE_TYPE, CREDIT_LIMIT_TYPE, DOC_CREDIT_EXPIRY_TYPES, BENEFIT_CATEGORY
from ..program_module.models import ProgramModel
from ..supplychainnode_module.models import SupplyChainNodes
from ..skus_module.models import OrderItemsModel


class BenefitsModel(DynamicModelBase):
    short_code = models.CharField(
                        "Short Code of Benefit",
                        max_length=25,
                        blank=True
                        )
    label = models.CharField(
                    "Label",
                    max_length=255,
                    )
    benefit_type = models.CharField(
                    "Benefit Type",
                    max_length=50,
                    choices=BENEFIT_TYPE,
                    blank=True
                    )
    benefit_category = models.CharField(
                    "Benefit Category",
                    max_length=50,
                    choices=BENEFIT_CATEGORY,
                    blank=True
                    )
    program = ZForeignKey(
                    ProgramModel,
                    related_name='benefits',
                    on_delete=models.SET_NULL
                    )
    # item_options = models.ManyToManyField(DispensingOptionsModel)
    item_choice_condition = models.TextField(
                    "Condition for Choosing",
                    max_length=2000,
                    blank=True
                    )
    # scn_executor_nodes = models.ManyToManyField(
    #                                 SupplyChainNodes,
    #                                 related_name='scn_executor_nodes',
    #                                 blank=True
    #                                 )
    # scn_extra1_nodes = models.ManyToManyField(
    #                                 SupplyChainNodes,
    #                                 related_name='scn_extra1_nodes',
    #                                 blank=True
    #                                 )
    # scn_extra2_nodes = models.ManyToManyField(
    #                                 SupplyChainNodes,
    #                                 related_name='scn_extra2_nodes',
    #                                 blank=True
    #                                 )
    # scn_extra3_nodes = models.ManyToManyField(
    #                                 SupplyChainNodes,
    #                                 related_name='scn_extra3_nodes',
    #                                 blank=True
    #                                 )
    generate_order_condition = models.TextField(
                    "Condition for Generating Order",
                    max_length=4000,
                    blank=True
                    )
    update_credit_condition = models.TextField(
                    "Condition for updating credit",
                    max_length=2000,
                    blank=True
                    )
    order_dispense_condition = models.TextField(
                    "Condition for order dispense",
                    max_length=2000,
                    blank=True
                    )
    order_close_condition = models.TextField(
                    "Condition for order close",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_1_condition = models.TextField(
                    "Condition for order Extra Status 1",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_2_condition = models.TextField(
                    "Condition for order Extra Status 2",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_3_condition = models.TextField(
                    "Condition for order Extra Status 3",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_4_condition = models.TextField(
                    "Condition for order Extra Status 4",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_5_condition = models.TextField(
                    "Condition for order Extra Status 5",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_6_condition = models.TextField(
                    "Condition for order Extra Status 6",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_7_condition = models.TextField(
                    "Condition for order Extra Status 7",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_8_condition = models.TextField(
                    "Condition for order Extra Status 8",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_9_condition = models.TextField(
                    "Condition for order Extra Status 9",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_10_condition = models.TextField(
                    "Condition for order Extra Status 10",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_11_condition = models.TextField(
                    "Condition for order Extra Status 11",
                    max_length=2000,
                    blank=True
                    )
    order_extrastatus_12_condition = models.TextField(
                    "Condition for order Extra Status 12",
                    max_length=2000,
                    blank=True
                    )
    order_return_condition = models.TextField(
                    "Condition for order return",
                    max_length=2000,
                    blank=True
                    )
    order_cancel_condition = models.TextField(
                    "Condition for order cancel",
                    max_length=2000,
                    blank=True
                    )
    order_scan_in_condition = models.TextField(
                    "Condition for order Scan In",
                    max_length=2000,
                    blank=True
                    )
    order_scan_out_condition = models.TextField(
                    "Condition for order Scan Out",
                    max_length=2000,
                    blank=True
                    )
    priority = models.IntegerField(
                    "Benefit Priority Order",
                    default=0
                    )
    extrafield1_text = models.TextField(
                    "ExtraField1 Text",
                    blank=True
                    )
    extrafield2_text = models.TextField(
                    "ExtraField2 Text",
                    blank=True
                    )
    extrafield1_char = models.CharField(
                    "ExtraField1 Char",
                    max_length=255,
                    blank=True
                    )
    extrafield2_char = models.CharField(
                    "ExtraField2 Char",
                    max_length=255,
                    blank=True
                    )


    def __str_(self):    
        return self.label
    

class BenefitsSupplyChainNodes(DynamicModelBase):
    benefit = ZForeignKey(
                    BenefitsModel,
                    on_delete=models.CASCADE,
                )
    scn_executor_nodes = ZForeignKey(
                    SupplyChainNodes,
                    on_delete=models.CASCADE,
                )
    



class DispensingOptionsModel(DynamicModelBase):

  label = models.CharField(
                   "Label",
                   max_length=255,
                   )
#   items = models.ManyToManyField(OrderItemsModel)
  dose = models.IntegerField(
                       "Dose",
                       null=True,
                       blank=True)
  min_dose = models.IntegerField(
                       "Min Dose",
                       null=True,
                       blank=True)
  max_dose = models.IntegerField(
                       "Max Dose",
                       null=True,
                       blank=True)
  min_income = models.BigIntegerField(
                        "Minimum Salary",
                        null=True,
                        blank=True
                        )
  max_income = models.BigIntegerField(
                        "Maximum Salary",
                        null=True,
                        blank=True
                        )
  order_number = models.CharField(
                      "Order Number",
                      max_length=255,
                      blank=True
                          )
  days_since_approval = models.IntegerField(
                      "Days since approval",
                      null=True,
                      blank=True
                      )
  days_of_supply = models.IntegerField(
                       "Days of supply",
                       blank=True,
                       null=True
                       )
  credit_required = models.FloatField(
                      "Credit required",
                      null=True,
                      blank=True
                      )
  credit_deducted = models.FloatField(
                      "Credit deducted",
                      null=True,
                      blank=True
                      )
  mrp = models.FloatField(
                      "MRP",
                      null=True,
                      blank=True
                      )
  jsonfield_extra1 = JSONField(null=True, blank=True)


  def __str__(self):
    return self.label
  


class DispensingOptionsOrderItemsModel(DynamicModelBase):
   dispensingoption = ZForeignKey(
                        DispensingOptionsModel,
                        on_delete=models.CASCADE
                    )
   items = ZForeignKey(
                OrderItemsModel,
                on_delete=models.CASCADE
            )
    

class BenefitsDispensingModel(DynamicModelBase):
   benefit = ZForeignKey(
                        BenefitsModel,
                        on_delete=models.CASCADE
                    )
   dispensingoption = ZForeignKey(
                DispensingOptionsModel,
                on_delete=models.CASCADE
            )