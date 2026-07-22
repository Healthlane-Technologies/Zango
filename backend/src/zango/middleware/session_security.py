"""Per-app / per-role idle-session timeout enforcement.

``django-session-security``'s stock ``SessionSecurityMiddleware`` logs a user out
after a single, platform-global ``EXPIRE_AFTER`` (snapshotted from settings at
import time). This subclass overrides the ``get_expire_seconds(request)`` hook to
resolve the expiry per request from the app's / role's ``auth_config``
(``session_policy.session_expire_after``), falling back to the platform default.

This is the authoritative server-side logout for BOTH frontends (appbuilder React
and the legacy Django-template apps): when the session is idle past the resolved
expiry, the session is cleared, and the next ``/session_security/ping/`` returns
``"logout"`` — which both clients honour. Client JS cannot bypass it.

Only ``expire_after`` matters server-side; the warning is a purely client-side
timer fed separately (React config + legacy templatetag override).
"""

from session_security.middleware import (
    SessionSecurityMiddleware as _BaseSessionSecurityMiddleware,
)
from session_security.settings import PASSIVE_URL_NAMES, PASSIVE_URLS

from django.urls import Resolver404, resolve

from zango.core.utils import get_app_session_timeout


class SessionSecurityMiddleware(_BaseSessionSecurityMiddleware):
    """Resolve the idle-logout window per app/role instead of globally."""

    def is_passive_request(self, request):
        """Match ``PASSIVE_URL_NAMES`` against the request's own urlconf.

        The library resolves with a bare ``resolve(request.path)``, which always
        uses ``ROOT_URLCONF`` -- the *tenants* urlconf. ``django_tenants`` selects
        the public urlconf per request by setting ``request.urlconf``, so on the
        public schema (the platform app panel) the library resolves panel paths
        against the wrong urlconf: they miss their real view and fall through to
        the dynamic-app catch-all, yielding ``url_name='dynamic-app'``. No panel
        URL can then ever match a passive name, so polled endpoints reset the idle
        clock on every request and the user never goes idle.

        ``request.urlconf`` is unset on tenant schemas, so ``None`` reproduces the
        library's behaviour there exactly.
        """
        if request.path in PASSIVE_URLS:
            return True

        try:
            match = resolve(request.path, urlconf=getattr(request, "urlconf", None))
        except Resolver404:
            return False

        return match.url_name in PASSIVE_URL_NAMES

    def get_expire_seconds(self, request):
        try:
            _warn, expire = get_app_session_timeout(request=request)
            return expire
        except Exception:
            # Never let resolution failure break request processing; fall back
            # to the library's platform-global default.
            return super().get_expire_seconds(request)
