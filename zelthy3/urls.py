from django.urls import path, include
from django.urls import re_path
from .views import zelthy_dynamic_views


urlpatterns = [
    re_path(r'^', include('zelthy3.backend.apps.shared.platformauth.urls')),
    # path('your_app/', include('your_app.urls')),
    re_path(r'api/auth/', include('knox.urls')),
    re_path(r'^((?:[\w\-:.,]+/)*)$', zelthy_dynamic_views)
]
