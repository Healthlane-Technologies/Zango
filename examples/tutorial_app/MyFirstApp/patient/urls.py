from django.urls import path

from .views import PatientCrudView


urlpatterns = [
    path("patient/", PatientCrudView.as_view(), name="patient_crud"),
]
