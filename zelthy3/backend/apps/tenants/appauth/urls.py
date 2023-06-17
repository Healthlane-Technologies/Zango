'''Defines which API URLs.'''
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from .views import *


urlpatterns = [
    url(
        regex=r'^login/', 
        view=AppUserLoginView.as_view(),
        name='app-login-view'
    ),
    # url(
    #     regex=r'^api/v1/login/', 
    #     view=UserLoginAPIV1.as_view(),
    #     name='api-v1-login'
    # ),
    url(
        regex=r'^api/v1/login/', 
        view=AppUserLoginAPI.as_view(),
        name='api-v1-login'
    ),
    url(
        regex=r'^app/', 
        view=AppView.as_view(),
        name='app-view'
    ),
    url(
        regex=r'^api/v1/initializeapp/', 
        view=InitializeAppAPIV1.as_view(),
        name='api-v1-initializeapp'
    ),
    url(
        regex=r'^logout/', 
        view=AppLogoutView.as_view(),
        name='app-logout-view'
    )

]