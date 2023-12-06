import uuid
import os
from collections import namedtuple

import cookiecutter.main

from django.db import models
from django.utils import timezone
from django.conf import settings
from django_tenants.models import TenantMixin, DomainMixin

from zelthy.core.model_mixins import FullAuditMixin
from zelthy.core.storage_utils import RandomUniqueFileName, ZFileField
from zelthy.apps.permissions.models import PolicyModel
from zelthy.apps.appauth.models import UserRoleModel

from .utils import (
    TIMEZONES,
    DATEFORMAT,
    DATETIMEFORMAT,
    DEFAULT_THEME_CONFIG,
    assign_policies_to_anonymous_user
)

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

    def __str__(self):
        return self.name

    def suspend(self):
        self.status = "suspended"
        self.suspended_on = timezone.now()
        self.save()

    @classmethod
    def create(cls, name, schema_name, description, **other_params):
        obj = cls(
            name=name, schema_name=schema_name, description=description, **other_params
        ).save()
        # initialize tenant's workspace
        obj.initialize_workspace()
        return obj

    def initialize_workspace(self):
        # Create workspace Folder
        project_base_dir = settings.BASE_DIR

        workspace_dir = os.path.join(project_base_dir, "workspaces")
        if not os.path.exists(workspace_dir):
            os.makedirs(workspace_dir)

        if not os.path.exists(os.path.join(workspace_dir, self.name)): 
            # Creating app folder with the initial files
            template_directory = os.path.join(
                os.path.dirname(__file__), "workspace_folder_template"
            )
            cookiecutter_context = {"app_name": self.name}

            cookiecutter.main.cookiecutter(
                template_directory,
                extra_context=cookiecutter_context,
                output_dir=workspace_dir,
                no_input=True,
            )

        self.status = "deployed"
        self.save()
        assign_policies_to_anonymous_user(self.schema_name)
        theme = ThemesModel.objects.create(
            name="Default", tenant=self, config=DEFAULT_THEME_CONFIG
        )


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
