from django.db import models
import uuid
from random import randint
from django.contrib.postgres.fields import JSONField

from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField, ZManyToManyField

from ..benefits_module.global_config import *
from .. benefits_module.models import BenefitsModel, DispensingOptionsModel
# from ..patient_module.models import PatientProgramModel




def random_unique_code():
    get_code = True
    while get_code:
        new_code = str(randint(100000, 999999))
        if len(OrderModel.objects.filter(ordercode=new_code)) == 0:
            get_code = False
            final_code = new_code
    return final_code



class OrderModel(DynamicModelBase):

  slug_code = models.UUIDField(
                          default=uuid.uuid4,
                          unique=True,
                          editable=False
                          )
  ordercode = models.CharField(
                    max_length=6,
                    verbose_name="Order Code",
                    # unique=True,
                    default=random_unique_code
                    )
  order_generation_date = models.DateTimeField(
                     verbose_name="Order Generation Date",
                     auto_now_add=True
                     )
  order_dispense_date = models.DateTimeField(
                     verbose_name="Order Dispense Date",
                     null=True
                     )
  order_closure_date = models.DateTimeField(
                     verbose_name="Order Closure Date",
                     null=True
                     )
  order_extrastatus1_date = models.DateTimeField(
                     verbose_name="Order Extra Status 1 Date",
                     null=True
                     )
  order_extrastatus2_date = models.DateTimeField(
                     verbose_name="Order Extra Status 2 Date",
                     null=True
                     )
  order_extrastatus3_date = models.DateTimeField(
                     verbose_name="Order Extra Status 3 Date",
                     null=True
                     )
  order_extrastatus4_date = models.DateTimeField(
                     verbose_name="Order Extra Status 4 Date",
                     null=True
                     )
  order_extrastatus5_date = models.DateTimeField(
                     verbose_name="Order Extra Status 5 Date",
                     null=True
                     )
  order_extrastatus6_date = models.DateTimeField(
                     verbose_name="Order Extra Status 6 Date",
                     null=True
                     )
  order_extrastatus7_date = models.DateTimeField(
                     verbose_name="Order Extra Status 7 Date",
                     null=True
                     )
  order_extrastatus8_date = models.DateTimeField(
                     verbose_name="Order Extra Status 8 Date",
                     null=True
                     )
  order_extrastatus9_date = models.DateTimeField(
                     verbose_name="Order Extra Status 9 Date",
                     null=True
                     )
  order_extrastatus10_date = models.DateTimeField(
                     verbose_name="Order Extra Status 10 Date",
                     null=True
                     )
  order_extrastatus11_date = models.DateTimeField(
                     verbose_name="Order Extra Status 11 Date",
                     null=True
                     )
  order_extrastatus12_date = models.DateTimeField(
                     verbose_name="Order Extra Status 12 Date",
                     null=True
                     )
  order_cancel_date = models.DateTimeField(
                     verbose_name="Order Cancel Date",
                     null=True
                     )
  order_status = models.CharField(
                      verbose_name="Order Status",
                      max_length=255,
                      choices=ORDER_STATUS,
                      blank=True
                          )
  benefit = ZForeignKey(
                      BenefitsModel,
                      on_delete=models.CASCADE,
                      related_name='benefit_orders',
                      null=True
                      )
#   patient_benefit = models.ForeignKey(
#                       PatientBenefitModel,
#                       related_name='all_benefit_orders',
#                       null=True
#                       )
#   shipping_address = models.ForeignKey(
#                      PatientAddress,
#                      null=True
#                      )
  items_to_dispense = ZForeignKey(
                      DispensingOptionsModel,
                      on_delete=models.CASCADE,
                      null=True
                      )
#   order_generate_document = models.OneToOneField(
#                     OrderGenerateDocumentModel,
#                     related_name='order_generate',
#                     null=True
#                     )
#   order_execute_document = models.OneToOneField(
#                     OrderExecuteDocumentModel,
#                     related_name='order_exec',
#                     null=True
#                     )
#   order_close_document = models.OneToOneField(
#                     OrderCloseDocumentModel,
#                     related_name='order_close',
#                     null=True
#                     )
#   order_cancel_document = models.OneToOneField(
#                     OrderCancelDocumentModel,
#                     related_name='order_cancel',
#                     null=True
#                     )
#   order_extrastatus1_document = models.OneToOneField(
#                     OrderExtraStatus1DocumentModel,
#                     related_name='order_extrastatus_1',
#                     null=True
#                     )
#   order_extrastatus2_document = models.OneToOneField(
#                     OrderExtraStatus2DocumentModel,
#                     related_name='order_extrastatus_2',
#                     null=True
#                     )
#   order_extrastatus3_document = models.OneToOneField(
#                     OrderExtraStatus3DocumentModel,
#                     related_name='order_extrastatus_3',
#                     null=True
#                     )
#   order_extrastatus4_document = models.OneToOneField(
#                     OrderExtraStatus4DocumentModel,
#                     related_name='order_extrastatus_4',
#                     null=True
#                     )
#   order_extrastatus5_document = models.OneToOneField(
#                     OrderExtraStatus5DocumentModel,
#                     related_name='order_extrastatus_5',
#                     null=True
#                     )
#   order_extrastatus6_document = models.OneToOneField(
#                     OrderExtraStatus6DocumentModel,
#                     related_name='order_extrastatus_6',
#                     null=True
#                     )
#   order_extrastatus7_document = models.OneToOneField(
#                     OrderExtraStatus7DocumentModel,
#                     related_name='order_extrastatus_7',
#                     null=True
#                     )
#   order_extrastatus8_document = models.OneToOneField(
#                     OrderExtraStatus8DocumentModel,
#                     related_name='order_extrastatus_8',
#                     null=True
#                     )
#   order_extrastatus9_document = models.OneToOneField(
#                     OrderExtraStatus9DocumentModel,
#                     related_name='order_extrastatus_9',
#                     null=True
#                     )
#   order_extrastatus10_document = models.OneToOneField(
#                     OrderExtraStatus10DocumentModel,
#                     related_name='order_extrastatus_10',
#                     null=True
#                     )
#   order_extrastatus11_document = models.OneToOneField(
#                     OrderExtraStatus11DocumentModel,
#                     related_name='order_extrastatus_11',
#                     null=True
#                     )
#   order_extrastatus12_document = models.OneToOneField(
#                     OrderExtraStatus12DocumentModel,
#                     related_name='order_extrastatus_12',
#                     null=True
#                     )
#   case = models.OneToOneField(
#                     CaseModel,
#                     related_name='case_order',
#                     null=True
#                      )
  order_note = models.TextField(
                    "Order Note",
                    max_length=1000,
                    blank=True
                    )
#   file = S3PrivateFileField(
#                     upload_to=RandomUniqueFileName,
#                     verbose_name="Order File",
#                     null=True,
#                     blank=True
#                     )

#   file_2 = S3PrivateFileField(
#                     upload_to=RandomUniqueFileName,
#                     verbose_name="File 2",
#                     null=True,
#                     blank=True
#                     )

#   file_3 = S3PrivateFileField(
#                     upload_to=RandomUniqueFileName,
#                     verbose_name="File 3",
#                     null=True,
#                     blank=True
#                     )


