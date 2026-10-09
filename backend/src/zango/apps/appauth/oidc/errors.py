"""Error codes and redirects for OIDC sign-in.

Every rejection sends the browser back to the login page as
``/app/login/?sso=oidc&error=<code>&provider=<slug>``. The login page shows a
fixed message per code; details go to the access log, never to the page.
"""

import logging

from datetime import datetime

from allauth.core.exceptions import ImmediateHttpResponse
from axes.helpers import get_client_user_agent
from ipware import get_client_ip

from django.http import HttpResponseRedirect
from django.utils.http import urlencode


logger = logging.getLogger("zango.oidc")

LOGIN_PATH = "/app/login/"
SSO_ERROR_SESSION_KEY = "sso_error"

OIDC_DISABLED = "oidc_disabled"
PROVIDER_INACTIVE = "provider_inactive"
CANCELLED = "cancelled"
STATE_MISMATCH = "state_mismatch"
IDP_ERROR = "idp_error"
ID_TOKEN_INVALID = "id_token_invalid"
EMAIL_MISSING = "email_missing"
EMAIL_UNVERIFIED = "email_unverified"
DOMAIN_NOT_ALLOWED = "domain_not_allowed"
USER_NOT_FOUND = "user_not_found"
IDENTITY_CONFLICT = "identity_conflict"
USER_INACTIVE = "user_inactive"
NO_ACTIVE_ROLE = "no_active_role"

# Codes for which the login page may show the email the provider returned.
_EMAIL_VISIBLE = {USER_NOT_FOUND, DOMAIN_NOT_ALLOWED}


def login_url(**params):
    query = {"sso": "oidc", **{k: v for k, v in params.items() if v}}
    return f"{LOGIN_PATH}?{urlencode(query)}"


def log_failure(request, code, slug=None, email=None, detail=None):
    from zango.apps.accesslogs.models import AppAccessLog

    logger.warning(
        "OIDC sign-in rejected: code=%s provider=%s email=%s detail=%s",
        code,
        slug,
        email,
        detail,
    )
    try:
        client_ip, _ = get_client_ip(request)
        AppAccessLog.objects.create(
            ip_address=client_ip,
            http_accept=request.META.get("HTTP_ACCEPT", "<unknown>"),
            path_info=request.META.get("PATH_INFO", "<unknown>"),
            user_agent=get_client_user_agent(request),
            username=email or "",
            attempt_time=datetime.now(),
            attempt_type="oidc_login",
            is_login_successful=False,
        )
    except Exception:
        import traceback

        traceback.print_exc()


def error_response(request, code, slug=None, email=None, detail=None):
    log_failure(request, code, slug=slug, email=email, detail=detail)
    request.session[SSO_ERROR_SESSION_KEY] = {
        "code": code,
        "provider": slug,
        "email": email if code in _EMAIL_VISIBLE else None,
    }
    return HttpResponseRedirect(login_url(error=code, provider=slug))


def sso_error(request, code, slug=None, email=None, detail=None):
    return ImmediateHttpResponse(
        error_response(request, code, slug=slug, email=email, detail=detail)
    )
