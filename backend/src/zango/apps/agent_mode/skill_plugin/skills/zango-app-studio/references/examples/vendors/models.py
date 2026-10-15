# EXAMPLE (vendor_hub spec, module `vendors`) - the shape to emit, not code to copy blindly.
# Rules: references/map/models.md
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from zango.apps.appauth.models import AppUserModel
from zango.apps.dynamic_models.fields import ZForeignKey
from zango.apps.dynamic_models.models import DynamicModelBase
from zango.core.storage_utils import ZFileField

from ..masters.models import Category, City
from ..zas_core import records as zr

# choice sets used here (choice_sets.vendor_type / payment_terms / risk_rating)
VENDOR_TYPE_CHOICES = [("manufacturer", "Manufacturer"), ("distributor", "Distributor"), ("service", "Service Provider")]
PAYMENT_TERMS_CHOICES = [("advance", "Advance"), ("net_30", "Net 30"), ("net_60", "Net 60")]
RISK_RATING_CHOICES = [("low", "Low"), ("medium", "Medium"), ("high", "High")]
DOC_TYPE_CHOICES = [("gst_certificate", "GST Certificate"), ("pan_card", "PAN Card"),
                    ("cancelled_cheque", "Cancelled Cheque"), ("msme_certificate", "MSME Certificate")]


class Vendor(DynamicModelBase):
    # auto: {sequence: "VEN-{00000}"} -> filled by zr.apply_on_save; readonly, never on a form
    vendor_ref = models.CharField("Vendor ID", max_length=50, unique=True, null=True, blank=True)
    legal_name = models.CharField("Legal Name", max_length=200, help_text="Exactly as on the GST certificate.")
    vendor_type = models.CharField("Vendor Type", max_length=50, choices=VENDOR_TYPE_CHOICES)
    category = ZForeignKey(Category, on_delete=models.PROTECT, related_name="+")
    gstin = models.CharField("GSTIN", max_length=15, unique=True, null=True, blank=True)
    pan = models.CharField("PAN", max_length=10, null=True, blank=True)
    email = models.EmailField("Email", max_length=255)
    phone = PhoneNumberField("Phone")
    city = ZForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    address = models.TextField("Address", null=True, blank=True)
    payment_terms = models.CharField("Payment Terms", max_length=50, choices=PAYMENT_TERMS_CHOICES,
                                     default="net_30", null=True, blank=True)
    credit_limit = models.DecimalField("Credit Limit", max_digits=16, decimal_places=2, null=True, blank=True)
    risk_rating = models.CharField("Risk Rating", max_length=50, choices=RISK_RATING_CHOICES, null=True, blank=True)
    approved_on = models.DateField("Approved On", null=True, blank=True)
    approved_by = models.ForeignKey(AppUserModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    logo = ZFileField(null=True, blank=True)
    # NOTE: no `status` field - the workflow package owns status (workflow.py)

    def __str__(self):
        return self.legal_name or ""

    def save(self, *args, **kwargs):
        zr.apply_on_save(self, "vendor")  # sequences + computed fields from the spec
        super().save(*args, **kwargs)


class VendorContact(DynamicModelBase):
    vendor = ZForeignKey(Vendor, on_delete=models.CASCADE, related_name="+")
    name = models.CharField("Name", max_length=255)
    designation = models.CharField("Designation", max_length=255, null=True, blank=True)
    email = models.EmailField("Email", max_length=255, null=True, blank=True)
    phone = PhoneNumberField("Phone", null=True, blank=True)
    is_primary = models.BooleanField("Primary", default=False)

    def __str__(self):
        return self.name or ""

    def save(self, *args, **kwargs):
        zr.apply_on_save(self, "vendor_contact")
        super().save(*args, **kwargs)


class VendorDocument(DynamicModelBase):
    vendor = ZForeignKey(Vendor, on_delete=models.CASCADE, related_name="+")
    doc_type = models.CharField("Document Type", max_length=50, choices=DOC_TYPE_CHOICES)
    file = ZFileField()
    expiry_date = models.DateField("Expiry Date", null=True, blank=True)

    def __str__(self):
        return self.get_doc_type_display() or ""

    def save(self, *args, **kwargs):
        zr.apply_on_save(self, "vendor_document")
        super().save(*args, **kwargs)
