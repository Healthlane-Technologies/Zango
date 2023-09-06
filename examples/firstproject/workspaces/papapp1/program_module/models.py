from django.db import models
from django.contrib.postgres.fields import JSONField
# from django.core.urlresolvers import reverse # old reverse
from django.urls import reverse # new reverse
from django.utils.html import format_html

from zelthy.apps.dynamic_models.models import DynamicModelBase


CAMP_CHOICES = (
                ('hospital', 'Hospital'),
                ('doctor', 'Doctor'),
                )


class ProgramModel(DynamicModelBase):
  """
  Program Model
  """
  short_code = models.CharField(
                    "Short Code of Program",
                    max_length=25,
                    blank=True
                    )
  program_name = models.CharField(
                  "Program Name",
                  max_length=255,
                  unique=True
                  )
  description = models.TextField(
                  "Program Description",
                  blank=True
                  )
#   therapy_roles = models.ManyToManyField(
#                  TherapyUserRoles,
#                  limit_choices_to=Qcurrent_therapy
#                  )
  patient_eligibility = models.TextField(
                 max_length=2000,
                 blank=True)
  program_eligibility = models.TextField(
                 max_length=2000,
                 blank=True)
  extrafield1_char = models.CharField(
                      "Extra Field1 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield2_char = models.CharField(
                      "Extra Field2 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield3_char = models.CharField(
                      "Extra Field3 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield1_boolean = models.BooleanField(
                      "Extra Field1 Boolean",
                      default=False
                      )
  extrafield2_boolean = models.BooleanField(
                      "Extra Field2 Boolean",
                      default=False
                      )
  extrafield3_boolean = models.BooleanField(
                      "Extra Field3 Boolean",
                      default=False
                      )
  is_delivered_as_camp = models.BooleanField(
                 "Is the program delivered as camp",
                 default=False
                 )
  program_delivered_through = models.CharField(
                 "Camp delivery mode",
                 max_length=50,
                 choices=CAMP_CHOICES,
                 blank=True
                 )
  jsonfield_extra1 = JSONField(null=True, blank=True)


  def __str__(self):
    return self.program_name

  # def generate_patient_condition(self):
  #   url = reverse('program-eligibility-rule', kwargs={'id':self.id})
  #   return format_html("<a href='{url}'>Add/Modify</a>", url= url)

  def generate_program_condition(self):
    url = reverse('get-program-details')  #< ------------- NOT Working reverse()
    return format_html("<a href='{url}'>Add/Modify</a>", url= url)

  def has_free_benefits(self):
    free_benefits = self.benefits.all().filter(benefit_category='free')
    if free_benefits:
      return True
    return False
  
  # @property
  def get_all_linked_benefits(self):
    all_benefits = self.benefits.all()
    return all_benefits

# def get_program_options():
#   try:
#     return ProgramModel.objects.all_therapies()
#   except:
#     return []