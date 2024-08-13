from django.urls import path
from .views import DynamicTestView, DummyTestView

urlpatterns = [
    path("customer/", DynamicTestView.as_view(), name="customer"),
    path("dummy/", DummyTestView.as_view(), name="customer"),
]
