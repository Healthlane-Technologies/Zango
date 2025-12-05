from django.urls import path

from .views import AppAuthConfigViewAPIV1


urlpatterns = [
    path("", AppAuthConfigViewAPIV1.as_view(), name="app-auth-config"),
]
