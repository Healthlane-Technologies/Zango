from django.db import models
from django.contrib.postgres.fields import JSONField
# from django.utils.translation import ugettext_lazy as _

# from django.core.urlresolvers import reverse # old reverse
from django.urls import reverse # new reverse
from django.utils.html import format_html

from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField, ZManyToManyField
from zelthy.apps.appauth.models import UserRoleModel

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
    # test_role = ZOneToOneField(
    #                     UserRoleModel,
    #                     blank=True,
    #                     null=True,
    #                     on_delete=models.SET_NULL
    # )

    test_role = ZOneToOneField(
                        UserRoleModel,
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL
    )

    name1 = models.CharField(
        "Name",
        max_length=255,
        blank=True
    )
    temp_role = ZOneToOneField(
                        UserRoleModel,
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL
    )


    temp_role2 = ZOneToOneField(
                        UserRoleModel,
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL
    )

    class Meta(DynamicModelBase.Meta):
        ordering = ['-short_code']


    def __str__(self):    
        return self.label
    

    def get_config(self):
        cs = self.benefitorderconfig_set.all()
        if len(cs) > 0:
            return cs[0]
        return None


    # def get_min_credit_reqd(self):
    #     credits = []
    #     for item in self.item_options.all():
    #         if item.credit_required:
    #             credits.append(item.credit_required)
    #     return min(credits)


    def generate_item_choice_condition(self):
        url = reverse('add_benefit_condition', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_generation_condition(self):
        url = reverse('generate-order-condition', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_benefit_credit_update_condition(self):
        url = reverse('update-credit-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_dispense_condition(self):
        url = reverse('order-dispense-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_close_condition(self):
        url = reverse('order-close-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_return_condition(self):
        url = reverse('order-return-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_cancel_condition(self):
        url = reverse('order-cancel-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_scan_in_condition(self):
        url = reverse('generate-order-scan-in-condition', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_scan_out_condition(self):
        url = reverse('generate-order-scan-out-condition', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_1_condition(self):
        url = reverse('order-extra-status1-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_2_condition(self):
        url = reverse('order-extra-status2-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_3_condition(self):
        url = reverse('order-extra-status3-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_4_condition(self):
        url = reverse('order-extra-status4-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_5_condition(self):
        url = reverse('order-extra-status5-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_6_condition(self):
        url = reverse('order-extra-status6-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_7_condition(self):
        url = reverse('order-extra-status7-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_8_condition(self):
        url = reverse('order-extra-status8-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_9_condition(self):
        url = reverse('order-extra-status9-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_10_condition(self):
        url = reverse('order-extra-status10-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_11_condition(self):
        url = reverse('order-extra-status11-rule', kwargs={'id':self.id})
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)

    def generate_order_extrastatus_12_condition(self):
        # url = reverse('order-extra-status12-rule', kwargs={'id':self.id})
        url = "."
        return format_html("<a href='{url}'>Add/Modify</a>", url= url)


    def get_days_of_supply(self, dosage_per_cycle):
        pass
        

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


#   def print_sku_details(self):
#     items = self.items.all()
#     result_html = ""
#     for item in items:
#       line = "<p style='margin:5px;'>{} - ({} {})</p>".format(item.label, item.quantity, item.sku.pack_size)
#       result_html = result_html + line
#     return result_html
  


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