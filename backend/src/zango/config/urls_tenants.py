from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path


urlpatterns = [
    re_path(r"^", include("zango.apps.appauth.urls")),
    re_path(r"api/auth/", include("knox.urls")),
    re_path(r"api/", include("zango.api.app_auth.urls")),
    re_path(r"session_security/", include("session_security.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# include dynamic views
urlpatterns += [
    re_path(r"^((?:[\w\-:.,]+/)*)$", include("zango.apps.dynamic_models.urls")),
]
