'''Defines which API URLs.'''
from django.urls import path, re_path, include
from django.views.decorators.csrf import csrf_exempt

from .views import *

urlpatterns = [
    re_path(
        r'^', 
        DynamicView.as_view(),
        name='dynamic-app'
    )]