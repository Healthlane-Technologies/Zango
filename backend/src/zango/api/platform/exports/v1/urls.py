from django.urls import path

from .views import (
    ExportJobCreateView,
    ExportJobDetailView,
    ExportJobDownloadView,
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
        "job/<uuid:job_uuid>/download/",
        ExportJobDownloadView.as_view(),
        name="exports-apiv1-download",
    ),
    path(
        "<str:kind>/",
        ExportJobCreateView.as_view(),
        name="exports-apiv1-create",
    ),
]
