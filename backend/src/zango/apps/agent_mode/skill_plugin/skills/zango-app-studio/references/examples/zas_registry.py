"""
What zas_core looks up by entity code or module code. Generated: rewrite it whole on every build
from spec.resolved.json. One import line per class, plain relative imports, nothing else.
"""
from .vendors import hooks as vendors_hooks
from .vendors.models import Vendor, VendorContact, VendorDocument
from .vendors.workflow import VendorDocumentWorkflow, VendorWorkflow

# every entity code -> its model (entities.<code>.names.model)
MODELS = {
    "vendor": Vendor,
    "vendor_contact": VendorContact,
    "vendor_document": VendorDocument,
}

# every entity with a workflow -> its workflow class (entities.<code>.names.workflow)
WORKFLOWS = {
    "vendor": VendorWorkflow,
    "vendor_document": VendorDocumentWorkflow,
}

# every module code -> its hooks.py
HOOKS = {
    "vendors": vendors_hooks,
}
