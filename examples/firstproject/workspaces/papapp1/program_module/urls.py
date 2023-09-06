from django.urls import re_path, path, include

from .views import ProgramView, ProgramFormView


urlpatterns = [
    path("add_program/", ProgramView.as_view(), name="add_program"),
    path("get_program_details/", ProgramView.as_view(), name="get-program-details"),
    path("program_form/<int:id>/", ProgramFormView.as_view(), name="program_form")
]
