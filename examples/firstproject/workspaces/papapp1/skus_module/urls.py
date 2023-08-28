from django.urls import re_path, path, include

from .views import SkuView, SkuTypesView, OrderItemsView


urlpatterns = [
    path("add_sku/", SkuView.as_view(), name="add_sku"),
    path("get_sku_detials/", SkuView.as_view(), name="get_sku_detials"),

    path("add_sku_type/", SkuTypesView.as_view(), name="add_sku_type"),
    path("get_sku_type_detials/", SkuTypesView.as_view(), name="get_sku_type_detials"),

    path("add_order_item/", OrderItemsView.as_view(), name="add_order_item"),
    path("get_order_item_detials/", OrderItemsView.as_view(), name="get_order_item_detials"),
]
