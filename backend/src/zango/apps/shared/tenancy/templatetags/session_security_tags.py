"""Override of ``django-session-security``'s ``session_security_tags`` library.

The stock ``session_security/all.html`` template (pulled in by legacy, non-appbuilder
apps via ``{% include 'session_security/all.html' %}``) renders its client timers from
the ``warn_after`` / ``expire_after`` template filters, which by default return the
platform-global ``WARN_AFTER`` / ``EXPIRE_AFTER`` constants.

Because ``zango.apps.shared.tenancy`` appears *after* ``session_security`` in
``INSTALLED_APPS``, Django's template-library registry resolves this module in place of
the library's own (later app wins for the same library name). That makes the legacy
frontend pick up per-app / per-role idle-timeout values with **no change to any
workspace template**.

Both filters receive ``request`` and run inside the view/template render, where the
user role is fully resolved — so warning/expiry timing is exact per app and role.
"""

from django import template

from zango.core.utils import get_app_session_timeout


register = template.Library()


@register.filter
def expire_after(request):
    """Seconds of inactivity before the session expires, per app/role."""
    _warn, expire = get_app_session_timeout(request=request)
    return expire


@register.filter
def warn_after(request):
    """Seconds of inactivity before the expiry warning is shown, per app/role."""
    warn, _expire = get_app_session_timeout(request=request)
    return warn
