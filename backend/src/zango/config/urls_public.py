from decorator_include import decorator_include

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path

from zango.core.decorators import internal_access_only


urlpatterns = [
    re_path(
        r"^auth/",
        decorator_include(internal_access_only, "zango.apps.shared.platformauth.urls"),
    ),
    re_path(
        r"^api/", decorator_include(internal_access_only, "zango.api.platform.urls")
    ),
    re_path(r"api/auth/", include("knox.urls")),
    re_path(r"session_security/", include("session_security.urls")),
    re_path(
        r"^platform/",
        decorator_include(internal_access_only, "zango.apps.shared.tenancy.urls"),
    ),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
