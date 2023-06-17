from django.conf.urls import url

from .views import *


urlpatterns = [    
    url(
        regex=r'^api/v1/launch-app/$', 
        view=AppaunchAppAPIV1.as_view(),
        name='apps-apiv1-launchapp'
    ),
    url(
        regex=r'^api/v1/app/(?P<app_uuid>[\w-]+)/$', 
        view=AppDetailViewAPIV1.as_view(),
        name='apps-apiv1-appdetailview'
    ),
    

]
