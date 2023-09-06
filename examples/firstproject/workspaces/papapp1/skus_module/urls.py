from django.urls import re_path, path, include

from .views import SkuView, SkuTypesView, OrderItemsView


urlpatterns = [
    path("add_sku/", SkuView.as_view(), name="add_sku"),
    path("get_sku_details/", SkuView.as_view(), name="get_sku_details"),

    path("add_sku_type/", SkuTypesView.as_view(), name="add_sku_type"),
    path("get_sku_type_details/", SkuTypesView.as_view(), name="get_sku_type_details"),

    path("add_order_item/", OrderItemsView.as_view(), name="add_order_item"),
    path("get_order_item_details/", OrderItemsView.as_view(), name="get_order_item_details"),
]
