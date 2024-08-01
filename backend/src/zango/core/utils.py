from importlib import import_module
import pytz
import json

from django.conf import settings
from django.db import connection
from django.shortcuts import render


def get_current_request():
    from ..middleware.request import _request_local

    return getattr(_request_local, "current_request", None)


def get_current_role():
    from ..middleware.request import _request_local
    from django.apps import apps

    # model = apps.get_model('appauth', 'UserRoleModel')
    return getattr(_request_local, "user_role", None)
    # return model.objects.get(id=user_role_id)


def get_app_object():
    from ..middleware.request import _request_local

    return getattr(_request_local, "app_object", None)


def get_package_url(request, path, package_name):
    if not request:
        request = get_mock_request()
    with open(f"workspaces/{request.tenant.name}/settings.json", "r") as f:
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
