# EXAMPLE (vendor_hub, module `vendors`). Rules: references/map/detail-views.md
# Only heroes with a detail_view get a ZasDetail; other entities use the package BaseDetail (drawer).
from ...packages.crud.detail.base import BaseDetail
from ..zas_core.detail import ZasDetail


class VendorDetail(ZasDetail, BaseDetail):
    zas_view = "vendor_360"

    class Meta:
        # EVERY field the 360 reads (header, facts, panels) - without Meta.fields the payload
        # carries only the table's columns and amounts render as "—"
        fields = ["id", "vendor_ref", "legal_name", "vendor_type", "category", "gstin", "pan", "email", "phone",
                  "city", "address", "payment_terms", "credit_limit", "risk_rating", "approved_on", "approved_by", "logo"]
