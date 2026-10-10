# EXAMPLE (vendor_hub, module `vendors`). One BaseCrudView per entity; nothing hand-rolled.
from ...packages.crud.base import BaseCrudView
from ..zas_core.mixins import ZasCrudViewMixin
from .forms import VendorContactForm, VendorDocumentForm, VendorForm
from .models import Vendor, VendorContact, VendorDocument
from .tables import VendorContactTable, VendorDocumentTable, VendorTable
from .workflow import VendorDocumentWorkflow, VendorWorkflow


class VendorCrudView(ZasCrudViewMixin, BaseCrudView):
    zas_entity = "vendor"
    page_title = "Vendors"
    add_btn_title = "Add Vendor"
    model = Vendor
    form = VendorForm
    table = VendorTable
    workflow = VendorWorkflow


class VendorContactCrudView(ZasCrudViewMixin, BaseCrudView):
    zas_entity = "vendor_contact"
    page_title = "Contacts"
    add_btn_title = "Add Contact"
    model = VendorContact
    form = VendorContactForm
    table = VendorContactTable


class VendorDocumentCrudView(ZasCrudViewMixin, BaseCrudView):
    zas_entity = "vendor_document"
    page_title = "Documents"
    add_btn_title = "Upload Document"
    model = VendorDocument
    form = VendorDocumentForm
    table = VendorDocumentTable
    workflow = VendorDocumentWorkflow
