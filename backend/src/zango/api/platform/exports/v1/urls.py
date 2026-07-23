from django.urls import path

from .views import (
    ExportJobCreateView,
    ExportJobDetailView,
    ExportJobListView,
)


urlpatterns = [
    path("", ExportJobListView.as_view(), name="exports-apiv1-list"),
    path(
        "job/<uuid:job_uuid>/",
        ExportJobDetailView.as_view(),
        name="exports-apiv1-detail",
    ),
    path(
        "<str:kind>/",
        ExportJobCreateView.as_view(),
        name="exports-apiv1-create",
    ),
]
