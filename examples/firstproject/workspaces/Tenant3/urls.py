# from django.urls import z_include
from django.urls import re_path
from zelthy.core.urls import z_include
# from .views import zelthy_dynamic_views


urlpatterns = [
    re_path(r'^mod1', z_include('module1.urls')),
    re_path(r'^mod2', z_include('module2.urls')),
    re_path(r'^pkg1', z_include('frame.urls')),
]

