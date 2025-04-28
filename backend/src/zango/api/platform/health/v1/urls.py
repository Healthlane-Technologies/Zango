from django.urls import re_path

from .views import HealthCheckAPIV1, stream_health


urlpatterns = [
    re_path(
        r"^stream/$",
        stream_health,
        name="healthcheck-stream",
    ),
    re_path(
        r"$",
        HealthCheckAPIV1.as_view(),
        name="healthcheck-apiv1",
    ),
]
