from django.urls import re_path, path, include

from .views import PatienView, PatientProgramView


urlpatterns = [
    path("add_patient/", PatienView.as_view(), name="add_patient"),
    path("get_patient_details/", PatienView.as_view(), name="get-patient-details"),

    path("add_patient_program/", PatientProgramView.as_view(), name="add_patient_program"),
    path("get_patient_parogram_details/", PatientProgramView.as_view(), name="get-patient-program-details"),
]