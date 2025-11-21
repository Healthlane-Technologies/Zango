from django.urls import path

from .views import AppCodebaseViewAPIV1

urlpatterns = [
    path("", AppCodebaseViewAPIV1.as_view()),
]