from django.urls import path
from .views import TestDynamicView, TestDummyView

urlpatterns = [
    path("customer/", TestDynamicView.as_view(), name="customer"),
    path("dummy/", TestDummyView.as_view(), name="dummy"),
]
