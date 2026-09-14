"""
Utility functions for authentication flow checks and validations.
Centralizes common auth logic to avoid code duplication across views.
"""

import json

from django.db.models import Q
from django.http import HttpResponse

from zango.apps.appauth.models import AppUserModel


# ============================================================================
# User Fetching Utilities
# ============================================================================


def get_user_by_email(email):
    """
    Fetch user by email (case-insensitive).

    Args:
        email: str - User email address

    Returns:
        AppUserModel or None: User instance if found, None otherwise
    """
    try:
        return AppUserModel.objects.get(email__iexact=email)
    except AppUserModel.DoesNotExist:
        return None


def get_user_by_phone(phone):
    """
    Fetch user by phone number.

    Args:
        phone: str - User phone number

    Returns:
        AppUserModel or None: User instance if found, None otherwise
    """
    try:
        return AppUserModel.objects.get(mobile=phone)
    except AppUserModel.DoesNotExist:
        return None


def get_user_by_email_or_phone(identifier):
    """
    Fetch user by email or phone number.
    Attempts email first (case-insensitive), then phone.

    Args:
        identifier: str - Email or phone number

    Returns:
        AppUserModel or None: User instance if found, None otherwise
    """
    try:
        query = Q(email__iexact=identifier) | Q(mobile=identifier)
        return AppUserModel.objects.get(query)
    except AppUserModel.DoesNotExist:
        return None


def get_user_by_email_or_phone_with_query(email=None, phone=None):
    """
    Fetch user by email and/or phone number.
    At least one parameter must be provided.

    Args:
        email: str or None - User email address
        phone: str or None - User phone number

    Returns:
        AppUserModel or None: User instance if found, None otherwise
    """
    if not email and not phone:
        return None

    query = Q()
    if email:
        query = query | Q(email__iexact=email)
    if phone:
        query = query | Q(mobile=phone)

    try:
        return AppUserModel.objects.get(query)
    except AppUserModel.DoesNotExist:
        return None


# ============================================================================
# Permission and Status Check Utilities
# ============================================================================


def is_user_active(user):
    """
    Check if user account is active.

    Args:
        user: AppUserModel instance

    Returns:
        bool: True if user is active, False otherwise
    """
    return user.is_active


def is_sso_enforced_for_user(user):
    """
    Check if SSO is enforced for any of the user's roles.

    Args:
        user: AppUserModel instance

    Returns:
        bool: True if SSO is enforced for any role, False otherwise
    """
    return any(role.auth_config.get("enforce_sso", False) for role in user.roles.all())


# ============================================================================
# Error Response Utilities
# ============================================================================


def get_user_inactive_error_response():
    """
    Generate error response for inactive user account.

    Returns:
        HttpResponse: JSON error response with 400 status
    """
    resp = {
        "status": 400,
        "errors": [
            {
                "message": "Your account is currently inactive. Please reach out to support for assistance."
            }
        ],
    }
    return HttpResponse(json.dumps(resp), status=400)


def get_sso_enforcement_error_response(method_name="this authentication method"):
    """
    Generate a standardized error response for SSO enforcement violations.

    Args:
        method_name: str - Name of the authentication method being blocked

    Returns:
        HttpResponse: JSON error response with 400 status
    """
    resp = {
        "status": 400,
        "errors": [{"message": f"{method_name} cannot be used when SSO is enforced"}],
    }
    return HttpResponse(json.dumps(resp), status=400)


def get_user_not_found_error_response(message="User not found"):
    """
    Generate error response for user not found.

    Args:
        message: str - Custom error message

    Returns:
        HttpResponse: JSON error response with 400 status
    """
    resp = {
        "status": 400,
        "errors": [{"message": message}],
    }
    return HttpResponse(json.dumps(resp), status=400)


# ============================================================================
# Combined Check Utilities
# ============================================================================


def check_user_sso_enforcement(user, method_name="this authentication method"):
    """
    Check if SSO is enforced for a user and return error response if true.

    Args:
        user: AppUserModel instance
        method_name: str - Name of the authentication method being checked

    Returns:
        HttpResponse or None: Error response if SSO enforced, None otherwise
    """
    if is_sso_enforced_for_user(user):
        return get_sso_enforcement_error_response(method_name)
    return None


def check_user_status(user):
    """
    Check if user is active and return error response if not.

    Args:
        user: AppUserModel instance

    Returns:
        HttpResponse or None: Error response if user inactive, None otherwise
    """
    if not is_user_active(user):
        return get_user_inactive_error_response()
    return None


def validate_user_for_authentication(user, method_name="this authentication method"):
    """
    Perform comprehensive validation for user authentication.
    Checks: user is active, SSO not enforced.

    Args:
        user: AppUserModel instance
        method_name: str - Name of the authentication method being checked

    Returns:
        HttpResponse or None: Error response if validation fails, None otherwise
    """
    # Check if user is active
    status_error = check_user_status(user)
    if status_error:
        return status_error

    # Check if SSO is enforced
    sso_error = check_user_sso_enforcement(user, method_name)
    if sso_error:
        return sso_error

    return None
