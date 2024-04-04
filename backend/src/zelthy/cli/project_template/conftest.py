# conftest.py

import os
import pytest
from django.db import connection
from zelthy.apps.appauth.models import AppUserModel
from zelthy.apps.shared.tenancy.models import TenantModel, Domain
from django.core.management import call_command
from zelthy.apps.permissions.models import PolicyModel
from zelthy.apps.appauth.models import UserRoleModel
from django_tenants.utils import schema_context
import subprocess
from django.conf import settings
from zelthy.apps.shared.tenancy.templatetags.zstatic import zstatic

from zelthy.apps.dynamic_models.workspace.base import Workspace
from workspaces.test.packages.loginSignup.loginSignup.models import LoginSignupConfigModel

from django.test import RequestFactory
from django_tenants.test.client import TenantRequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

DEFAULT_THEME_CONFIG = {
    "color": {"primary": "#5048ED", "secondary": "#E1D6AE", "background": "#ffffff"},
    "button": {
        "color": "#ffffff",
        "background": "#5048ED",
        "border_color": "#C7CED3",
        "border_radius": "10",
    },
    "typography": {"font_family": "Open Sans"},
}

from django_tenants.utils import schema_context
from django.test import TestCase, Client
from django.conf import settings
from django_tenants.test.client import TenantRequestFactory


def pytest_addoption(parser):
    parser.addoption("--test", action="store", default="true", help="Description of your custom option")


@pytest.fixture(scope='session')
def tenant_django_db(django_db_setup, django_db_blocker):

    """
    Custom fixture to set up the database connection with a specific schema.
    """

    with django_db_blocker.unblock():

    
        from zelthy.apps.shared.tenancy.models import TenantModel, ThemesModel

        print(TenantModel.objects.all())

        obj = TenantModel.objects.create(
            name="test", 
            schema_name="test", 
            description="This is my NurseEducator schema",
            tenant_type="app"
        )

        Domain.objects.create(domain="testserver", tenant=obj)

        tenant_uuid = obj.uuid
        tenant = TenantModel.objects.get(uuid=tenant_uuid)

        # Creating schema
        tenant.create_schema(check_if_exists=True)

        # migrating schema

        tenant.status = "deployed"
        tenant.save()

        theme = ThemesModel.objects.create(
            name="Default", tenant=tenant, config=DEFAULT_THEME_CONFIG
        )

        connection.set_tenant(tenant)

        ws = Workspace(connection.tenant, request=None, as_systemuser=True)
        ws.ready()
        ws.sync_policies()

        factory = TenantRequestFactory(tenant=tenant)
        request = factory.get('/', tenant=tenant)

        # Add any attributes or methods you need for testing
        request.method = 'GET'
        request.path = '/example/path'
        request.tenant = tenant

    yield tenant, request
