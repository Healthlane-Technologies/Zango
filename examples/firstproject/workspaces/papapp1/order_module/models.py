from django.db import models
import uuid
from random import randint
from django.contrib.postgres.fields import JSONField

from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField, ZManyToManyField

from ..benefits_module.global_config import *
from .. benefits_module.models import BenefitsModel, DispensingOptionsModel
from ..patient_module.models import PatientBenefitModel




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
                    # default=random_unique_code <--   causing migration error
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
  patient_benefit = ZForeignKey(
                      PatientBenefitModel,
                      related_name='all_benefit_orders',
                      null=True,
                      on_delete=models.CASCADE
                      )
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



  @classmethod
  def add(self, n1, n2):
    return n1+n2


  # @classmethod
  # def order_dispense_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_generation_date_searchvalue(self,arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_closure_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus1_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus2_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus3_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return    

  # @classmethod
  # def order_extrastatus4_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus5_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus6_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus7_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus8_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus9_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus10_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus11_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return

  # @classmethod
  # def order_extrastatus12_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return


  # @classmethod
  # def order_check1_date_searchvalue(self, arg):
  #   try:
  #     return processdatetimepicker(arg)
  #   except:
  #     return


  # @property
  # def order_id(self):
  #   return str(self.id+10000)


  # @classmethod
  # def order_id_searchquery(self):
  #   return 'id'

  # @classmethod
  # def order_id_searchvalue(self, arg):
  #   try:
  #     return int(arg)-10000
  #   except:
  #     return

  # @property
  # def order_id_url(self):
  #   url = reverse('order-view', kwargs={'slug':self.slug_code})
  #   return format_html("<a href='{url}'>"+self.order_id+"</a>", url= url)

  # @classmethod
  # def order_id_url_searchquery(self):
  #   return 'id'

  # @classmethod
  # def order_id_url_searchvalue(self, arg):
  #   try:
  #     return int(arg)-10000
  #   except:
  #     return

  @property
  def get_doctor_city(self):
    return self.doctor.city

  @classmethod
  def get_doctor_city_searchquery(self):
    return 'doctor__city__icontains'

  def get_patient(self):
    return self.patient_benefit.program.patient

  @property
  def patient(self):
    return self.get_patient().name

  @property
  def patient_dob(self):
    return self.get_patient().dob
  
  @property
  def patient_gender(self):
    return self.get_patient().get_gender_display
  

  @classmethod
  def patient_searchquery(self):
    return 'patient_benefit__program__patient__name__icontains'

  @property
  def get_patient_primary_phone(self):
    return self.get_patient().primary_phone

  @property
  def patient_memId(self):
    return self.get_patient().mem_id

  @classmethod
  def patient_memId_searchquery(self):
    return 'patient_benefit__program__patient__id'

  @classmethod
  def patient_memId_searchvalue(self, arg):
    try:
      return int(arg)-10000
    except:
      return

  # @property
  # def get_shipping_address(self):
  #   return format_html(self.shipping_address.print_address())

  @property
  def print_order_details(self):
    try:
      items = self.items_to_dispense.items.all()
      result_html = ""
      for item in items:
        line = "<p style='margin:5px;'>{}</p>".format(item)
        result_html = result_html + line
    except:
      result_html = ''
    return result_html

  @classmethod
  def print_order_details_searchquery(self):
    return 'items_to_dispense__items__sku__label__icontains'

  @property
  def get_order_status(self):
    if self.order_status == 'open':
      if self.benefit.config.display_open_as:
        return self.benefit.config.display_open_as
    if self.order_status == 'dispensed':
      if self.benefit.config.display_dispensed_as:
        return self.benefit.config.display_dispensed_as
    if self.order_status == 'closed':
      if self.benefit.config.display_close_as:
        return self.benefit.config.display_close_as
    if self.order_status == 'cancelled':
      if self.benefit.config.display_cancel_as:
        return self.benefit.config.display_cancel_as
    if self.order_status == 'returned':
      if self.benefit.config.display_return_as:
        return self.benefit.config.display_return_as
    if self.order_status == 'extrastatus_1':
      if self.benefit.config.display_extrastatus1_as:
        return self.benefit.config.display_extrastatus1_as      
    if self.order_status == 'extrastatus_2':
      if self.benefit.config.display_extrastatus2_as:
        return self.benefit.config.display_extrastatus2_as      
    if self.order_status == 'extrastatus_3':
      if self.benefit.config.display_extrastatus3_as:
        return self.benefit.config.display_extrastatus3_as      
    if self.order_status == 'extrastatus_4':
      if self.benefit.config.display_extrastatus4_as:
        return self.benefit.config.display_extrastatus4_as          
    if self.order_status == 'extrastatus_5':
      if self.benefit.config.display_extrastatus5_as:
        return self.benefit.config.display_extrastatus5_as 
    if self.order_status == 'extrastatus_6':
      if self.benefit.config.display_extrastatus6_as:
        return self.benefit.config.display_extrastatus6_as
    if self.order_status == 'extrastatus_7':
      if self.benefit.config.display_extrastatus7_as:
        return self.benefit.config.display_extrastatus7_as
    if self.order_status == 'extrastatus_8':
      if self.benefit.config.display_extrastatus8_as:
        return self.benefit.config.display_extrastatus8_as         
    if self.order_status == 'extrastatus_9':
      if self.benefit.config.display_extrastatus9_as:
        return self.benefit.config.display_extrastatus9_as         
    if self.order_status == 'extrastatus_10':
      if self.benefit.config.display_extrastatus10_as:
        return self.benefit.config.display_extrastatus10_as         
    if self.order_status == 'extrastatus_11':
      if self.benefit.config.display_extrastatus11_as:
        return self.benefit.config.display_extrastatus11_as         
    if self.order_status == 'extrastatus_12':
      if self.benefit.config.display_extrastatus12_as:
        return self.benefit.config.display_extrastatus12_as         
    return self.get_order_status_display()

  @classmethod
  def get_order_status_searchquery(self):
    return 'order_status__in'

  # @classmethod
  # def get_order_status_searchvalue(self, arg):
  #   result = []
  #   if BenefitOrderConfig.objects.filter(display_open_as__icontains=arg).count() > 0:
  #     result.append('open') 
  #   if BenefitOrderConfig.objects.filter(display_dispensed_as__icontains=arg).count() > 0:
  #     result.append('dispensed')
  #   if BenefitOrderConfig.objects.filter(display_close_as__icontains=arg).count() > 0:
  #     result.append('closed')
  #   if BenefitOrderConfig.objects.filter(display_return_as__icontains=arg).count() > 0:
  #     result.append('returned')
  #   if BenefitOrderConfig.objects.filter(display_cancel_as__icontains=arg).count() > 0:
  #     result.append('cancelled')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus1_as__icontains=arg).count() > 0:
  #     result.append('extrastatus_1')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus2_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_2')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus3_as__icontains=arg).count() > 0:
  #     result.append('extrastatus_3')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus4_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_4')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus5_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_5')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus6_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_6')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus7_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_7')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus8_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_8')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus9_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_9')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus10_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_10')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus11_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_11')
  #   if BenefitOrderConfig.objects.filter(display_extrastatus12_as__icontains=arg).count() > 0: 
  #     result.append('extrastatus_12')
  #   return result



