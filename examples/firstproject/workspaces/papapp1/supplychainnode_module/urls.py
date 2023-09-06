from django.urls import re_path, path, include

from .views import SupplyChainNodesView


urlpatterns = [
    path("add_scn/", SupplyChainNodesView.as_view(), name="add_scn"),
    path("get_scn_details/", SupplyChainNodesView.as_view(), name="get_scn_details")
]
