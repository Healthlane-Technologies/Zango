import json

from copy import deepcopy
from importlib import import_module
from typing import Any, Dict, Literal, Optional, Union

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


def has_view_feature(request, feature_name):
    """
    Check if a specific feature is enabled for the current view based on user's permissions.

    Features are automatically attached to the request during view permission checks
    by the DynamicView's PermissionMixin.has_perm() method.

    Args:
        request: HttpRequest object (must have view_features attached by permission check)
        feature_name (str): The feature to check (e.g., 'add', 'export', 'upload', 'delete')

    Returns:
        bool: True if the feature is enabled for the current user and view, False otherwise

    Note:
        Features must be defined in the policies.json file:
        ```json
        {
            "name": "backend.myapp.views.MyView",
            "type": "view",
            "features": ["add", "export", "upload"]
        }
        ```
    """
    view_features = getattr(request, "view_features", set())
    return feature_name in view_features


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


def get_datetime_in_current_timezone(datetime_val, tenant):
    """
    Convert datetime to currently activated timezone.
    Priority: X-Client-Timezone header (from request) > task timezone (from connection) > tenant timezone > settings.TIME_ZONE
    """
    from django.db import connection

    request = get_current_request()

    # Priority 1: Request timezone (set by middleware from X-Client-Timezone header)
    if request and hasattr(request, "tzname") and request.tzname:
        tzname = request.tzname
    # Priority 2: Task timezone (set on connection in task executor)
    elif hasattr(connection, "tzname") and connection.tzname:
        tzname = connection.tzname
    # Priority 3: Tenant timezone
    elif tenant.timezone:
        tzname = tenant.timezone
    # Priority 4: Default timezone
    else:
        tzname = settings.TIME_ZONE

    tz = pytz.timezone(tzname)
    return datetime_val.astimezone(tz)


def get_datetime_str_in_current_timezone(datetime_val, tenant):
    """
    Convert datetime to currently activated timezone and format using tenant's format.
    Uses X-Client-Timezone header if set, otherwise tenant timezone.
    """
    datetime_val = get_datetime_in_current_timezone(datetime_val, tenant)
    return datetime_val.strftime(tenant.datetime_format or "%d %b %Y %I:%M %p")


def get_search_columns(request):
    search_columns = {}
    for key, value in request.GET.items():
        if key.startswith("search_"):
            search_columns[key.replace("search_", "")] = value
    return search_columns


def generate_lockout_response(request, credentials):
    from .api.utils import get_api_response

    cooloff_time = settings.AXES_COOLOFF_TIME

    if "/api/v1/appauth/" in request.path:
        cooloff_seconds = (
            int(cooloff_time.total_seconds())
            if hasattr(cooloff_time, "total_seconds")
            else cooloff_time
        )
        cooloff_minutes = cooloff_seconds // 60

        # Determine time unit for message
        if cooloff_seconds < 60:
            time_message = f"{cooloff_seconds} seconds"
        else:
            time_message = f"{cooloff_minutes} minutes"

        return get_api_response(
            success=False,
            response_content={
                "message": f"Account locked due to too many failed login attempts. Please try again after {time_message}.",
                "cooloff_time_seconds": cooloff_seconds,
                "cooloff_time_minutes": cooloff_minutes,
                "error_code": "ACCOUNT_LOCKED",
            },
            status=403,
        )

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


AuthLevel = Literal["user", "user_role", "tenant"]


def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries, with source values taking precedence.

    Args:
        target: The target dictionary to merge into
        source: The source dictionary to merge from

    Returns:
        A new dictionary with deeply merged values
    """
    result = deepcopy(target)

    for key, value in source.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def filter_user_auth_config(user_auth_config, user_role_auth_config):
    if user_auth_config.get("two_factor_auth", {}).get("required"):
        return user_auth_config
    if user_role_auth_config.get("two_factor_auth", {}).get("required"):
        if user_auth_config.get("two_factor_auth", {}):
            user_auth_config["two_factor_auth"]["required"] = True
        else:
            user_auth_config["two_factor_auth"] = {
                "required": True,
            }
    return user_auth_config


def filter_user_role_auth_config(user_role_auth_config, tenant_auth_config):
    if tenant_auth_config.get("two_factor_auth", {}).get("required"):
        if user_role_auth_config.get("two_factor_auth", {}):
            user_role_auth_config["two_factor_auth"]["required"] = True
        else:
            user_role_auth_config["two_factor_auth"] = {
                "required": True,
            }
    return user_role_auth_config


def get_auth_priority(
    config_key: Optional[str] = None,
    policy: Optional[str] = None,
    request: Any = None,
    user: Any = None,
    user_role: Any = None,
    tenant: Any = None,
) -> Dict[str, Dict[str, Any]] | Union[str, int, bool, float]:
    """
    Check authentication priority for a configuration key across user, role, and tenant levels.
    When policy is specified, merges the policy configurations across all levels.

    Args:
        config_key: The configuration key to check
        policy: Optional policy name to check within auth configs
        request: HTTP request object (auto-resolved if None)
        user: User object (auto-resolved from request if None)
        user_role: User role object (auto-resolved if None)
        tenant: Tenant object (auto-resolved from request if None)

    Returns:
        If policy is specified:
            - The merged policy configuration across all levels
        If policy is not specified:
            - The value of the configuration key from the first level that has it,
              or an empty string if not found at any level
    """

    from zango.apps.appauth.models import UserRoleModel
    from zango.apps.shared.tenancy.schema import DEFAULT_AUTH_CONFIG

    if request is None:
        request = get_current_request()
    if user is None:
        user = request.user if request else None
        if user and user.is_anonymous:
            from allauth.account.internal.stagekit import unstash_login

            login = unstash_login(request, peek=True)
            if login:
                user = login.user
            else:
                user = None
    if user_role is None:
        if getattr(request, "session", None):
            if request.session.get("role_id"):
                user_role = UserRoleModel.objects.get(id=request.session["role_id"])
        else:
            user_role = get_current_role()
        if user_role is None:
            try:
                if user and not user.is_anonymous:
                    roles = user.roles.filter(is_active=True)
                    if roles.count() == 1:
                        user_role = roles.first()
            except Exception:
                pass
    if tenant is None:
        tenant = request.tenant if request else None
    try:
        tenant_auth_config = (
            getattr(tenant, "auth_config", {}) if tenant else DEFAULT_AUTH_CONFIG
        )
    except Exception:
        tenant_auth_config = DEFAULT_AUTH_CONFIG
    user_role_auth_config = filter_user_role_auth_config(
        getattr(user_role, "auth_config", {}) if user_role else {}, tenant_auth_config
    )
    user_auth_config = filter_user_auth_config(
        getattr(user, "auth_config", {}) if user and not user.is_anonymous else {},
        user_role_auth_config,
    )

    from zango.apps.appauth.models import SAMLModel

    for saml in SAMLModel.objects.filter(is_active=True):
        if (
            not tenant_auth_config.get("login_methods", {})
            .get("sso", {})
            .get("providers")
        ):
            tenant_auth_config["login_methods"]["sso"]["providers"] = []
        tenant_auth_config["login_methods"]["sso"]["providers"].append(
            {"id": saml.id, "label": saml.label}
        )

    if not config_key and not policy:
        merged_policy = {}

        merged_policy = deep_merge(merged_policy, tenant_auth_config)
        merged_policy = deep_merge(merged_policy, user_role_auth_config)
        merged_policy = deep_merge(merged_policy, user_auth_config)
        return merged_policy

    if policy:
        merged_policy = {}

        tenant_policy = tenant_auth_config.get(policy, {})
        if tenant_policy:
            merged_policy = deep_merge(merged_policy, tenant_policy)
        user_role_policy = user_role_auth_config.get(policy, {})
        if user_role_policy:
            merged_policy = deep_merge(merged_policy, user_role_policy)
        user_policy = user_auth_config.get(policy, {})
        if user_policy:
            merged_policy = deep_merge(merged_policy, user_policy)
        return merged_policy
    else:
        auth_levels = [
            ("user", user_auth_config),
            ("user_role", user_role_auth_config),
            ("tenant", tenant_auth_config),
        ]

        for level, config in auth_levels:
            if config.get(config_key) is not None:
                return config.get(config_key)

        return ""


def mask_email(email):
    """Masks an email address, showing only the first and last character before the '@' and the domain."""
    if "@" not in email:
        return email

    parts = email.split("@")
    local_part = parts[0]
    domain_part = parts[1]

    if len(local_part) <= 2:
        masked_local = "*" * len(local_part)
    else:
        masked_local = local_part[0] + "*" * (len(local_part) - 2) + local_part[-1]

    return f"{masked_local}@{domain_part}"


def mask_phone_number(phone_number):
    """Masks a phone number, showing only the last four digits."""
    digits_only = "".join(filter(str.isdigit, phone_number))

    if len(digits_only) <= 4:
        return "*" * len(digits_only)
    else:
        return "*" * (len(digits_only) - 4) + digits_only[-4:]
