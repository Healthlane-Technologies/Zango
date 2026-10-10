# EXAMPLE (vendor_hub, module `vendors`). Rules: references/map/tables.md
# Scoping (rows), the 360 parent filter, quick filters, default sort and the row-action
# gates/handlers come from ZasTableMixin + spec.json. Only columns and actions are declared.
from ...packages.crud.table.base import ModelTable
from ...packages.crud.table.column import ModelCol, StatusCol, StringCol, TagsCol
from ..zas_core.mixins import ZasTableMixin
from . import hooks
from .detail import VendorDetail
from .forms import VendorContactEditForm, VendorEditForm, VendorUpdateBankActionForm
from .models import Vendor, VendorContact, VendorDocument


class VendorTable(ZasTableMixin, ModelTable):
    zas_entity = "vendor"
    pagination = 25                                                                   # table.page_size (class attr, not Meta)

    vendor_ref = ModelCol(display_as="Vendor ID", searchable=True, sortable=True)
    legal_name = ModelCol(display_as="Name", searchable=True, sortable=True)
    vendor_type = ModelCol(display_as="Type", searchable=True)                       # filterable → searchable
    category = ModelCol(display_as="Category", related_object_attribute="name", searchable=True)
    city = ModelCol(display_as="City", related_object_attribute="name", searchable=True, sortable=True)
    status = StatusCol(display_as="Status", searchable=True)
    tags = TagsCol(display_as="Tags")
    open_po_value = StringCol(display_as="Open PO value")                             # source: computed
    risk_rating = ModelCol(display_as="Risk", searchable=True, user_roles=["Procurement Manager"])
    created_at = ModelCol(display_as="Created", sortable=True)

    # crud row actions: edit/form → type "form" (+ form class); confirm/download/navigate/delete → "simple"
    # roles here = who sees it; show_when / editable_in are checked by ZasTableMixin.can_perform_row_action_<key>
    row_actions = [
        {"name": "Edit", "key": "edit", "description": "Edit vendor", "type": "form", "form": VendorEditForm,
         "roles": ["Procurement Executive", "Procurement Manager"]},
        {"name": "Open 360", "key": "open_360", "description": "Open the vendor page", "type": "simple"},
        {"name": "Resend Portal Invite", "key": "resend_invite", "description": "", "type": "simple",
         "confirmation_message": "Send a fresh login invite to this vendor's email?", "roles": ["Procurement Executive"]},
        {"name": "Update Bank Details", "key": "update_bank", "description": "", "type": "form",
         "form": VendorUpdateBankActionForm, "roles": ["Finance"]},
    ]

    def open_po_value_getval(self, obj):  # zas:hole H-11 (computed column → hooks.py)
        return hooks.vendor__col__open_po_value(obj)

    class Meta:
        model = Vendor
        fields = ["vendor_ref", "legal_name", "vendor_type", "category", "city", "risk_rating", "created_at"]
        detail_class = VendorDetail


class VendorContactTable(ZasTableMixin, ModelTable):
    zas_entity = "vendor_contact"

    name = ModelCol(display_as="Name", searchable=True)
    designation = ModelCol(display_as="Designation")
    email = ModelCol(display_as="Email")
    phone = ModelCol(display_as="Phone")
    is_primary = ModelCol(display_as="Primary")

    row_actions = [
        {"name": "Edit", "key": "edit", "description": "Edit contact", "type": "form", "form": VendorContactEditForm},
    ]

    class Meta:
        model = VendorContact
        fields = ["name", "designation", "email", "phone", "is_primary"]


class VendorDocumentTable(ZasTableMixin, ModelTable):
    zas_entity = "vendor_document"

    doc_type = ModelCol(display_as="Document", searchable=True)
    file = ModelCol(display_as="File")
    expiry_date = ModelCol(display_as="Expires", sortable=True)
    status = StatusCol(display_as="Status", searchable=True)
    created_at = ModelCol(display_as="Uploaded", sortable=True)

    row_actions = [
        {"name": "Preview", "key": "preview", "description": "Open the file", "type": "simple"},
    ]

    class Meta:
        model = VendorDocument
        fields = ["doc_type", "file", "expiry_date", "created_at"]
