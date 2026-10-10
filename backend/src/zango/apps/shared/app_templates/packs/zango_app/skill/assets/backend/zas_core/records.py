"""
Per-record helpers used from generated models.save() and from ZasDetail:

    apply_on_save(obj, entity_code)   sequences + arithmetic computed fields + computed hooks
    next_sequence(key, fmt)           "VEN-{00000}", "PO-{YY}-{00000}" (row-locked, gap-free)
    value_of(obj, path)               walk a dotted / reverse[filter] path
    field_value(E, obj, path)         {key, label, type, value, display, tone, url, uuid}
    interpolate(E, obj, template)     "{approved_on} by {approved_by.name}"
    display(value, fmt)               table cell text for a column `format` (money/percent/number/date/datetime/days)
"""

import ast
import datetime
import decimal
import logging
import operator
import re

from django.db import transaction

from . import expr as zx
from . import spec as zs

logger = logging.getLogger(__name__)


# ───────────────────────── sequences ─────────────────────────

def _period_key(fmt, today):
    if "{YYYY}" in fmt or "{YY}" in fmt:
        if "{MM}" in fmt:
            return today.strftime("%Y%m")
        return today.strftime("%Y")
    return ""


def render_sequence(fmt, n, today=None):
    today = today or datetime.date.today()
    out = fmt.replace("{YYYY}", today.strftime("%Y")).replace("{YY}", today.strftime("%y")).replace("{MM}", today.strftime("%m"))
    return re.sub(r"\{(0+)\}", lambda m: str(n).zfill(len(m.group(1))), out)


def next_sequence(key, fmt):
    """Increment the counter for key (per year when the format has {YY}/{YYYY})."""
    from .models import ZasSequence
    today = datetime.date.today()
    period = _period_key(fmt, today)
    full = f"{key}.{period}" if period else key
    with transaction.atomic():
        row, _ = ZasSequence.objects.select_for_update().get_or_create(key=full, defaults={"value": 0})
        row.value += 1
        row.save(update_fields=["value"])
        return render_sequence(fmt, row.value, today)


# ───────────────────────── computed (arithmetic) ─────────────────────────

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float, decimal.Decimal)):
        return decimal.Decimal(str(v))
    try:
        return decimal.Decimal(str(v))
    except Exception:
        return None


def compute_arith(obj, src):
    """Evaluate 'quantity * unit_price' (+ - * / numbers, dotted fields). None if any operand is None."""
    tree = ast.parse(src, mode="eval")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            a, b = ev(n.left), ev(n.right)
            if a is None or b is None:
                return None
            if isinstance(n.op, ast.Div) and b == 0:
                return None
            return _OPS[type(n.op)](a, b)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return decimal.Decimal(str(n.value))
        if isinstance(n, (ast.Name, ast.Attribute)):
            return _num(value_of(obj, ast.unparse(n)))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            v = ev(n.operand)
            return None if v is None else -v
        raise ValueError(f"unsupported computed expression: {src}")

    return ev(tree)


def apply_on_save(obj, entity_code):
    """Call from the generated model's save(), before super().save()."""
    E = zs.entity(entity_code)
    for f in E["fields"]:
        auto = f.get("auto") or {}
        if auto.get("sequence") and not getattr(obj, f["key"], None):
            setattr(obj, f["key"], next_sequence(f"{entity_code}.{f['key']}", auto["sequence"]))
        comp = f.get("computed")
        if comp and "expr" in comp:
            val = compute_arith(obj, comp["expr"])
            if val is not None and f["type"] in ("money", "decimal", "percent"):
                val = val.quantize(decimal.Decimal("0.01") if f["type"] != "percent" else decimal.Decimal("0.0001"))
            setattr(obj, f["key"], val)
        elif comp and "text" in comp:
            fn = f"{entity_code}__compute__{f['key']}"
            h = zs.hook(E["module"], fn)
            if h is not None:
                try:
                    setattr(obj, f["key"], h(obj))
                except Exception:
                    logger.exception("zas: computed hook %s failed", fn)


# ───────────────────────── values & display ─────────────────────────

_REV = re.compile(r"(\w+)\[(.*)\]")


def value_of(obj, path, ctx=None):
    """Walk 'city.name', 'status', 'vendor_contact[is_primary].name' from obj."""
    cur = obj
    parts = str(path).split(".")
    for i, part in enumerate(parts):
        if cur is None:
            return None
        m = _REV.fullmatch(part)
        if m:
            child_code, flt = m.group(1), m.group(2).strip()
            cur = _reverse_first(cur, child_code, flt, ctx)
            continue
        if part == "status" and i == len(parts) - 1 and hasattr(cur, "object_uuid"):
            return zx.current_status(cur)
        if part == "tags" and i == len(parts) - 1 and hasattr(cur, "object_uuid"):
            return sorted(zx.current_tags(cur))
        if part == "id":
            return getattr(cur, "pk", None)
        cur = getattr(cur, part, None)
    return cur


def _reverse_first(parent, child_code, flt, ctx):
    """First child record (child links to parent) matching flt."""
    try:
        C = zs.entity(child_code)
        Model = zs.model(child_code)
    except Exception:
        return None
    parent_code = _entity_code_of(parent)
    fk = next((f["key"] for f in C["fields"] if f["type"] == "link" and f.get("to") == parent_code), None)
    if not fk:
        return None
    qs = Model.objects.filter(**{fk: parent})
    try:
        node = zx.parse(flt)
    except zx.ExprError:
        node = zx.parse(flt + " is_true")
    try:
        return qs.filter(zx.to_q(node, Model, ctx or {})).order_by("-modified_at").first()
    except Exception:
        for rec in qs.order_by("-modified_at")[:200]:
            if zx.evaluate(node, rec, ctx or {}):
                return rec
    return None


def _entity_code_of(obj):
    name = obj.__class__.__name__
    for code, E in zs.entities().items():
        if E["names"]["model"] == name:
            return code
    return None


def _field_def(E, key):
    for f in E["fields"]:
        if f["key"] == key:
            return f
    return {"created_at": {"type": "datetime", "label": "Created"}, "modified_at": {"type": "datetime", "label": "Modified"},
            "created_by": {"type": "user", "label": "Created by"}, "modified_by": {"type": "user", "label": "Modified by"},
            "id": {"type": "integer", "label": "ID"}}.get(key)


def resolve_def(E, path):
    """(entity dict of the last hop, field def) for a dotted path."""
    cur = E
    parts = str(path).split(".")
    for i, part in enumerate(parts):
        m = _REV.fullmatch(part)
        if m:
            cur = zs.entity(m.group(1))
            continue
        if part == "status":
            return cur, {"key": "status", "type": "status", "label": "Status"}
        if part == "tags":
            return cur, {"key": "tags", "type": "tags", "label": "Tags"}
        f = _field_def(cur, part)
        if f is None:
            return cur, None
        if i < len(parts) - 1 and f.get("type") == "link" and f.get("to") in zs.entities():
            cur = zs.entity(f["to"])
            continue
        return cur, {**f, "key": f.get("key", part)}
    return cur, None


def _jsonable(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime, datetime.time)):
        return v.isoformat()
    if hasattr(v, "_meta"):
        return getattr(v, "pk", None)
    if hasattr(v, "url") and hasattr(v, "name"):
        return v.name or None
    if isinstance(v, (set, tuple)):
        return list(v)
    if hasattr(v, "as_e164"):  # phonenumber_field PhoneNumber
        return v.as_e164 if getattr(v, "is_valid", lambda: True)() else str(v)
    if v is not None and not isinstance(v, (str, int, float, bool, list, dict)):
        return str(v)
    return v


def _record_display(rec, E=None):
    if rec is None:
        return None
    if E and E.get("display") and E["display"] != "id":
        v = getattr(rec, E["display"], None)
        if v not in (None, ""):
            return str(v)
    if hasattr(rec, "name") and not callable(getattr(rec, "name")):
        return str(rec.name)
    return str(rec)


def field_value(E, obj, path, label=None, fmt=None):
    """Display-ready value for one field path (contracts §8 panels.fields[])."""
    owner, f = resolve_def(E, path)
    raw = value_of(obj, path)
    out = {"key": path, "label": label or (f or {}).get("label") or path.split(".")[-1].replace("_", " ").title(),
           "type": fmt or (f or {}).get("type") or "text", "value": None, "display": None, "tone": None}
    if raw is None or raw == "" or raw == []:
        return out
    t = (f or {}).get("type")
    if t == "status":
        st = next((s for s in (owner.get("workflow") or {}).get("statuses", []) if s["code"] == raw), None)
        out.update(value=raw, display=(st or {}).get("label", raw), tone=(st or {}).get("color"))
    elif t == "tags":
        tags = {tg["code"]: tg for tg in (owner.get("workflow") or {}).get("tags", [])}
        out.update(value=raw, display=", ".join(tags.get(c, {}).get("label", c) for c in raw),
                   items=[{"code": c, "label": tags.get(c, {}).get("label", c), "tone": tags.get(c, {}).get("color")} for c in raw])
    elif t in ("choice", "multi_choice"):
        ch = {str(c["id"]): c for c in f.get("choices") or []}
        vals = raw if isinstance(raw, list) else [raw]
        out.update(value=raw, display=", ".join(ch.get(str(v), {}).get("label", str(v)) for v in vals),
                   tone=ch.get(str(vals[0]), {}).get("color") if vals else None)
    elif t == "link" and hasattr(raw, "_meta"):
        T = zs.entities().get(f.get("to"))
        disp_attr = f.get("display")
        disp = str(getattr(raw, disp_attr)) if disp_attr and getattr(raw, disp_attr, None) is not None else _record_display(raw, T)
        out.update(value=getattr(raw, "pk", None), display=disp, uuid=str(getattr(raw, "object_uuid", "")) or None,
                   entity=f.get("to"))
    elif t == "user" or (t == "link" and f.get("to") == "app_user"):
        out.update(value=getattr(raw, "pk", None), display=getattr(raw, "name", None) or str(raw))
    elif t in ("file", "image"):
        name = getattr(raw, "name", None)
        if name:
            try:
                url = raw.url
            except Exception:
                url = None
            out.update(value=name, display=name.rsplit("/", 1)[-1], url=url)
    elif t == "boolean":
        out.update(value=bool(raw), display="Yes" if raw else "No")
    else:
        out.update(value=_jsonable(raw), display=str(_jsonable(raw)))
    return out


def interpolate(E, obj, template, txn_lookup=None):
    """'{approved_on} by {approved_by.name}' -> display text. Unknown → '—'."""
    def rep(m):
        path = m.group(1).strip()
        v = field_value(E, obj, path)
        if v["display"] is None and txn_lookup:
            t = txn_lookup(path)
            return str(t) if t not in (None, "") else "—"
        if v["display"] is None:
            return "—"
        if v["type"] == "date" and v["value"]:
            try:
                d = datetime.date.fromisoformat(str(v["value"])[:10])
                return d.strftime("%-d %b %Y")
            except Exception:
                pass
        return v["display"]
    return re.sub(r"\{([^}]+)\}", rep, str(template))


def latest_form_value(obj, key):
    """Value of `key` from the newest workflow transaction whose form collected it."""
    from ...packages.workflow.base.models import WorkflowTransaction
    for t in WorkflowTransaction.objects.filter(obj_uuid=obj.object_uuid).order_by("-id")[:50]:
        fd = (t.data or {}).get("form_data") or {}
        if key in fd and fd[key] not in (None, ""):
            return fd[key]
    return None


# ───────────────────────── display formats (table cells) ─────────────────────────

_SYMBOL = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "AED": "AED ", "SGD": "S$"}


def _group(n, decimals, locale):
    s = f"{abs(n):,.{decimals}f}"
    if str(locale or "").endswith("-IN"):  # lakh grouping: 12,34,567.00
        whole, _, frac = s.replace(",", "").partition(".")
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail]) + (f".{frac}" if frac else "")
    return ("-" if n < 0 else "") + s


def display(value, fmt=None):
    """Text for a table cell, matching the frontend formatters (config.ts) closely enough
    for list pages. None → "". Unknown format → str(value)."""
    if value is None or value == "":
        return ""
    app = zs.app() or {}
    locale, currency = app.get("locale"), app.get("currency") or "USD"
    try:
        if fmt == "money":
            n = _num(value)
            return ("-" if n < 0 else "") + _SYMBOL.get(currency, currency + " ") + _group(abs(n), 2, locale)
        if fmt == "percent":
            return f"{_num(value):.1f}%"
        if fmt == "number":
            n = _num(value)
            return _group(n, 0 if n == n.to_integral_value() else 2, locale)
        if fmt == "days":
            return f"{int(_num(value))} days"
        if fmt in ("date", "datetime"):
            if isinstance(value, str):
                value = datetime.datetime.fromisoformat(value)
            return value.strftime("%d %b %Y" if fmt == "date" else "%d %b %Y, %H:%M")
    except Exception:
        logger.debug("zas: display(%r, %r) fell back to str", value, fmt)
    return str(value)
