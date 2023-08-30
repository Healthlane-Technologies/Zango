from django.urls import re_path
from zelthy.core.urls import z_include


urlpatterns = [
    re_path(r'^mod1', z_include('module1.urls')),
    re_path(r'^mod2', z_include('module2.urls')),
    re_path(r'^pkg1', z_include('frame.urls')),
]

