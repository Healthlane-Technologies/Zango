# EXAMPLE (vendor_hub, module `vendors`). Rules: references/map/workflow.md
# Conditions and done hooks are NOT written here: ZasWorkflowMixin supplies
# <name>_condition / <name>_done from the spec (expressions generated, text → hooks.py).
from ...packages.workflow.base.engine import WorkflowBase
from ..zas_core.mixins import ZasWorkflowMixin
from .forms import (
    VendorApproveForm, VendorDocumentRejectForm, VendorHoldForm, VendorMsmeEnableForm, VendorRejectForm, VendorSendBackForm,
)
from .models import Vendor, VendorDocument


class VendorWorkflow(ZasWorkflowMixin, WorkflowBase):
    zas_entity = "vendor"

    # one entry per (spec transition × from status); a multi-from transition becomes <name>__<from>
    status_transitions = [
        {"name": "submit", "display_name": "Submit for Approval", "description": "", "from": "draft",
         "to": "pending_approval", "confirmation_message": "Submit this vendor for approval?",
         "roles": ["Procurement Executive"]},
        {"name": "approve", "display_name": "Approve", "description": "", "from": "pending_approval", "to": "approved",
         "form": VendorApproveForm, "roles": ["Procurement Manager"]},
        {"name": "reject", "display_name": "Reject", "description": "", "from": "pending_approval", "to": "rejected",
         "form": VendorRejectForm, "roles": ["Procurement Manager"]},
        {"name": "send_back", "display_name": "Send Back", "description": "", "from": "pending_approval", "to": "draft",
         "form": VendorSendBackForm, "roles": ["Procurement Manager"]},
        {"name": "hold", "display_name": "Put on Hold", "description": "", "from": "approved", "to": "on_hold",
         "form": VendorHoldForm, "roles": ["Procurement Manager"]},
        {"name": "release", "display_name": "Release Hold", "description": "", "from": "on_hold", "to": "approved",
         "confirmation_message": "Release the hold on this vendor?", "roles": ["Procurement Manager"]},
        # trigger: system → is_manual False; run from tasks.py via zas_core.mixins.run_system_transition
        {"name": "auto_expire", "display_name": "Expire Draft", "description": "", "from": "draft", "to": "rejected",
         "is_manual": False},
    ]

    tag_transitions = [
        {"name": "msme",
         "enabled": {"roles": ["Procurement Executive", "Procurement Manager"], "confirmation_message": "Mark as MSME?",
                     "form": VendorMsmeEnableForm},
         "disabled": {"roles": ["Procurement Manager"], "confirmation_message": "Remove MSME?"}},
        {"name": "preferred",
         "enabled": {"roles": ["Procurement Manager"], "confirmation_message": "Mark as preferred?"},
         "disabled": {"roles": ["Procurement Manager"], "confirmation_message": "Remove preferred?"}},
        # kyc_expiring is system: listed in Meta.tags, no tag_transitions entry (set by tasks.py)
    ]

    class Meta:
        model = Vendor
        on_create_status = "draft"
        # colour = spec tone mapped for the engine's white-text badge (references/map/workflow.md)
        statuses = {
            "draft": {"label": "Draft", "color": "gray"},
            "pending_approval": {"label": "Pending Approval", "color": "orange"},
            "approved": {"label": "Approved", "color": "green"},
            "on_hold": {"label": "On Hold", "color": "purple"},
            "rejected": {"label": "Rejected", "color": "red"},
        }
        tags = [("msme", "MSME"), ("preferred", "Preferred"), ("kyc_expiring", "KYC Expiring")]


class VendorDocumentWorkflow(ZasWorkflowMixin, WorkflowBase):
    zas_entity = "vendor_document"
    status_transitions = [
        {"name": "verify", "display_name": "Verify", "description": "", "from": "uploaded", "to": "verified",
         "confirmation_message": "Mark this document as verified?", "roles": ["Procurement Executive"]},
        {"name": "reject", "display_name": "Reject", "description": "", "from": "uploaded", "to": "rejected",
         "form": VendorDocumentRejectForm, "roles": ["Procurement Executive"]},
    ]

    class Meta:
        model = VendorDocument
        on_create_status = "uploaded"
        statuses = {
            "uploaded": {"label": "Uploaded", "color": "blue"},
            "verified": {"label": "Verified", "color": "green"},
            "rejected": {"label": "Rejected", "color": "red"},
        }
        tags = []
