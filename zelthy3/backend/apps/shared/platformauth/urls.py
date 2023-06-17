from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from .views import *


urlpatterns = [
    url(
        regex=r'^login/', 
        view=PlatformUserLoginView.as_view(),
        name='platform-login'
    ),
    url(
        regex=r'^api/v1/login/', 
        view=PlatformUserLoginAPIV1.as_view(),
        name='platform-api-v1-login'
    ),
    # url(
    #     regex=r'^api/v1/register-user/', 
    #     view=PlatformUserRegisterAPIV1.as_view(),
    #     name='platform-api-v1-registeruser'
    # ),
    url(
        regex=r'^api/v1/profile/', 
        view=PlatformUserProfileAPIV1.as_view(),
        name='platform-api-v1-userprofile'
    )

]