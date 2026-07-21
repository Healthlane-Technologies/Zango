"""Template tags for Zango's copy of ``session_security/all.html``.

``django-session-security``'s own ``all.html`` renders its client timers from that
library's ``warn_after`` / ``expire_after`` filters, which return the platform-global
constants. Zango ships its own ``all.html`` (resolved ahead of the library's by our
filesystem template loader) that uses the tag below instead, so legacy, template-based
apps get per-app / per-role idle-timeout values with **no change to any workspace
template** -- they keep doing ``{% include 'session_security/all.html' %}``.

This library deliberately uses a Zango-owned name rather than shadowing
``session_security_tags``: overriding a third-party library's name depends on app
ordering and trips Django's templates.E003 duplicate-library check.

The tag runs inside the view/template render, where the tenant and user role are fully
resolved, so timing is exact per app and role. On the public schema (the platform app
panel) ``get_app_session_timeout`` returns the platform defaults.
"""

from django import template

from zango.core.utils import get_app_session_timeout


register = template.Library()


@register.simple_tag(takes_context=True)
def zango_session_security_config(context):
    """Return ``{"warn_after": int, "expire_after": int}`` for this request.

    Resolved per app (tenant) and user role, falling back to the platform
    ``SESSION_SECURITY_WARN_AFTER`` / ``SESSION_SECURITY_EXPIRE_AFTER``.
    """
    from django.db import connection

    request = context.get("request")
    warn_after, expire_after = get_app_session_timeout(request=request)
    return {
        "warn_after": warn_after,
        "expire_after": expire_after,
        "schema": connection.schema_name,
    }
