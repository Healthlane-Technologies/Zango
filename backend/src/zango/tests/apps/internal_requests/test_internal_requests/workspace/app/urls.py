from django.urls import path
from .views import TestAPIView, TestView

urlpatterns = [
    path("api/", TestAPIView.as_view(), name="customer"),
    path("view/", TestView.as_view(), name="dummy"),
]
