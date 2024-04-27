from django.urls import path

from .views import AccessLogViewAPIV1

urlpatterns = [
    path(
        "",
        AccessLogViewAPIV1.as_view(),
        name="accesslog-apiv1-accessloglistview",
    ),
]
