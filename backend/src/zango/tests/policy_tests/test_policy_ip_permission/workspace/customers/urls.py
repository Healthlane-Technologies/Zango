from django.urls import path
from .views import TestDynamicView, CIDRDynamicView

urlpatterns = [
    path("customer/", TestDynamicView.as_view(), name="customer"),
    path("cidr/", CIDRDynamicView.as_view(), name="cidr"),
]
