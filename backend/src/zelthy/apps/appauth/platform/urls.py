from django.conf.urls import url

from .views import *


urlpatterns = [
            url(
                regex=r'^api/v1/user-role/(?P<app_id>[\w-]+)/$', 
                view=UserRoleAPIV1.as_view(),
                name='api-v1-userrole'
            ),
        ]