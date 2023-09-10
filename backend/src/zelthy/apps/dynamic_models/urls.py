'''Defines which API URLs.'''
import os
from django.urls import re_path

from .views import *


urlpatterns = [
    re_path(
        r'^((?:[\w\-:.,]+/)*)$', 
        DynamicView.as_view(),
        name='dynamic-app'
    )
]