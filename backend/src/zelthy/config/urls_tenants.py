from django.urls import include
from django.urls import re_path, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    re_path(r"^", include("zelthy.apps.appauth.urls")),
    re_path(r"api/auth/", include("knox.urls")),
    re_path(r"api/", include("zelthy.api.app_auth.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
    re_path(r"^((?:[\w\-:.,]+/)*)$", include("zelthy.apps.dynamic_models.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
