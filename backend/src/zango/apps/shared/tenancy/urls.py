from django.urls import path, re_path

from .views import AppPanelView, CeleryStatusAPIView


urlpatterns = [
    path("celery-status/", CeleryStatusAPIView.as_view(), name="celery-status"),
    re_path(r"^", AppPanelView.as_view(), name="platform"),
]
