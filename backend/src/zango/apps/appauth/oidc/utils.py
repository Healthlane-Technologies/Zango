from urllib.parse import urlparse

from zango.core.utils import get_auth_priority


# {"method": "oidc", "provider": <slug>, "id_token": <raw id_token>} for the
# session's current sign-in; read by the status and logout endpoints.
SSO_SESSION_KEY = "sso"
# Where to send the user once the OIDC sign-in completes.
NEXT_SESSION_KEY = "oidc_next"
DEFAULT_NEXT = "/app"


def oidc_enabled(request=None, tenant=None):
    login_methods = get_auth_priority(
        policy="login_methods", request=request, tenant=tenant
    )
    return bool((login_methods or {}).get("oidc", {}).get("enabled", False))


def public_providers():
    """Provider list for the login page. Never includes secrets or endpoints."""
    from zango.apps.appauth.models import OIDCProviderModel

    return [
        {"slug": p.slug, "label": p.label, "icon": p.icon}
        for p in OIDCProviderModel.objects.filter(is_active=True).order_by(
            "display_order", "id"
        )
    ]


def safe_next(value):
    """Accept only a same-origin relative path such as ``/app/batches/``."""
    if not isinstance(value, str) or not value.startswith("/"):
        return DEFAULT_NEXT
    if value.startswith("//") or "\\" in value:
        return DEFAULT_NEXT
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return DEFAULT_NEXT
    return value
