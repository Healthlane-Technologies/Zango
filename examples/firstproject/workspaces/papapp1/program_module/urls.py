from django.urls import re_path, path, include

from .views import ProgramView


urlpatterns = [
    path("add_program/", ProgramView.as_view(), name="add_program"),
    path("get_program_detials/", ProgramView.as_view(), name="get_program_detials")
]
