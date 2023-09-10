from django.urls import path, include
from django.urls import re_path
from django.contrib import admin


urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^api/", include("zelthy.api.platform.urls")),
    re_path(r"api/auth/", include("knox.urls")),
    re_path(r"^", include("zelthy.apps.shared.tenancy.urls")),
]
