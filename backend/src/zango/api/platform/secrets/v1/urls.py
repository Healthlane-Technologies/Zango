from django.urls import path

from .views import SecretsViewAPIV1


urlpatterns = [
    path("", SecretsViewAPIV1.as_view()),
]
