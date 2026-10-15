# EXAMPLE (vendor_hub, module `vendors`) - hand-written logic for the spec's plain-language items.
# Every function: the exact name and signature from .zas/holes.md, the `# zas:hole H-NN` marker,
# one docstring line quoting the spec text. Generated code never overwrites this file.
import datetime
import logging

from django.db.models import Sum

from ..zas_core import app_user, notify
from ..zas_core import expr as zx
from .models import Vendor, VendorDocument

logger = logging.getLogger(__name__)


# zas:hole H-01
def vendor__submit__condition(request, obj):
    """At least one vendor_document of type gst_certificate is verified."""
    docs = VendorDocument.objects.filter(vendor=obj, doc_type="gst_certificate")
    return any(zx.current_status(d) == "verified" for d in docs)


# zas:hole H-03
def vendor__approve__condition(request, obj):
    """The approver must not be the user who created the vendor (maker-checker)."""
    user = getattr(request, "user", None)
    return not (obj.created_by_id and user is not None and obj.created_by_id == getattr(user, "id", None))


# zas:hole H-04
def vendor__approve__done(request, obj, form_data):
    """Copy risk_rating from the form, set approved_on/approved_by, then provision the Vendor User login."""
    # risk_rating was already written by ZasActionFormMixin (same-named field)
    obj.approved_on = datetime.date.today()
    obj.approved_by = getattr(request, "user", None) if getattr(getattr(request, "user", None), "pk", None) else None
    obj.save(update_fields=["approved_on", "approved_by"])
    app_user.provision(obj, "vendor", request)  # create_on: status == approved also triggers this; idempotent


# zas:hole H-05
def vendor__hold__done(request, obj, form_data):
    """Disable the Vendor User login and block new POs for this vendor."""
    app_user.set_active(obj, "vendor", False)
    # "block new POs": purchase_order.vendor.limit_choices already requires status == approved


# zas:hole H-06
def vendor__release__done(request, obj, form_data):
    """Re-enable the Vendor User login."""
    app_user.set_active(obj, "vendor", True)


# zas:hole H-11
def vendor__col__open_po_value(obj):
    """Sum of total_amount over this vendor's purchase orders not in [closed, cancelled]."""
    from ..procurement.models import PurchaseOrder  # later module: import inside the function (no import cycle)
    qs = PurchaseOrder.objects.filter(vendor=obj)
    qs = qs.filter(zx.to_q(zx.parse("status not_in [closed, cancelled]"), PurchaseOrder))
    total = qs.aggregate(v=Sum("total_amount"))["v"] or 0
    return float(total)


# zas:hole H-12
def vendor__action__resend_invite(request, obj, form_data):
    """Email the Vendor User a new invite link; old links stop working."""
    user = app_user.provision(obj, "vendor", request)
    if user is None:
        return {"message": "This vendor has no login yet."}
    notify.notify("vendor.invite", obj.email, subject="Your portal invite", body="…", vendor=str(obj.object_uuid))
    return {"message": "Invite sent."}
