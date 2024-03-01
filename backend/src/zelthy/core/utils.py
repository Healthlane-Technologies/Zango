from importlib import import_module
import pytz
import json

from django.conf import settings


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
    with open(f"workspaces/{request.tenant.name}/settings.json", "r") as f:
        data = json.loads(f.read())
    for route in data["package_routes"]:
        if route["package"] == package_name:
            domain = request.tenant.domains.filter(is_primary=True).last()
            url = get_current_request_url(request, domain=domain)
            return f"{url}/{route['re_path'][1:]}{path}"
    return ""


def get_current_request_url(request, domain=None):
    # Determine the protocol (HTTP or HTTPS) based on the request's is_secure() method.
    if settings.ENV == "dev":
        protocol = "https" if request.is_secure() else "http"
    else:
        protocol = "https"

    # Get the hostname (domain) from the request.
    if not domain:
        domain = request.get_host()

    # Get the port from the request. Use the standard ports (80 for HTTP, 443 for HTTPS) as default.
    if settings.ENV == "dev":
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
    tz = pytz.timezone(tenant.timezone)
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
