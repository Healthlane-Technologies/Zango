from django.urls import include
from django.urls import re_path
# from .views import zelthy_dynamic_views


urlpatterns = [
    re_path(r'^mod1', include('module1.urls')),
    re_path(r'^mod2', include('module2.urls')),
    re_path(r'^frame', include('frame.urls')),
]