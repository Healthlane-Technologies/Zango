import pytz

from django.db import connection
from django_tenants.utils import schema_context
from loguru import logger


__all__ = [
    "TIMEZONES",
    "DATEFORMAT",
    "DATETIMEFORMAT",
    "TenantSuspended",
    "assert_tenant_active",
]


class TenantSuspended(Exception):
    """Raised when a Celery task is invoked against a suspended tenant.

    Celery treats this as a task failure — the broker acknowledges the
    message and the failure is recorded. A future dispatch after the
    tenant is unsuspended runs normally.
    """


def assert_tenant_active(tenant=None):
    """Raise ``TenantSuspended`` if the (given or current-connection) tenant
    is suspended.

    Cheap — one attribute lookup, no DB roundtrip. Called from
    ``zango_task_executor`` and ``codexec_executor`` right after
    ``connection.set_tenant(...)`` so the two chokepoints where every
    tenant-scoped Celery task passes through catch a suspended tenant
    before any workspace code loads.
    """
    tenant = tenant or getattr(connection, "tenant", None)
    if tenant is not None and getattr(tenant, "status", None) == "suspended":
        logger.info(
            "Task skipped: tenant '{}' is suspended",
            getattr(tenant, "schema_name", "?"),
        )
        raise TenantSuspended(getattr(tenant, "schema_name", "?"))

TIMEZONES = [(tz, tz) for tz in pytz.all_timezones]

DATEFORMAT = (
    ("%d %b %Y", "04 Oct 2017"),
    ("%d %B %Y", "04 October 2017"),
    ("%d/%m/%Y", "04/10/2017"),
    ("%d/%m/%y", "04/10/17"),
    ("%m/%d/%y", "10/04/17"),
    ("%d/%m/%Y", "04/10/2017"),
)

DATETIMEFORMAT = (
    ("%d %b %Y %H:%M", "04 Oct 2017 13:48"),
    ("%d %b %Y %I:%M %p", "04 Oct 2017 01:48 PM"),
    ("%d %B %Y %H:%M", "04 October 2017 13:48"),
    ("%d %B %Y %I:%M %p", "04 October 2017 01:48 PM"),
    ("%d/%m/%Y %H:%M", "04/10/2017 13:48"),
    ("%d/%m/%y %I:%M %p", "04/10/17 01:48 PM"),
    ("%m/%d/%y %H:%M", "10/04/17 13:48"),
    ("%d/%m/%Y %I:%M %p", "04/10/2017 01:48 PM"),
)

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


def assign_policies_to_anonymous_user(schema_name):
    from zango.apps.appauth.models import UserRoleModel
    from zango.apps.permissions.models import PolicyModel

    with schema_context(schema_name):
        anonymous_users_role = UserRoleModel.objects.get(name="AnonymousUsers")
        anonymous_users_role.policies.add(
            PolicyModel.objects.get(name="AllowFromAnywhere")
        )
        anonymous_users_role.save()
