from django.urls import path, include
from django.urls import re_path
from django.contrib import admin


urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^", include("zelthy.apps.shared.platformauth.urls")),
    re_path(r"^", include("zelthy.apps.shared.tenancy.urls")),
    re_path(r"api/auth/", include("knox.urls")),
]
