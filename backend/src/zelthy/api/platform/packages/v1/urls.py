from django.urls import re_path, path, include

from .views import (
    ListAvailablePackagesAPIV1,    
)


urlpatterns = [
    re_path(
        r"^(?P<app_uuid>[\w-]+)/$",
        ListAvailablePackagesAPIV1.as_view(),
        name="packages-apiv1-listview",
    ),
]