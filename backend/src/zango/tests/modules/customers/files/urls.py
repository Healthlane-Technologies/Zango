from django.urls import path
from .views import TestDynamicView

urlpatterns = [
    path("customer/", TestDynamicView.as_view(), name="customer"),
]
