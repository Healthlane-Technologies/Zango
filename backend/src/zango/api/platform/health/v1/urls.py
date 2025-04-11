from django.urls import re_path

from .views import HealthCheckAPIV1


urlpatterns = [
    re_path(
        r"$",
        HealthCheckAPIV1.as_view(),
        name="healthcheck-apiv1",
    )
]
