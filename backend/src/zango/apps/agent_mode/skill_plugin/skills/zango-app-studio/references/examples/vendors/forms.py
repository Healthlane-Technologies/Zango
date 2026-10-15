# EXAMPLE (vendor_hub, module `vendors`). Rules: references/map/forms.md
from django import forms

from ...packages.crud.form_fields import ModelField
from ...packages.crud.forms import BaseForm, BaseSimpleForm
from ..zas_core.mixins import ZasActionFormMixin, ZasFormMixin
from .models import RISK_RATING_CHOICES, Vendor, VendorContact, VendorDocument


# ───── vendor: create (form.create) ─────
class VendorForm(ZasFormMixin, BaseForm):
    zas_entity = "vendor"
    zas_form = "create"

    # one ModelField per form field; label/required/help/tooltip/pattern from the spec field
    legal_name = ModelField(label="Legal Name", required=True,
                            description="Exactly as on the GST certificate.", tooltip="Used on POs and payment advice.")
    vendor_type = ModelField(label="Vendor Type", required=True, sync_enabled=True)  # drives credit_limit.show_when
    category = ModelField(label="Category", required=True)  # limit_choices applied by ZasFormMixin
    gstin = ModelField(label="GSTIN", pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$",
                       pattern_msg="Enter a valid 15-character GSTIN.")
    pan = ModelField(label="PAN", pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$", pattern_msg="Enter a valid PAN.")
    logo = ModelField(label="Logo")
    email = ModelField(label="Email", required=True)
    phone = ModelField(label="Phone", required=True, pattern=r"^[6-9][0-9]{9}$", pattern_msg="10-digit mobile without +91.")
    city = ModelField(label="City")
    address = ModelField(label="Address")
    payment_terms = ModelField(label="Payment Terms")
    credit_limit = ModelField(label="Credit Limit", prefix="₹")  # show_when: vendor_type != service

    class Meta:
        model = Vendor
        title = "Add Vendor"
        layout = "drawer-half"
        # sections → rows in order (Company / Contact / Commercials); ZasFormMixin drops hidden fields from it
        order = [["legal_name", "vendor_type"], ["category", "gstin"], ["pan", "logo"],
                 ["email", "phone"], ["city", "address"], ["payment_terms", "credit_limit"]]
        success_message = "Vendor saved."


# ───── vendor: edit (form.edit: same_as create, readonly_when, editable_in) ─────
class VendorEditForm(VendorForm):
    zas_form = "edit"

    class Meta:
        model = Vendor
        title = "Edit Vendor"
        layout = "drawer-half"
        order = VendorForm.Meta.order
        success_message = "Vendor updated."


# ───── transition forms (workflow.transitions[].form) ─────
class VendorApproveForm(ZasActionFormMixin, BaseSimpleForm):
    zas_entity = "vendor"
    # risk_rating shares a name with a Vendor field → saved onto the vendor by ZasActionFormMixin
    risk_rating = forms.ChoiceField(label="Risk Rating", choices=RISK_RATING_CHOICES, required=True)
    approval_note = forms.CharField(label="Approval Note", required=False, widget=forms.Textarea)

    class Meta:
        title = "Approve"
        layout = "drawer-half"
        order = [["risk_rating"], ["approval_note"]]


class VendorRejectForm(ZasActionFormMixin, BaseSimpleForm):
    zas_entity = "vendor"
    reject_reason = forms.CharField(label="Reject Reason", required=True, widget=forms.Textarea)

    class Meta:
        title = "Reject"
        layout = "drawer-half"
        order = [["reject_reason"]]


class VendorSendBackForm(ZasActionFormMixin, BaseSimpleForm):
    zas_entity = "vendor"
    send_back_reason = forms.CharField(label="Send Back Reason", required=True, widget=forms.Textarea)

    class Meta:
        title = "Send Back"
        order = [["send_back_reason"]]


class VendorHoldForm(ZasActionFormMixin, BaseSimpleForm):
    zas_entity = "vendor"
    hold_reason = forms.CharField(label="Hold Reason", required=True, widget=forms.Textarea)

    class Meta:
        title = "Put on Hold"
        order = [["hold_reason"]]


# ───── tag form (workflow.tags[].enable.form) ─────
class VendorMsmeEnableForm(ZasActionFormMixin, BaseSimpleForm):
    zas_entity = "vendor"
    msme_reg_no = forms.CharField(label="MSME Reg No", required=True)

    class Meta:
        title = "Mark as MSME"
        order = [["msme_reg_no"]]


# ───── row-action form (table.row_actions[type=form]): a ModelForm on the entity ─────
class VendorUpdateBankActionForm(ZasActionFormMixin, BaseForm):
    zas_entity = "vendor"
    account_no = forms.CharField(label="Account No", required=True)
    ifsc = forms.RegexField(label="IFSC", regex=r"^[A-Z]{4}0[A-Z0-9]{6}$", required=True)

    class Meta:
        model = Vendor
        title = "Update Bank Details"
        order = [["account_no"], ["ifsc"]]


# ───── child: contacts (parent FK preset + hidden on the 360 tab by ZasFormMixin) ─────
class VendorContactForm(ZasFormMixin, BaseForm):
    zas_entity = "vendor_contact"
    zas_form = "create"
    vendor = ModelField(label="Vendor", required=True)  # not in the spec form; needed on the list page
    name = ModelField(label="Name", required=True)
    designation = ModelField(label="Designation")
    email = ModelField(label="Email")
    phone = ModelField(label="Phone")
    is_primary = ModelField(label="Primary")

    class Meta:
        model = VendorContact
        title = "Add Contact"
        order = [["vendor"], ["name", "designation"], ["email", "phone"], ["is_primary"]]


class VendorContactEditForm(VendorContactForm):
    zas_form = "edit"

    class Meta:
        model = VendorContact
        title = "Edit Contact"
        order = VendorContactForm.Meta.order


class VendorDocumentForm(ZasFormMixin, BaseForm):
    zas_entity = "vendor_document"
    zas_form = "create"
    vendor = ModelField(label="Vendor", required=True)
    doc_type = ModelField(label="Document Type", required=True)
    file = ModelField(label="File", required=True, description="PDF, JPG or PNG, up to 10 MB.")
    expiry_date = ModelField(label="Expiry Date")

    class Meta:
        model = VendorDocument
        title = "Upload Document"
        order = [["vendor"], ["doc_type", "expiry_date"], ["file"]]

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if f and hasattr(f, "size"):
            ext = f.name.rsplit(".", 1)[-1].lower()
            if ext not in ("pdf", "jpg", "png"):
                raise forms.ValidationError("Upload a PDF, JPG or PNG file.")
            if f.size > 10 * 1024 * 1024:
                raise forms.ValidationError("The file must be 10 MB or smaller.")
        return f


class VendorDocumentRejectForm(ZasActionFormMixin, BaseSimpleForm):
    zas_entity = "vendor_document"
    reject_reason = forms.CharField(label="Reject Reason", required=True)

    class Meta:
        title = "Reject"
        order = [["reject_reason"]]
