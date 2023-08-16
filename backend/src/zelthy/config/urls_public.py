from django.urls import path, include
from django.urls import re_path



urlpatterns = [
    re_path(r'^', include('zelthy.backend.apps.shared.platformauth.urls')),
    re_path(r'api/auth/', include('knox.urls'))
]
