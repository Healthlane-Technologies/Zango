import json

from importlib import import_module

import phonenumbers
import pytz

from phonenumbers.phonenumberutil import country_code_for_region

from django.conf import settings
from django.db import connection
from django.shortcuts import render


def get_current_request():
    from ..middleware.request import _request_local

    return getattr(_request_local, "current_request", None)


def get_current_role():
    from ..middleware.request import _request_local

    # model = apps.get_model('appauth', 'UserRoleModel')
    return getattr(_request_local, "user_role", None)
    # return model.objects.get(id=user_role_id)


def get_app_object():
    from ..middleware.request import _request_local

    return getattr(_request_local, "app_object", None)


def get_package_url(request, path, package_name):
    if not request:
        request = get_mock_request()
    with open(f"workspaces/{request.tenant.name}/settings.json") as f:
        data = json.loads(f.read())
    for route in data["package_routes"]:
        if route["package"] == package_name:
            domain = request.tenant.domains.filter(is_primary=True).last()
            url = get_current_request_url(request, domain=domain)
            return f"{url}/{route['re_path'][1:]}{path}"
    return ""


def get_mock_request(**kwargs):
    from django.db import connection
    from django.http import HttpRequest

    request = HttpRequest()
    request.path = kwargs.get("path")
    request.tenant = connection.tenant
    request.method = kwargs.get("method", "GET")
    request.META = kwargs.get("META", {})
    request.header = kwargs.get("header", {})

    if kwargs.get("session", False):
        session = kwargs.get("session")
        if session:
            request.session = session
        else:
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore()

    return request


def get_current_request_url(request, domain=None):
    # Determine the protocol (HTTP or HTTPS) based on the request's is_secure() method.
    secure = (
        request.headers.get("X-Forwarded-Proto") == "https"
        or request.META.get("HTTP_X_FORWARDED_PROTO") == "https"
    )
    if secure:
        protocol = "https"
    else:
        protocol = "http"

    # Get the hostname (domain) from the request.
    if not domain:
        domain = request.get_host()
    if not secure:
        port = request.META.get("SERVER_PORT", "")
        if (protocol == "http" and port == "80") or (
            protocol == "https" and port == "443"
        ):
            port_string = ""
        else:
            port_string = f":{port}"
    else:
        port_string = ""

    # Construct and return the complete URL.
    current_url = f"{protocol}://{domain}{port_string}"
    return current_url


def get_datetime_in_tenant_timezone(datetime_val, tenant):
    timezone = tenant.timezone
    if not tenant.timezone:
        timezone = settings.TIME_ZONE
    tz = pytz.timezone(timezone)
    return datetime_val.astimezone(tz)


def get_datetime_str_in_tenant_timezone(datetime_val, tenant):
    datetime_val = get_datetime_in_tenant_timezone(datetime_val, tenant)
    return datetime_val.strftime(tenant.datetime_format or "%d %b %Y %I:%M %p")


def get_search_columns(request):
    search_columns = {}
    for key, value in request.GET.items():
        if key.startswith("search_"):
            search_columns[key.replace("search_", "")] = value
    return search_columns


def generate_lockout_response(request, credentials):
    cooloff_time = settings.AXES_COOLOFF_TIME
    if connection.tenant.tenant_type == "app":
        return render(
            request,
            "core/error_pages/account_lockout.html",
            {"logout_url": "/logout", "cooloff_time": cooloff_time},
            status=403,
        )
    return render(
        request,
        "core/error_pages/account_lockout.html",
        {"logout_url": "/auth/logout", "cooloff_time": cooloff_time},
        status=403,
    )


def validate_phone(phone_number, region=None):
    """
    Validates a phone number by parsing it and checking if it is a valid phone number for the given region.

    Args:
        phone_number (str): The phone number to be validated.
        region (str, optional): The region in which the phone number is valid. Defaults to None.

    Returns:
        bool: True if the phone number is valid, False otherwise.

    Raises:
        None

    """
    try:
        region = region or settings.PHONENUMBER_DEFAULT_REGION
        phone_number = phonenumbers.parse(phone_number, region=region)
        if phonenumbers.is_valid_number(phone_number):
            return True
    except Exception:
        return False


def get_region_from_timezone(tzname):
    timezone_country = {}
    for countrycode in pytz.country_timezones:
        timezones = pytz.country_timezones[countrycode]
        for tz in timezones:
            timezone_country[tz] = countrycode
    return timezone_country[tzname]


def get_country_code_for_tenant(tenant, with_plus_sign=True):
    """
    Returns the country code for the given tenant.

    The region is first determined from the tenant's timezone. If no timezone is set,
    the default region from `settings.PHONENUMBER_DEFAULT_REGION` is used.

    Args:
        tenant: A TenantModel instance.
        with_plus_sign (bool): Whether to prepend a "+" to the country code. Default is True.

    Returns:
        str: The country code with or without "+" based on the region (e.g., "+1" for "US", "+91" for "IN").
    """
    default_region = settings.PHONENUMBER_DEFAULT_REGION

    if tenant.timezone:
        try:
            default_region = get_region_from_timezone(tenant.timezone)
        except Exception:
            pass

    country_code = country_code_for_region(default_region)
    return f"+{country_code}" if with_plus_sign else country_code


def get_app_secret(key=None, id=None):
    """
    Retrieves a secret from the database.

    Args:
        key (str, optional): The key of the secret to retrieve.
        id (int, optional): The ID of the secret to retrieve.

    Returns:
        str: The unencrypted value of the secret.

    Raises:
        ValueError: If the secret is not found or is inactive.
    """
    from zango.apps.secrets.models import SecretsModel

    if key and id:
        raise ValueError("Provide either 'key' or 'id', not both.")
    if not key and not id:
        raise ValueError("Either 'key' or 'id' must be provided.")

    sec = None
    try:
        if key:
            sec = SecretsModel.objects.get(key=key)
        if id:
            sec = SecretsModel.objects.get(id=id)
    except SecretsModel.DoesNotExist:
        raise ValueError(
            f"Secret not found for key={key}"
            if key
            else f"Secret not found for id={id}"
        )

    if not sec.is_active:
        raise ValueError(f"Secret {sec.key} is inactive.")

    return sec.get_unencrypted_val()
