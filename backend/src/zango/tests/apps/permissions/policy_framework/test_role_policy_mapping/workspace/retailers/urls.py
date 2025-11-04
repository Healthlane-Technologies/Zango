from django.urls import path

from .views import DummyTestView, DynamicRetailerView


urlpatterns = [
    path("retailer/", DynamicRetailerView.as_view(), name="retailers"),
    path("dummy/", DummyTestView.as_view(), name="dummy"),
]
