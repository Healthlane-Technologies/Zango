from django.urls import re_path

from .views import PackagesViewAPIV1


urlpatterns = [
    re_path(
        r"",
        PackagesViewAPIV1.as_view(),
        name="packages-apiv1-packageview",
    ),
]
