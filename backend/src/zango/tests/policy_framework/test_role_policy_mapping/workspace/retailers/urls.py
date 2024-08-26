from django.urls import path
from .views import DynamicRetailerView,DummyTestView

urlpatterns = [
    path("retailer/", DynamicRetailerView.as_view(), name="retailers"),
    path("dummy/", DummyTestView.as_view(), name="dummy"),
]
