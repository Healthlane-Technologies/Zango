import os
import re
import tempfile
import uuid

from collections import namedtuple

import requests

from django_tenants.models import DomainMixin, TenantMixin

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from zango.api.platform.tenancy.v1.utils import extract_zip_to_temp_dir
from zango.core.model_mixins import FullAuditMixin
from zango.core.storage_utils import ZFileField

from .schema import get_default_auth_config
from .tasks import initialize_workspace
from .utils import DATEFORMAT, DATETIMEFORMAT, TIMEZONES


Choice = namedtuple("Choice", ["value", "display"])

TYPES = [
    Choice("shared", "Shared"),
    Choice("app", "App"),
]

STATUSES = [
    Choice("staged", "Staged"),
    Choice("deployed", "Deployed"),
    Choice("suspended", "Suspended"),
    Choice("deleted", "Deleted"),
]

SQL_IDENTIFIER_RE = re.compile(r"^[_a-zA-Z][_a-zA-Z0-9]{4,30}$")
SQL_SCHEMA_NAME_RESERVED_RE = re.compile(r"^pg_", re.IGNORECASE)


def _is_valid_identifier(identifier):
    return bool(SQL_IDENTIFIER_RE.match(identifier))


def _is_valid_tenant_name(name):
    return _is_valid_identifier(name) and not SQL_SCHEMA_NAME_RESERVED_RE.match(name)


def _check_tenant_name(name):
    if not _is_valid_tenant_name(name):
        raise ValidationError("Invalid string used for the Tenant Name")


class TenantModel(TenantMixin, FullAuditMixin):
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

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(
        "Unique App Name",
        max_length=30,
        unique=True,
        help_text="Unique name of the Tenant",
    )
    description = models.TextField(
        max_length=200, blank=True, help_text="Short description of the Tenant"
    )
    tenant_type = models.CharField(
        "Tenant Type",
        max_length=20,
        choices=[(c.value, c.display) for c in TYPES],
        null=True,
    )
    status = models.CharField(
        "Tenant Status",
        max_length=50,
        choices=[(c.value, c.display) for c in STATUSES],
        default=STATUSES[1].value,
    )
    deployed_on = models.DateTimeField(null=True, blank=True)
    suspended_on = models.DateTimeField(null=True, blank=True)
    deleted_on = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(
        "Timezone", max_length=255, null=True, blank=True, choices=TIMEZONES
    )
    language = models.CharField(
        "Langauge", max_length=50, null=True, blank=True, choices=settings.LANGUAGES
    )
    date_format = models.CharField(
        "Strf format for Date", max_length=25, choices=DATEFORMAT, null=True, blank=True
    )
    datetime_format = models.CharField(
        "Strf format for DateTime",
        max_length=25,
        choices=DATETIMEFORMAT,
        null=True,
        blank=True,
    )
    logo = ZFileField(verbose_name="Logo", null=True, blank=True)
    fav_icon = ZFileField(verbose_name="Fav Icon", null=True, blank=True)
    extra_config = models.JSONField(null=True, blank=True)
    app_template = ZFileField(
        verbose_name="template used for app", null=True, blank=True
    )
    auth_config = models.JSONField(default=get_default_auth_config)

    auto_create_schema = False

    def __str__(self):
        return self.name

    def suspend(self):
        self.status = "suspended"
        self.suspended_on = timezone.now()
        self.save()

    @classmethod
    def create(
        cls,
        name,
        schema_name,
        description,
        app_template_name,
        run_migrations=False,
        **other_params,
    ):
        _check_tenant_name(name)
        obj = cls.objects.create(
            name=name, schema_name=schema_name, description=description, **other_params
        )
        app_template_path = None
        if obj.app_template:
            if obj.app_template.url.startswith("https://"):
                downloaded_file_path = cls.download_file(obj.app_template.url)
            else:
                downloaded_file_path = obj.app_template
            app_template_path = os.path.join(
                extract_zip_to_temp_dir(downloaded_file_path), app_template_name
            )
        # initialize tenant's workspace
        init_task = initialize_workspace.delay(
            str(obj.uuid), app_template_path, run_migrations
        )
        return obj, init_task.id

    @staticmethod
    def download_file(url):
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            return temp_file.name


class Domain(DomainMixin, FullAuditMixin):
    """
    Model to store the details of Domains for the Tenants. Multiple
    domains can be created for each tenant
    """

    def __str__(self):
        return self.domain


class ThemesModel(FullAuditMixin):
    """
    Model to store the details of Themes for the Tenants. Multiple
    themes can be created for each tenant
    """

    name = models.CharField(max_length=50)
    tenant = models.ForeignKey(TenantModel, on_delete=models.PROTECT)
    config = models.JSONField(null=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

    def save(self, *args, **kwargs):
        # Get all other active themes with the same tenant
        themes_list = self.__class__.objects.filter(
            tenant=self.tenant, is_active=True
        ).exclude(pk=self.pk)
        # If we have no active theme yet, set as active theme by default
        self.is_active = self.is_active or (not themes_list.exists())
        if self.is_active:
            # Remove active status of existing domains for tenant
            themes_list.update(is_active=False)
        super().save(*args, **kwargs)
