from django.urls import re_path, path, include

from .views import OrderView


urlpatterns = [
    path("add_order/", OrderView.as_view(), name="add_order"),
    path("get_order_details/", OrderView.as_view(), name="get-order-details")
]