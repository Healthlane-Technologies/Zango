#!/usr/bin/env python3
"""
Offline self-test of the backend runtime (zas_core) on plain Django + in-memory sqlite.
No Zango, no database server, no app needed.

    python3 selftest_runtime.py                      # tests <skill>/assets/backend/zas_core
    python3 selftest_runtime.py --workspace <ws>     # tests <ws>/backend/zas_core and checks its spec.json

Proves: the expression engine compiles to the same answer as a Django Q and as an in-memory
evaluate (status, tags, related paths, form values, and/or/not, emptiness), arithmetic computed
fields, sequence formats, duplicate matching, value paths, cell display formats. With
--workspace it also checks that backend/zas_core/spec.json is the current .zas/spec.resolved.json.
Workflow tables are minimal stand-ins with the same columns the engine reads.
Needs `pip install django` on the host (any 4.x/5.x).
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

MODELS = '''
import uuid
from django.db import models
class Base(models.Model):
    object_uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True); modified_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True; app_label = "app"
class City(Base):
    name = models.CharField(max_length=100)
    class Meta: app_label = "app"
class Vendor(Base):
    legal_name = models.CharField(max_length=200); gstin = models.CharField(max_length=15, null=True, blank=True)
    vendor_type = models.CharField(max_length=20, choices=[("manufacturer","M"),("service","S")])
    city = models.ForeignKey(City, null=True, on_delete=models.SET_NULL); credit_limit = models.DecimalField(max_digits=16, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True); start_date = models.DateField(null=True); end_date = models.DateField(null=True)
    class Meta: app_label = "app"
class PurchaseOrder(Base):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE); quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    class Meta: app_label = "app"
'''

WF_MODELS = '''
from django.db import models
class WorkflowTransaction(models.Model):
    obj_uuid = models.UUIDField(); transition_name = models.CharField(max_length=255)
    transition_type = models.CharField(max_length=20, default="status"); from_state = models.CharField(max_length=255)
    to_state = models.CharField(max_length=255); data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: app_label = "app"
class WorkflowState(models.Model):
    obj_uuid = models.UUIDField(); transaction = models.ForeignKey(WorkflowTransaction, on_delete=models.PROTECT)
    current_state = models.CharField(max_length=255, null=True)
    content_type = models.ForeignKey("contenttypes.ContentType", null=True, on_delete=models.SET_NULL)
    class Meta: app_label = "app"
'''

RUN = r'''
import sys, os, datetime, decimal, django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from django.conf import settings
settings.configure(INSTALLED_APPS=["django.contrib.contenttypes", "app"],
                   DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}, USE_TZ=True)
django.setup()
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from app.models import City, Vendor, PurchaseOrder
from app.packages.workflow.base.models import WorkflowTransaction, WorkflowState
with connection.schema_editor() as se:
    for m in (ContentType, City, Vendor, PurchaseOrder, WorkflowTransaction, WorkflowState):
        se.create_model(m)
from app.backend.zas_core import expr as zx, records as zr, dupes, spec as zs
zs.app = lambda: {"locale": "en-IN", "currency": "INR"}
pune = City.objects.create(name="Pune")
a = Vendor.objects.create(legal_name="Apex Industries", gstin="27AAPCA1234F1Z5", vendor_type="manufacturer", city=pune,
                          credit_limit=1000, start_date=datetime.date(2026, 1, 1), end_date=datetime.date(2026, 6, 1))
b = Vendor.objects.create(legal_name="Nova Supplies", gstin="", vendor_type="service", is_active=False)
def setstatus(o, s):
    t = WorkflowTransaction.objects.create(obj_uuid=o.object_uuid, transition_name="x", from_state="", to_state=s)
    WorkflowState.objects.create(obj_uuid=o.object_uuid, transaction=t, current_state=s, content_type=ContentType.objects.get_for_model(o))
def settag(o, tag, on):
    WorkflowTransaction.objects.create(obj_uuid=o.object_uuid, transition_name=tag, transition_type="tag", from_state="",
                                       to_state="enabled" if on else "disabled")
setstatus(a, "approved"); setstatus(b, "draft"); settag(a, "msme", True); settag(b, "msme", True); settag(b, "msme", False)
po = PurchaseOrder.objects.create(vendor=a, quantity=3, unit_price=12.5)
results = []
def check(name, good, detail=""):
    results.append(good)
    print(("PASS " if good else "FAIL ") + name + (("  " + str(detail)) if not good else ""))
cases = {
    "status == approved": {"Apex Industries"},
    "status not_in [rejected, draft]": {"Apex Industries"},
    "has_tag msme": {"Apex Industries"},
    "not has_tag msme": {"Nova Supplies"},
    "gstin is_set": {"Apex Industries"},
    "gstin is_empty": {"Nova Supplies"},
    "is_active is_false": {"Nova Supplies"},
    "vendor_type == manufacturer and city.name == 'Pune'": {"Apex Industries"},
    "end_date > start_date": {"Apex Industries"},
    "credit_limit >= 500 or vendor_type == service": {"Apex Industries", "Nova Supplies"},
    "(status == draft or status == approved) and not gstin is_set": {"Nova Supplies"},
}
for src, want in cases.items():
    ast = zx.parse(src)
    got = set(Vendor.objects.filter(zx.to_q(ast, Vendor)).values_list("legal_name", flat=True))
    ev = {v.legal_name for v in Vendor.objects.all() if zx.evaluate(ast, v)}
    check(f"expr {src}", got == want and ev == want, f"Q={got} evaluate={ev} want={want}")
r = PurchaseOrder.objects.filter(zx.to_q(zx.parse("vendor.status == approved"), PurchaseOrder)).count()
check("expr related status", r == 1, r)
f = PurchaseOrder.objects.filter(zx.to_q(zx.parse("vendor == form.vendor"), PurchaseOrder, {"form": {"vendor": a}})).count()
check("expr form value", f == 1, f)
from app.backend.zas_core.mixins import _FormRecord
ff = zx.parse("end_date > start_date")
fr = [zx.evaluate(ff, _FormRecord({"start_date": datetime.date(2026, 1, 1), "end_date": d}, model=Vendor))
      for d in (datetime.date(2026, 2, 1), datetime.date(2025, 12, 1))]
check("expr field vs field on a form record", fr == [True, False], fr)
v = zr.compute_arith(po, "quantity * unit_price")
check("computed quantity * unit_price", float(v) == 37.5, v)
s = zr.render_sequence("PO-{YY}-{00000}", 42, datetime.date(2026, 3, 1))
check("sequence format", s == "PO-26-00042", s)
check("dupes fuzzy + normalise", dupes.dice("Apex Industries", "Apex Industries Pvt") > 0.8 and dupes.norm("A-p ex") == "apex")
check("value_of paths", zr.value_of(a, "city.name") == "Pune" and zr.value_of(a, "status") == "approved")
d = (zr.display(decimal.Decimal("1234567.5"), "money"), zr.display(-950, "money"), zr.display(None, "money"),
     zr.display(datetime.date(2026, 10, 9), "date"), zr.display(12.345, "percent"))
check("display formats", d == ("₹12,34,567.50", "-₹950.00", "", "09 Oct 2026", "12.3%"), d)
# every module imports (zango.core.api is stubbed in the temp tree)
import importlib
for m in ("access", "app_user", "dupes", "mixins", "detail", "notify"):
    try:
        importlib.import_module(f"app.backend.zas_core.{m}")
        check(f"import zas_core.{m}", True)
    except Exception as e:
        check(f"import zas_core.{m}", False, repr(e))
# workflow mixin: a tag side the spec leaves out (or a system tag) must be refused
from app.backend.zas_core import mixins
ent = {"module": "m", "workflow": {"statuses": [{"code": "draft"}], "transitions": [], "tags": [
    {"code": "msme", "enable": {"roles": ["A"]}, "disable": None},
    {"code": "kyc", "system": True, "enable": None, "disable": None}]}}
zs.entity = lambda code: ent
class WF(mixins.ZasWorkflowMixin):
    zas_entity = "x"
w = WF()
miss = [w.msme_disabled_condition(None, None), w.kyc_enabled_condition(None, None), w.kyc_disabled_condition(None, None)]
check("tag side missing / system tag → condition False", miss == [False, False, False], miss)
try:
    w.msme_enabled_condition
    check("tag side present without condition → no condition method", False, "attribute exists")
except AttributeError:
    check("tag side present without condition → no condition method", True)
print("ALL OK" if all(results) else f"{results.count(False)} FAILED")
sys.exit(0 if all(results) else 1)
'''


def build(tmp, runtime):
    app = os.path.join(tmp, "app")
    for d in ("", "backend", "packages", "packages/workflow", "packages/workflow/base"):
        os.makedirs(os.path.join(app, d), exist_ok=True)
        open(os.path.join(app, d, "__init__.py"), "w").close()
    for d in ("zango", "zango/core"):  # stub: detail.py imports get_api_response at module load
        os.makedirs(os.path.join(tmp, d), exist_ok=True)
        open(os.path.join(tmp, d, "__init__.py"), "w").close()
    with open(os.path.join(tmp, "zango/core/api.py"), "w") as f:
        f.write("def get_api_response(success, response_content, status):\n    return {'success': success, 'response': response_content, 'status': status}\n")
    with open(os.path.join(app, "models.py"), "w") as f:
        f.write(MODELS)
    with open(os.path.join(app, "packages/workflow/base/models.py"), "w") as f:
        f.write(WF_MODELS)
    shutil.copytree(runtime, os.path.join(app, "backend", "zas_core"),
                    ignore=shutil.ignore_patterns("__pycache__", "spec.json", "migrations"))
    with open(os.path.join(tmp, "run.py"), "w") as f:
        f.write(RUN)


def spec_copy_check(ws):
    a = os.path.join(ws, ".zas", "spec.resolved.json")
    b = os.path.join(ws, "backend", "zas_core", "spec.json")
    if not os.path.exists(b):
        print(f"FAIL spec.json missing: cp {a} {b}")
        return False
    h = [hashlib.sha256(open(p, "rb").read()).hexdigest() for p in (a, b)]
    good = h[0] == h[1]
    print(("PASS " if good else "FAIL ") + "backend/zas_core/spec.json is the current .zas/spec.resolved.json"
          + ("" if good else f"  (re-copy: cp {a} {b})"))
    return good


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace")
    ap.add_argument("--runtime", help="zas_core dir to test (default: workspace copy, else the skill's assets)")
    a = ap.parse_args(argv)
    try:
        import django  # noqa: F401
    except ImportError:
        print("selftest_runtime needs Django on the host: pip install 'django>=4.2'", file=sys.stderr)
        return 2
    runtime = a.runtime or (os.path.join(a.workspace, "backend", "zas_core") if a.workspace
                            else os.path.join(HERE, "..", "assets", "backend", "zas_core"))
    if not os.path.isdir(runtime):
        print(f"no runtime at {runtime}", file=sys.stderr)
        return 2
    ok = True
    if a.workspace:
        ok &= spec_copy_check(a.workspace)
    with tempfile.TemporaryDirectory(prefix="zas_selftest_") as tmp:
        build(tmp, runtime)
        r = subprocess.run([sys.executable, os.path.join(tmp, "run.py")], cwd=tmp)
        ok &= r.returncode == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
