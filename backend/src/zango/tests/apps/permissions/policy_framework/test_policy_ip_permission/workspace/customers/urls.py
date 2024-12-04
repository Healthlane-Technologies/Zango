from django.urls import path
from .views import TestDynamicView, CIDRDynamicView, AllIPDynamicView

urlpatterns = [
    path("customer/", TestDynamicView.as_view(), name="customer"),
    path("cidr/", CIDRDynamicView.as_view(), name="cidr"),
    path("all-ip/", AllIPDynamicView.as_view(), name="all-ip"),
]
