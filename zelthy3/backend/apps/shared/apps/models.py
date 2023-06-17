import os
import json
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import JSONField

from django_tenants.models import TenantMixin, DomainMixin

from zelthy3.backend.core.common_utils import get_client_ip
from zelthy3.backend.core.model_mixins import FullAuditMixin
# from backend.core.storage_utils import S3PrivateFileField, RandomUniqueFileName
from zelthy3.backend.core.storage_utils import RandomUniqueFileName


import pytz
TIMEZONES = [(tz, tz) for tz in pytz.all_timezones]

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

class AppModel(TenantMixin, FullAuditMixin):

  # auto_create_schema = False

  APP_TYPES = (
               ('shared', _('Shared')),
               ('tenant', _('Tenant')),
               )
  APP_STATUSES = (
                 ('staged', 'Staged'),
                 ('deployed', 'Deployed'),
                 ('suspended', 'Suspended'),
                 ('deleted', 'Deleted')
                 )
  uuid = models.UUIDField(
                          default=uuid.uuid4,
                          unique=True,
                          editable=False
                          )
  name = models.CharField(
            "Unique App Name",
            max_length=30,
            unique=True,
            help_text=_(
            'Unique name of the App'
              )
            )
  description = models.TextField(
            max_length=200,
            blank=True
            )
  category = models.CharField(
              "App Category",
              max_length=50,
              null=True,
              blank=True,
              )
  app_type = models.CharField(
                 _("App Type"),
                 max_length=20,
                 choices=APP_TYPES,
                 null=True
                 )
  status = models.CharField(
                _("Application Status"),
                max_length=50,
                choices=APP_STATUSES,
                default='deployed'
                )
  autodelete_days = models.IntegerField(
                _("Auto delete on days after suspension"),
                default=90
                )
  deployed_on = models.DateTimeField(
                                  null=True,
                                  blank=True
                                  ) 
  suspended_on = models.DateTimeField(
                                  null=True,
                                  blank=True
                                  ) 
  deleted_on = models.DateTimeField(
                                  null=True,
                                  blank=True
                                  ) 
  whitelist_ips = models.CharField(
                          "IPs to be Whitelisted",
                          blank=True,
                          max_length=255                          
                          )
  timezone = models.CharField(
                _("Timezone"),
                max_length=255,
                null=True,
                blank=True,
                choices=TIMEZONES
                )
  app_language = models.CharField(
                _("App Langauge"),
                max_length=50,
                null=True,
                blank=True,
                choices=settings.LANGUAGES
                )
  date_format = models.CharField(
                _("Strf format for Date"),
                max_length=25,
                choices=DATEFORMAT,
                null=True,
                blank=True
                )
  datetime_format = models.CharField(
                _("Strf format for DateTime"),
                max_length=25,
                choices=DATETIMEFORMAT,
                null=True,
                blank=True
                )
  logo = models.FileField(
        upload_to=RandomUniqueFileName,
        verbose_name=_("App Logo"),
        null=True,
        blank=True
        )

  app_config = JSONField(
        null=True,
        blank=True
        )


  def check_for_whitelisting(self, request):
    """
    return True if whitelisting check is passed
    """
    if not self.tenant_config.whitelist_ips:
      return True
    try:   
      whitelist_ips = self.tenant_config.whitelist_ips.replace(" ","").split(",")
      if get_client_ip(request) in whitelist_ips:
        return True
      return False
    except:
      return False

  def is_login_allowed(self, request):
    """ 
    To allow login for a request on a tenancy allow_login must be True and check_for_whitelisting should
    pass
    """
    if self.tenant_config.allow_login and self.check_for_whitelisting(request):
      return True
    return False

  def __str__(self):
    return self.name


class Domain(DomainMixin):
    pass