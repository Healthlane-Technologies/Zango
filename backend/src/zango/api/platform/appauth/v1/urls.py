from django.urls import re_path

from .views import AuthConfigViewAPIV1


urlpatterns = [
    re_path(
        r"^tenants/(?P<app_uuid>[\w-]+)/$",
        AuthConfigViewAPIV1.as_view(),
        name="tenantauthconfig-apiv1-view",
    ),
]
