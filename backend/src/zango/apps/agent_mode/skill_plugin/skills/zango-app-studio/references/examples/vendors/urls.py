# EXAMPLE (vendor_hub, module `vendors`). Paths = entity code with "-" (contracts §1); trailing slash; never "".
from django.urls import path

from .views import VendorContactCrudView, VendorCrudView, VendorDocumentCrudView

urlpatterns = [
    path("vendor/", VendorCrudView.as_view(), name="vendor"),
    path("vendor-contact/", VendorContactCrudView.as_view(), name="vendor_contact"),
    path("vendor-document/", VendorDocumentCrudView.as_view(), name="vendor_document"),
]
