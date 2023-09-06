from django.urls import re_path, path, include

from .views import PatientView, PatientProgramView, PatientBenefitView


urlpatterns = [
    path("add_patient/", PatientView.as_view(), name="add_patient"),
    path("get_patient_details/", PatientView.as_view(), name="get-patient-details"),

    path("add_patient_program/", PatientProgramView.as_view(), name="add_patient_program"),
    path("get_patient_program_details/", PatientProgramView.as_view(), name="get-patient-program-details"),

    path("add_patient_benefit/", PatientBenefitView.as_view(), name="add_patient_benefit"),
    path("get_patient_benefit_details/", PatientBenefitView.as_view(), name="get-patient-benefit-details"),
]