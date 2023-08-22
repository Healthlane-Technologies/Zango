from django.urls import include
from django.urls import re_path

urlpatterns = [
    re_path(r'^', include('zelthy.apps.appauth.urls')),
    # path('your_app/', include('your_app.urls')),
    re_path(r'api/auth/', include('knox.urls')),
    # re_path(r'^((?:[\w\-:.,]+/)*)$', zelthy_dynamic_views)
    re_path(r'^((?:[\w\-:.,]+/)*)$', include('zelthy.apps.dynamic_models.urls'))
]
