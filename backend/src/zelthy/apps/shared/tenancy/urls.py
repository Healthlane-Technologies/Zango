from django.urls import re_path

from .views import *


urlpatterns = [    
    re_path(
        r'^api/v1/launch-app/$', 
        AppaunchAppAPIV1.as_view(),
        name='apps-apiv1-launchapp'
    ),
    re_path(
        r'^api/v1/app/(?P<app_uuid>[\w-]+)/$', 
        AppDetailViewAPIV1.as_view(),
        name='apps-apiv1-appdetailview'
    ),
    

]
