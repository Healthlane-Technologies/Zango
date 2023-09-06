from django.db import models
import uuid
from django.contrib.postgres.fields import JSONField

from ..test_module.models import CityModel
from ..program_module.models import ProgramModel
from ..benefits_module.global_config import *

from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField, ZManyToManyField




# class DoctorModel(DynamicModelBase):
#   doctor_name = models.CharField(
#                   "Doctor Name",
#                   max_length=255
#               )
#   city = ZForeignKey(
#     CityModel,
# on_delete = models.CASCADE,    on_delete=models.CASCAD
# E,
#     blank=True,
#     null=True
#   )
  



# class AbstractPatient(DynamicModelBase):

#   name = models.CharField(
#                     "Name",
#                     max_length=255,
#                     )
  
#   class Meta(DynamicModelBase.Meta):
#     abstract = True


# class Patient2(AbstractPatient):
#   address = models.CharField(
#                     "Address",
#                     max_length=255,
#                     )
#   doctor = ZForeignKey(
#             DoctorModel,
# on_delete = models.CASCADE,            on_delete
# =models.CASCADE,
#             blank=True,
#             null=True
#   )
  


  
  




class AbstractTempOrderModel(DynamicModelBase):

  name = models.CharField(
                    "Name",
                    max_length=255,
                    )
  
  class Meta(DynamicModelBase.Meta):
    pass


class TempOrderModel(AbstractTempOrderModel):
  address = models.CharField(
                    "Address",
                    max_length=255,
                    )
  slug_code = models.UUIDField(
                          default=uuid.uuid4,
                          unique=True,
                          editable=False
                          )
  









# class AbstractTempModel(DynamicModelBase):

#   name = models.CharField(
#                     "Name",
#                     max_length=255,
#                     )
  
#   class Meta(DynamicModelBase.Meta):
#     pass


# class TempOrderModel(AbstractTempModel):
#   address = models.CharField(
#                     "Address",
#                     max_length=255,
#                     )










# ----------------------------------------------------------------------
MARITAL_STATUS = (('single', 'Single'),
                  ('married', 'Married'),
                  )

GENDER = (('m', 'Male'),
          ('f', 'Female'),
          ('o', 'Other'),
          ('d', 'Prefer not to say'),
          )


CAREGIVER_RELATIONS = (('spouse', 'Spouse'),
                      ('wife', 'Wife'),
                      ('husband', 'Husband'),
                      ('brother', 'Brother'),
                      ('sister', 'Sister'),
                      ('mother', 'Mother'),
                      ('father', 'Father'),
                      ('son', 'Son'),
                      ('daughter', 'Daughter'),
                      ('uncle', 'Uncle'),
                      ('auntie', 'Auntie'),
                      ('friend', 'Friend'),
                      ('relative', 'Other Relative'),
                      ('other', 'Other'),
                      )


BLOOD_GROUP = (('o_neg', 'O Negative'),
               ('o_pos', 'O Positive'),
               ('a_neg', 'A Negative'),
               ('a_pos', 'A Positive'),
               ('b_neg', 'B Negative'),
               ('b_pos', 'B Positive'),
               ('ab_neg', 'AB Negative'),
               ('ab_pos', 'AB Positive'),
              )



class Patient(DynamicModelBase):


  # COUNTRIES = get_country_choices()

  slug_code = models.UUIDField(
                          default=uuid.uuid4,
                          unique=True,
                          editable=False
                          )
  name = models.CharField(
                'Patient Name',
                max_length=150,
                blank=True
                )
  email = models.EmailField(
                'Primary Email',
                null=True,
                blank=True
                )
  alt_email = models.EmailField(
                'Alternate Email',
                null=True,
                blank=True
                )
  primary_phone = models.CharField(
               'Primary Phone',
                max_length=100,
               null=True,
               blank=True
               )
  alt_phone = models.CharField(
               'Alternate Phone',
                max_length=100,
               null=True,
               blank=True
               )
  phone3 = models.CharField(
               '3rd Phone',
                max_length=100,
               null=True,
               blank=True
               )
  phone4 = models.CharField(
               '4th Phone',
                max_length=100,
               null=True,
               blank=True
               )
  phone5 = models.CharField(
               '5th Phone',
                max_length=100,
               null=True,
               blank=True
               )
  phone6 = models.CharField(
               '6th Phone',
                max_length=100,
               null=True,
               blank=True
               )
  phone7 = models.CharField(
               '7th Phone',
                max_length=100,
               null=True,
               blank=True
               )
  phone8 = models.CharField(
               '8th Phone',
                max_length=100,
               null=True,
               blank=True
               )
  phone9 = models.CharField(
               '9th Phone',
                max_length=100,
               null=True,
               blank=True
               )
  dob = models.DateField(
                "Date of Birth",
                null=True,
                blank=True
                )
  gender = models.CharField(
                'Gender',
                max_length=10,
                choices=GENDER,
                null=True,
                blank=True
                )
  # citizenship = models.CharField(
  #                verbose_name = "Citizenship",
  #                max_length = 200,
  #                choices = COUNTRIES,
  #                null = True,
  #                blank=True
  #                )
  caregiver = models.CharField(
                 'Caregiver',
                 max_length=200,
                 blank=True
                  )
  caregiver_relation = models.CharField(
                  'Caregiver Relation',
                  max_length=100,
                  choices=CAREGIVER_RELATIONS,
                  blank=True
                  ),
  ethnicity = models.CharField(
                  'Ethnicity',
                  max_length=100,
                  blank=True
                  )
  # preferred_language = models.ForeignKey(
  #                LanguageModel,
  #                related_name='pref_language',
  #                null=True,
  #                blank=True,
  #                 )
  # second_language = models.ForeignKey(
  #                 LanguageModel,
  #                 related_name='second_language',
  #                 null=True,
  #                 blank=True
  #                 )
  marital_status = models.CharField(
                  'Marital Status',
                  max_length=100,
                  choices=MARITAL_STATUS,
                  blank=True
                  )
  blood_group = models.CharField(
                  'Blood Group',
                  max_length=10,
                  choices=BLOOD_GROUP,
                  blank=True
                  )
  alergies = models.CharField(
                  'Alergies',
                  max_length=150,
                  blank=True
                  )
  # emergency_contact = PhoneNumberField(
  #                 'Emergency Contact',
  #                 null=True,
  #                 blank=True
  #                 )
  # reimbursement = ZForeignKey(
  #               ReimbursementLevelModel,
  # on_delete = models.CASCADE,              null=Tr
  # ue,
  #               blank=True,
  #               limit_choices_to={'is_active':True}
  #                 )
  is_approved = models.BooleanField(
                    "Is Approved?",
                    default=False
                    )
  is_suspended = models.BooleanField(
                    "Is suspended?",
                    default=False
                    )
  age_in_years = models.FloatField(
                    "Age in Years",
                    null=True,
                    blank=True
                    )
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
  extrafield4_char = models.CharField(
                      "Extra Field4 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield5_char = models.CharField(
                      "Extra Field5 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield6_char = models.CharField(
                      "Extra Field6 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield7_char = models.CharField(
                      "Extra Field7 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield8_char = models.CharField(
                      "Extra Field8 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield9_char = models.CharField(
                      "Extra Field9 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield10_char = models.CharField(
                      "Extra Field10 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield11_char = models.CharField(
                      "Extra Field11 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield12_char = models.CharField(
                      "Extra Field12 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield13_char = models.CharField(
                      "Extra Field13 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield14_char = models.CharField(
                      "Extra Field14 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield15_char = models.CharField(
                      "Extra Field15 Char",
                      max_length=255,
                      blank=True
                      )
  extrafield1_text = models.TextField(
                      "Extra Field1 Text",
                      blank=True
                      )
  extrafield2_text = models.TextField(
                      "Extra Field2 Text",
                      blank=True
                      )
  extrafield3_text = models.TextField(
                      "Extra Field3 Text",
                      blank=True
                      )
  extrafield1_datetime = models.DateTimeField(
                       "Extra Field 1 DateTime",
                       null=True,
                       blank=True
                       )
  extrafield2_datetime = models.DateTimeField(
                       "Extra Field 2 DateTime",
                       null=True,
                       blank=True
                       )
  extrafield3_datetime = models.DateTimeField(
                       "Extra Field 3 DateTime",
                       null=True,
                       blank=True
                       )
  extrafield1_date = models.DateField(
                       "Extra Field 1 Date",
                       null=True,
                       blank=True
                       )
  extrafield2_date = models.DateField(
                       "Extra Field 2 Date",
                       null=True,
                       blank=True
                       )
  extrafield3_date = models.DateField(
                       "Extra Field 3 Date",
                       null=True,
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

  # tags = models.ManyToManyField(
  #                     PatientsTagModel,
  #                     limit_choices_to={'is_active':True},
  #                     blank=True
  #                     )

  jsonfield_extra1 = JSONField(null=True, blank=True)

  jsonfield_extra2 = JSONField(null=True, blank=True)

  city_fk = ZForeignKey(
                 CityModel,
                 on_delete = models.CASCADE,
                 null=True,
                 blank=True,
                 limit_choices_to={'is_active':True}
                 )
  # customoption1 = ZForeignKey(
  #                     PatientCustomOptionModel1,
  # on_delete = models.CASCADE,                    null=T
  # rue,
  #                     blank=True,
  #                     limit_choices_to={'is_active':True}
  #                     )
  # customoption2 = ZForeignKey(
  #                     PatientCustomOptionModel2,
  # on_delete = models.CASCADE,                    null=T
  # rue,
  #                     blank=True,
  #                     limit_choices_to={'is_active':True}
  #                     )
  # customoption3 = ZForeignKey(
  #                     PatientCustomOptionModel3,
  # on_delete = models.CASCADE,                    null=T
  # rue,
  #                     blank=True,
  #                     limit_choices_to={'is_active':True}
  #                     )
  # customoption4 = ZForeignKey(
  #                     PatientCustomOptionModel4,
  # on_delete = models.CASCADE,                    null=T
  # rue,
  #                     blank=True,
  #                     limit_choices_to={'is_active':True}
  #                     )
  # customoption5 = ZForeignKey(
  #                     PatientCustomOptionModel5,
  # on_delete = models.CASCADE,                    null=T
  # rue,
  #                     blank=True,
  #                     limit_choices_to={'is_active':True}
  #                     )
  # file = S3PrivateFileField(
  #                   upload_to=RandomUniqueFileName,
  #                   verbose_name="Patient File",
  #                   null=True,
  #                   blank=True
  #                   )
  # file_1 = S3PrivateFileField(
  #                   upload_to=RandomUniqueFileName,
  #                   verbose_name="Patient File 1",
  #                   null=True,
  #                   blank=True
  #                   )
  # file_2 = S3PrivateFileField(
  #                   upload_to=RandomUniqueFileName,
  #                   verbose_name="Patient File 2",
  #                   null=True,
  #                   blank=True
  #                   )
  # file_3 = S3PrivateFileField(
  #                   upload_to=RandomUniqueFileName,
  #                   verbose_name="Patient File 3",
  #                   null=True,
  #                   blank=True
  #                   )
  # user = models.OneToOneField(
  #                   Users,
  #                   related_name='patient_user',
  #                   null=True,
  #                   blank=True
  #                   )






class PatientProgramModel(DynamicModelBase):
  """
  Model to store applied programs
  """
  slug_code = models.UUIDField(
                          default=uuid.uuid4,
                          unique=True,
                          editable=False
                          )
  program = ZForeignKey(
                      ProgramModel,
                      on_delete = models.CASCADE,
                      related_name='patient_programs'
  )
  patient = ZForeignKey(
                      Patient,
                      on_delete = models.CASCADE,
                      related_name='applied_programs'
  )
  status = models.CharField(
                      "Program Status",
                      max_length=200,
                      choices=PROGRAM_STATUS,
                      default='applied'
                      )
  is_approved = models.BooleanField(default=False)
  # approved_by = models.ForeignKey(
  #                     Users,
  #                     null=True
  #                     )
  approval_date = models.DateTimeField(
                        null=True
                        )
  is_suspended = models.BooleanField(default=False)
  # suspended_by = models.ForeignKey(
  #                      Users,
  #                      related_name='suspended_by',
  #                      null=True
  #                      )
  # case = models.OneToOneField(
  #                       CaseModel,
  #                       related_name='case_program',
  #                       null=True
  #                        )
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
  extrafield1_text = models.TextField(
                      "Extra Field1 Text",
                      blank=True
                      )
  extrafield2_text = models.TextField(
                      "Extra Field2 Text",
                      blank=True
                      )
  extrafield3_text = models.TextField(
                      "Extra Field3 Text",
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
  # file_1 = S3PrivateFileField(
  #                   upload_to=RandomUniqueFileName,
  #                   verbose_name="Patient Program File 1",
  #                   null=True,
  #                   blank=True
  #                   )
  # file_2 = S3PrivateFileField(
  #                   upload_to=RandomUniqueFileName,
  #                   verbose_name="Patient Program File 2",
  #                   null=True,
  #                   blank=True
  #                   )
  # file_3 = S3PrivateFileField(
  #                   upload_to=RandomUniqueFileName,
  #                   verbose_name="Patient Program File 3",
  #                   null=True,
  #                   blank=True
  #                   )
  jsonfield_extra1 = JSONField(null=True, blank=True)
  jsonfield_extra2 = JSONField(null=True, blank=True)









