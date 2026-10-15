# EXAMPLE (vendor_hub, module `vendors`) - scheduled items: system transitions, system tags,
# custom_requirements with area: scheduled. `zango_platform.py sync` registers each task, and
# `zango_platform.py schedule` sets the cron from its `# zas:schedule` line (references/zango/core/async-tasks.md).
import datetime

from celery import shared_task

from ..zas_core import expr as zx
from ..zas_core.mixins import run_system_transition, set_system_tag
from .models import Vendor, VendorDocument


# zas:hole H-07
# zas:schedule 0 1 * * *    (nightly 01:00)
@shared_task
def vendor__auto_expire__run():
    """Run nightly; a draft untouched for 90 days moves to rejected."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=90)
    moved = 0
    qs = Vendor.objects.filter(modified_at__lt=cutoff).filter(zx.to_q(zx.parse("status == draft"), Vendor))
    for v in qs:
        ok, _ = run_system_transition("vendor", v, "auto_expire")
        moved += bool(ok)
    return moved


# zas:hole H-08
# zas:schedule 0 7 * * *    (daily 07:00, same sweep as H-16)
@shared_task
def vendor__tag_kyc_expiring__sync():
    """Set when any verified vendor_document expires within 30 days; cleared on renewal."""
    soon = datetime.date.today() + datetime.timedelta(days=30)
    changed = 0
    for v in Vendor.objects.all():
        docs = VendorDocument.objects.filter(vendor=v, expiry_date__isnull=False)
        expiring = any(d.expiry_date <= soon and zx.current_status(d) == "verified" for d in docs)
        changed += set_system_tag("vendor", v, "kyc_expiring", expiring)
    return changed
