from django.urls import path, include
from django.urls import re_path
from .views import zelthy_dynamic_views


urlpatterns = [
    re_path(r'^((?:[\w\-:.,]+/)*)$', zelthy_dynamic_views)
]
