'''Defines which API URLs.'''
from django.urls import path, re_path, include
from django.views.decorators.csrf import csrf_exempt

from .views import *
from .login import AppLoginSignupView, LoginSignupV2APIView

urlpatterns = [
    re_path(
        r'^login/', 
        AppUserLoginView.as_view(),
        name='app-login-view'
    ),
    re_path(
        r'^v2/login/(?P<role_id>\d+)/',
        AppLoginSignupView.as_view(),
        name='app-role-login-signup'
      ),
      re_path(
        r'^api/v2/login/(?P<role_id>\d+)/',
        LoginSignupV2APIView.as_view(),
        name='app-role-login-signup-api'
      ),
    # url(
    #     regex=r'^api/v1/login/', 
    #     view=UserLoginAPIV1.as_view(),
    #     name='api-v1-login'
    # ),
    # url(
    #     regex=r'^api/v1/login/', 
    #     view=AppUserLoginAPI.as_view(),
    #     name='api-v1-login'
    # ),
    # url(
    #     regex=r'^app/', 
    #     view=AppView.as_view(),
    #     name='app-view'
    # ),
    # url(
    #     regex=r'^api/v1/initializeapp/', 
    #     view=InitializeAppAPIV1.as_view(),
    #     name='api-v1-initializeapp'
    # ),
    # url(
    #     regex=r'^logout/', 
    #     view=AppLogoutView.as_view(),
    #     name='app-logout-view'
    # )

]