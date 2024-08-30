from django.urls import path

from .views import AuditLogViewAPIV1


urlpatterns = [
    path(
        "",
        AuditLogViewAPIV1.as_view(),
        name="auditlog-apiv1-auditloglistview",
    ),
]
