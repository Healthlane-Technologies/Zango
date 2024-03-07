import uuid
from collections import namedtuple

from django.db import models
from django.utils import timezone
from django.conf import settings
from django_tenants.models import TenantMixin, DomainMixin

# from zelthy.core.model_mixins import FullAuditMixin
# from zelthy.core.storage_utils import RandomUniqueFileName



Choice = namedtuple('Choice', ['value', 'display'])

TYPES = [
    Choice('shared', 'Shared'),
    Choice('app', 'App'),
]

STATUSES = [
    Choice('staged', 'Staged'),
    Choice('deployed', 'Deployed'),
    Choice('suspended', 'Suspended'),
    Choice('deleted', 'Deleted')
]

import pytz

__all__ = [
    "TIMEZONES",
    "DATEFORMAT",
    "DATETIMEFORMAT",
]

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


class TenantModel(TenantMixin):
    """
    Model to store the details of Tenants in the system

    Attributes:
    - `uuid`: The unique identifier of the Tenant
    - `name`: The name of the Tenant. The tenants's codebase is stored at
    the location project_dir/workspaces/{name}/
    - `schema_name`: The name of the db schema_name of the Tenant. This
    attribute is defined in TenantMixin
    - `description`: Short description of the Tenant
    - `tenant_type`: The type of the Tenant -  Shared or App. Shared tenant is
    created on the public schema and only one such tenant can exist. Mutiple
    app Tenants can be created each representing a different application
    - `status`: The status of the Tenant - Staged, Deployed, Suspended or
    Deleted
    - `deleted_on`: The timestamp when the Tenant was deleted
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    name = models.CharField(
        "Unique App Name",
        max_length=30,
        unique=True,
        help_text='Unique name of the Tenant'
    )
    description = models.TextField(
        max_length=200,
        blank=True,
        help_text="Short description of the Tenant"
    )
    tenant_type = models.CharField(
        "Tenant Type",
        max_length=20,
        choices=[(c.value, c.display) for c in TYPES],
        null=True
    )
    status = models.CharField(
        "Tenant Status",
        max_length=50,
        choices=[(c.value, c.display) for c in STATUSES],
        default=STATUSES[1].value
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
    timezone = models.CharField(
        "Timezone",
        max_length=255,
        null=True,
        blank=True,
        choices=TIMEZONES
    )
    language = models.CharField(
        "Langauge",
        max_length=50,
        null=True,
        blank=True,
        choices=settings.LANGUAGES
    )
    date_format = models.CharField(
        "Strf format for Date",
        max_length=25,
        choices=DATEFORMAT,
        null=True,
        blank=True
    )
    datetime_format = models.CharField(
        "Strf format for DateTime",
        max_length=25,
        choices=DATETIMEFORMAT,
        null=True,
        blank=True
    )
    extra_config = models.JSONField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    def suspend(self):
        self.status = 'suspended'
        self.suspended_on = timezone.now()
        self.save()

    @classmethod
    def create(cls,
                name,
                schema_name,
                description, 
                **other_params
                ):
        obj = cls.objects.create(
            name=name,
            schema_name=schema_name,
            description=description,
            **other_params
        )
        # initialize tenant's workspace
        # obj.initialize_workspace()
        
class Domain(DomainMixin):
    """
    Model to store the details of Domains for the Tenants. Multiple
    domains can be created for each tenant
    """
    def __str__(self):
        return self.domain


class ThemesModel(models.Model):
    """
    Model to store the details of Themes for the Tenants. Multiple
    themes can be created for each tenant
    """
    name = models.CharField(
        max_length=50        
    )
    tenant = models.ForeignKey(
        TenantModel, 
        on_delete=models.PROTECT
    )
    config = models.JSONField(
        null=True
    )
    is_default = models.BooleanField(
        default=False
    )

    def __str__(self):
        return