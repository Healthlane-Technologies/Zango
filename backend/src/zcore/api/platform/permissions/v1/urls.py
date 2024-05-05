from django.urls import re_path

from .views import PolicyViewAPIV1, PolicyDetailViewAPIV1


urlpatterns = [
    re_path(
        r"^(?P<app_uuid>[\w-]+)/policies/$",
        PolicyViewAPIV1.as_view(),
        name="permissions-apiv1-policyview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/policies/(?P<policy_id>[\w-]+)/$",
        PolicyDetailViewAPIV1.as_view(),
        name="permissions-apiv1-policydetailview",
    ),
    re_path(
        r"^(?P<app_uuid>[\w-]+)/permissions/$",
        PolicyViewAPIV1.as_view(),
        name="permissions-apiv1-policyview",
    ),
]
