from django.urls import include
from django.urls import re_path
from .views import zelthy_dynamic_views


urlpatterns = [
    re_path(r'^', include('zelthy3.backend.apps.tenants.appauth.urls')),
    # path('your_app/', include('your_app.urls')),
    re_path(r'api/auth/', include('knox.urls')),
    # re_path(r'^((?:[\w\-:.,]+/)*)$', zelthy_dynamic_views)
    re_path(r'^((?:[\w\-:.,]+/)*)$', include('zelthy3.backend.apps.tenants.dynamic_models.urls'))
]
