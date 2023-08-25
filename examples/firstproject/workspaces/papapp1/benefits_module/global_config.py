# -*- coding: utf-8 -*-
from __future__ import unicode_literals

'''
Global Configuration File
'''
# from django.utils.translation import ugettext_lazy as _
import pytz

COMPANY_USER_EMAIL_SUFFIX = '@zelthy.com'


USER_TYPE = (
             ('superuser', 'Super User'),
             ('companyuser', 'Company User'),
             ('zelthyuser', 'Zelthy User'),
             )
"""
company user is created at company tenant and is allowed login through tenant domain
zelthy user is created at public tenant and is allowed login through public domain ('e.g cloud.zelthy.com')

"""


TENANT_TYPE = (
               ('shared', 'Shared'),
               ('therapy', 'Therapy'),
               ('company', 'Company'),
               )


USER_CATEGORIES = (
                   ('DoctorModel', 'Doctor'),
                   ('HospitalModel', 'Hospital'),
                   ('Patient', 'Patient'),
                   ('SalesLevel5Model', 'Sales Level 5'),
                   ('SalesLevel4Model', 'Sales Level 4'),
                   ('SalesLevel3Model', 'Sales Level 3'),
                   ('SalesLevel2Model', 'Sales Level 2'),
                   ('SalesLevel1Model', 'Sales Level 1'),
                   ('PhlebotomistModel', 'Phlebotomist'),
                   ('SupplyChainModel', 'SupplyChainModel'),
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


MARITAL_STATUS = (('single', 'Single'),
                  ('married', 'Married'),
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

HOSPITAL_TYPES = (('private_standalone', 'Private Hospital'),
                 ('corp_chain_', 'Corporate Chain'),
                 ('govt_school_hosp', 'Government Medical School Hospital'),
                 ('govt_hosp', 'Government Hospital'),
                 ('priv_school_hosp', 'Private Medical School Hospital'),
                 ('priv_nursing_home', 'Private Nursing Home'),
                 ('priv_clinic', 'Private Clinic'),
                 ('esic_hosp', 'ESIC Hospital'),
                 ('military_hosp', 'Military Hospital'),
                 ('esic_hosp', 'ESIC Hospital'),
                 ('railways_hosp', 'Railways Hospital'),
                 ('state_gov_hosp', 'State Government Hospital'),
                 ('other', 'Other'),
                )

HOSPITAL_ACCOUNT_TYPE = (('trade', 'Trade'),
                         ('key_account', 'Key Account'),
                         ('tender', 'Tender'),
                        )

DOCTOR_SALUTATIONS = (('Dr.', 'Dr.'),
                      ('Colonel', 'Colonel'),
                      ('Lt. Col', 'Lt. Col'),
                      )

PHARMACY_TYPE = (('standalone', 'Standalone Pharmacy'),
                  ('chain_pharmacy', 'Pharmacy Chain'),
                  ('hosp_pharmacy', 'Hospital Pharmacy'),
                )

IDENTITY_CARD_TYPES = (('pan_in', 'PAN Card'),
                       ('voter_in', 'Voter ID Card'),
                       ('aadhar_in', 'Aadhar Card'),
                       ('driving_lic_in', 'Driving License'),
                       )

DOCUMENT_CONFIG = (('IdentityCardModel', 'Identity Card',  'IDCardFormConfigModel', ),
                   ('PrescriptionModel', 'Prescription',  'PrescriptionFormModel', ),
                   ('EnrolmentFormModel', 'Enrolment Form',  'EFFormConfigModel',),
                   ('PatientConsentFormModel', 'Patient Consent Form',   'PCFFormConfigModel',  ),
                   ('DoctorConsentFormModel', 'Doctor Consent Form', 'DCFFormConfigModel',  ),
                   ('SelfDeclarationModel', 'Self Declaration', 'SelfDeclarationFormConfigModel',  ),
                   ('ApprovalLetterModel', 'Approval Letter', 'ApprovalLetterFormConfigModel',  ),
                   ('InvoiceModel', 'Invoice', 'InvoiceFormConfigModel',  ),
                   ('CreditUpdateRequestModel', 'Credit Update Form', 'CreditUpdateFormConfigModel',),
                   )


PROGRAM_STATUS = (
                  ('ineligible', 'Not Eligible'),
                  ('eligible', 'Eligible'),
                  ('applied', 'Applied'),
                  ('active', 'Active'),
                  ('shortfall', 'Document Shortfall'),
                  ('complete','Completed'),
                  ('suspend', 'Suspended'),
                  ('rejected', 'Rejected'),
                  )

BENEFIT_STATUS = (
                  ('applied', 'Applied'),
                  ('active', 'Active'),
                  ('shortfall', 'Document Shortfall'),
                  ('complete','Completed'),
                  ('suspend', 'Suspended'),
                  )


REIMBUSEMENT = (
                ('no_reimbursement', 'No Reimbursement'),
                ('partial_reimbursement', 'Partial Reimbursement'),
                ('full_reimbursement', 'Full Reimbursement'),
                )


ORDER_STATUS = (
                ('open', 'Open'),
                ('dispensed', 'Dispensed'),
                ('closed', 'Closed'),
                ('cancelled', 'Cancelled'),
                ('returned', 'Returned'),
                ('extrastatus_1', 'Extra Status 1'),
                ('extrastatus_2', 'Extra Status 2'),
                ('extrastatus_3', 'Extra Status 3'),
                ('extrastatus_4', 'Extra Status 4'),
                ('extrastatus_5', 'Extra Status 5'),
                ('extrastatus_6', 'Extra Status 6'),
                ('extrastatus_7', 'Extra Status 7'),
                ('extrastatus_8', 'Extra Status 8'),
                ('extrastatus_9', 'Extra Status 9'),
                ('extrastatus_10', 'Extra Status 10'),
                ('extrastatus_11', 'Extra Status 11'),
                ('extrastatus_12', 'Extra Status 12'),
                )


CREDIT_TRANSACTION_STATUS = (
                ('complete', 'Complete'),
                ('reversed', 'Reversed'),
                )

SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']

PREFIX_SHOW = '_show'
PREFIX_SHOW_DETAIL = '_show_detail'
PREFIX_SHOW_EXCEL = '_show_excel'
####Form Builder
PREFIX_PLACEHOLDER = '_placeholder'
PREFIX_WIDTH = '_width'
PREFIX_SHOW_VALIDATOR = '_show_validator'
PREFIX_NONEMPTY_MESSAGE = '_notEmpty_message'
PREFIX_REGEX_MESSAGE = '_regex_message'
PREFIX_REGEX_PATTERN = '_regex_pattern'
PREFIX_ROW_NUMBER = '_row_number'
PREFIX_COL_NUMBER = '_col_number'
PREFIX_EXTRA_CSS = '_extra_css'
PREFIX_EXTRA_ATTRIBUTE = '_extra_attribute'
PREFIX_IS_UNIQUE = '_is_unique'
PREFIX_IS_HIDDEN = '_is_hidden'

###Table Builder
TABLE_PREFIX_TITLE = '_title'
TABLE_PREFIX_COL_NUMBER = '_column'
TABLE_PREFIX_DETAIL_COL_NUMBER = '_detail_col_number'
TABLE_PREFIX_EXCEL_COL_NUMBER = '_excel_col_number'
TABLE_PREFIX_IS_SEARCHABLE = '_is_searchable'

DEFAULT_SALES_ORG = (('field_rep', 'Field Representative'),
                     ('area_manager', 'Area Manager'),
                     ('zonal_manager', 'Zonal Manager'),
                     ('national_manager', 'National Manager'),)


CALLTYPES = (
             ('incoming', 'Incoming'),
             ('outgoing', 'Outgoing'),
             )

TELEPHONY_PROVIDER = (
                       ('knowlarity', 'Knowlarity'),
                       ('exotel', 'Exotel'),
                       ('ozonetel', 'Ozonetel'),
                       ('aisth', 'AIS Thailand'),
                       ('nice', 'NICE'),
                       )
SMS_PROVIDER = (
                ('plivo', 'Plivo'),
                ('ais', 'AIS Thailand'),
                ('ozonetel', 'Ozonetel'),
                ('msg91', 'Msg91'),
                ('infobip', 'Infobip'),
                )

NOTIFICATION_PROVIDER = (
                ('firebase', 'Firebase'),
                )
SOURCE_TYPE = (
                ('sdk', 'SDK'),
                ('api', 'API'),
                )


MONTH = (
         ('January', 'January'),
         ('February', 'February'),
         ('March','March'),
         ('April','April'),
         ('May','May'),
         ('June','June'),
         ('July','July'),
         ('August','August'),
         ('September','September'),
         ('October','October'),
         ('November','November'),
         ('December','December')
         )

RECONSTATUS = (
               ('open', 'Open'),
               ('accepted', 'Accepted'),
               ('closed','Closed')
               )

BENEFIT_TYPE = (
              ('drug', 'Drug Benefit'),
              ('others', 'Others'),
              )

BENEFIT_CATEGORY = (
              ('free', 'Free'),
              ('prepaid', 'Prepaid'),
              ('cod', 'Cash on Delivery'),
              )

CREDIT_UPDATE_TYPE = (
              ('manual', 'Manual Input in Credit Update Form'),
              ('auto_fixed', 'Automatic-Fixed'),
              ('auto_multiplier', 'Automatic-Multiplier')
              )

CREDIT_LIMIT_TYPE = (
              ('fixed', 'Fixed Credit Limit'),
              ('multiplier', 'Multiplier Credit Limit'),
              ('nolimit', 'No Credit Limit')
              )


PV_REPORTING_METHODS = (('email', 'Email'),
                        ('phone', 'Phone'),
                        ('app', 'Mobile App'),
                        )

TIMEZONES = []
for tz in pytz.all_timezones:
  TIMEZONES.append((tz, tz))

TIMEZONES = tuple(TIMEZONES)

DATEFORMAT = (
              ('%d %b %Y','04 Oct 2017'),
              ('%d %B %Y','04 October 2017'),
              ('%d/%m/%Y','04/10/2017'),
              ('%d/%m/%y','04/10/17'),
              ('%m/%d/%y','10/04/17'),
              ('%d/%m/%Y','04/10/2017'),
              )

DATETIMEFORMAT = (
              ('%d %b %Y %H:%M','04 Oct 2017 13:48'),
              ('%d %b %Y %I:%M %p','04 Oct 2017 01:48 PM'),
              ('%d %B %Y %H:%M','04 October 2017 13:48'),
              ('%d %B %Y %I:%M %p','04 October 2017 01:48 PM'),
              ('%d/%m/%Y %H:%M','04/10/2017 13:48'),
              ('%d/%m/%y %I:%M %p','04/10/17 01:48 PM'),
              ('%m/%d/%y %H:%M','10/04/17 13:48'),
              ('%d/%m/%Y %I:%M %p','04/10/2017 01:48 PM'),
              )


COMMUNICATION_TYPES = (
                      ('email', 'Email'),
                      ('sms', 'SMS'),
                      )


MENUCHOICES = (
      ('Patients', 'Patients'),
      ('Program_Applications', "Program Applications"),
      ('Orders', 'Orders'),
      ('Reconciliation-Self', 'Reconciliation-Self'),
      ('Reconciliation-Others', 'Reconciliation-Others'),
      ('Pharmacovigilance','Pharmacovigilance'),
      ('Inventory', 'Inventory'),
      ('Purchase', 'Purchase'),
      ('Hospital', 'Hospital'),
      ('Doctor', 'Doctor'),
      ('Call Center', 'Call Center'),
      ('Sales Level 5', 'Sales Level 5'),
      ('SalesLevel4Model', 'Sales Level 4'),
      ('SalesLevel3Model', 'Sales Level 3'),
      ('SalesLevel2Model', 'Sales Level 2'),
      ('SalesLevel1Model', 'Sales Level 1'),
      ('Sales', 'Sales'),
      ('Cases', 'Cases'),
      ('Credits', 'Credits'),
      ('Vouchers', 'Vouchers'),
      ('Phlebotomist', 'Phlebotomist'),
      ('Camps', 'Camps'),
      ('Tasks', 'Tasks'),
      )


DOC_CREDIT_EXPIRY_TYPES = (
                          ('days', '# of days'),
                          ('date', 'Date'),
                          )


DOCTORQUALIFICATION = (
                       ('MS', 'MS'),
                       ('MD', 'MD'),
                       ('DM', 'DM'),
                       ('other', 'Other')
                       )

LEGALNOTICETYPE = (
                   ('hosted','Self Hosted'),
                   ('external', 'External Link'),
                   )

NOTESTATUS = (
              ('open', 'Open'),
              ('closed', 'Closed'),
              ('complete', 'Complete')
              )

APP_STATUSES = (
                 ('deployed', 'Deployed'),
                 ('suspended', 'Suspended'),
                 ('deleted', 'Deleted'),
                 ) # only valid for production apps

UPLOAD_STATUS = (
                 ('initiated', 'Initiated'),
                 ('inprogress', 'In Progress'),
                 ('failed', 'Failed'),
                 ('completed', 'Completed'),
                 )

REPORT_STATUS = (
                 ('requested', 'Requested'),
                 ('waiting', 'Waiting'),
                 ('inprogress', 'In Progress'),
                 ('completed', 'Completed'),
                 ('failed', 'Failed'),
                 )

VIDEOCALL_PROVIDER = (
                        ('twilio','Twilio'),
                      )

FAX_PROVIDER = (
              ('gofax','Gofax'),
              )

FAX_STATUS = (
              ('initialised','Initialised'),
              ('invalid number','Invalid Number'),
              ('invalid documents','Invalid Documents'),
              ('sent','Sent'),
              ('received','Received'),
              ('insufficient credit','Insufficient Credit'),
              )

CODE_TYPES = (
              ('object_code', 'Object Code'),
              ('generic_code', 'Generic Code'),
            )

COUNTRY_CODES = {'BD': '880', 'BE': '32', 'BF': '226', 'BG': '359', 'BA': '387', 'BB': '1', 'WF': '681', 'BL': '590', 'BM': '1', 'BN': '673', 'BO': '591', 'JP': '81', 'BI': '257', 'BJ': '229', 'BT': '975', 'JM': '1', 'BW': '267', 'WS': '685', 'BQ': '599', 'BR': '55', 'BS': '1', 'JE': '44', 'BY': '375', 'BZ': '501', 'RU': '7', 'RW': '250', 'RS': '381', 'TL': '670', 'RE': '262', 'PA': '507', 'TJ': '992', 'RO': '40', 'PG': '675', 'GW': '245', 'GU': '1', 'GT': '502', 'GR': '30', 'GQ': '240', 'GP': '590', 'BH': '973', 'GY': '592', 'GG': '44', 'GF': '594', 'GE': '995', 'GD': '1', 'GB': '44', 'GA': '241', 'SV': '503', 'GN': '224', 'GM': '220', 'GL': '299', 'KW': '965', 'GI': '350', 'GH': '233', 'OM': '968', 'IL': '972', 'JO': '962', 'TA': '290', 'KH': '855', 'HR': '385', 'HT': '509', 'HU': '36', 'HK': '852', 'HN': '504', 'AD': '376', 'PR': '1', 'PS': '970', 'PW': '680', 'PT': '351', 'SJ': '47', 'AF': '93', 'IQ': '964', 'LV': '371', 'PF': '689', 'UY': '598', 'PE': '51', 'PK': '92', 'PH': '63', 'TM': '993', 'PL': '48', 'PM': '508', 'ZM': '260', 'EH': '212', 'EE': '372', 'EG': '20', 'ZA': '27', 'EC': '593', 'AL': '355', 'AO': '244', 'SB': '677', 'ET': '251', 'ZW': '263', 'SA': '966', 'ES': '34', 'ER': '291', 'ME': '382', 'MD': '373', 'MG': '261', 'MF': '590', 'MA': '212', 'MC': '377', 'UZ': '998', 'MM': '95', 'ML': '223', 'MO': '853', 'MN': '976', 'MH': '692', 'US': '1', 'MU': '230', 'MT': '356', 'MW': '265', 'MV': '960', 'MQ': '596', 'MP': '1', 'MS': '1', 'MR': '222', 'IM': '44', 'UG': '256', 'MY': '60', 'MX': '52', 'MZ': '258', 'FR': '33', 'AW': '297', 'FI': '358', 'FJ': '679', 'FK': '500', 'FM': '691', 'FO': '298', 'NI': '505', 'NL': '31', 'NO': '47', 'NA': '264', 'VU': '678', 'NC': '687', 'NE': '227', 'NF': '672', 'NG': '234', 'NZ': '64', 'NP': '977', 'NR': '674', 'NU': '683', 'CK': '682', 'XK': '383', 'CI': '225', 'CH': '41', 'CO': '57', 'CN': '86', 'CM': '237', 'CL': '56', 'CC': '61', 'CA': '1', 'LB': '961', 'CG': '242', 'CF': '236', 'CD': '243', 'CZ': '420', 'CY': '357', 'CX': '61', 'CR': '506', 'PY': '595', 'KP': '850', 'CW': '599', 'CV': '238', 'CU': '53', 'SZ': '268', 'SY': '963', 'SX': '1', 'KG': '996', 'KE': '254', 'SS': '211', 'SR': '597', 'KI': '686', 'TK': '690', 'KN': '1', 'KM': '269', 'ST': '239', 'SK': '421', 'KR': '82', 'SI': '386', 'SH': '290', 'SO': '252', 'SN': '221', 'SM': '378', 'SL': '232', 'SC': '248', 'KZ': '7', 'KY': '1', 'SG': '65', 'SE': '46', 'SD': '249', 'DO': '1', 'DM': '1', 'DJ': '253', 'DK': '45', 'DE': '49', 'YE': '967', 'DZ': '213', 'MK': '389', 'YT': '262', 'TZ': '255', 'LC': '1', 'LA': '856', 'TV': '688', 'TW': '886', 'TT': '1', 'TR': '90', 'LK': '94', 'LI': '423', 'TN': '216', 'TO': '676', 'LT': '370', 'LU': '352', 'LR': '231', 'LS': '266', 'TH': '66', 'TG': '228', 'TD': '235', 'TC': '1', 'LY': '218', 'VA': '39', 'AC': '247', 'VC': '1', 'AE': '971', 'VE': '58', 'AG': '1', 'VG': '1', 'AI': '1', 'VI': '1', 'IS': '354', 'IR': '98', 'AM': '374', 'IT': '39', 'VN': '84', 'AS': '1', 'AR': '54', 'AU': '61', 'AT': '43', 'IO': '246', 'IN': '91', 'AX': '358', 'AZ': '994', 'IE': '353', 'ID': '62', 'UA': '380', 'QA': '974'}

