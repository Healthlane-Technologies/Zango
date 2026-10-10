"""
Duplicate detection for validation.duplicate_check (called from ZasFormMixin.clean).

compare:
  exact       field values equal (case-sensitive; links by pk)
  normalised  equal after lower-casing and dropping spaces/punctuation
  fuzzy       bigram Dice similarity >= threshold (default 0.85) on the joined values
"""

import re

from . import access
from . import expr as zx
from . import records


def norm(v):
    if v is None:
        return ""
    if hasattr(v, "_meta"):
        return f"#{v.pk}"
    return re.sub(r"[^a-z0-9]", "", str(v).lower())


def dice(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if len(a) < 2 or len(b) < 2:
        return 0.0

    def grams(s):
        out = {}
        for i in range(len(s) - 1):
            g = s[i:i + 2]
            out[g] = out.get(g, 0) + 1
        return out

    A, B = grams(a), grams(b)
    hit = sum(min(c, B.get(g, 0)) for g, c in A.items())
    return 2 * hit / (len(a) + len(b) - 2)


MAX_SCAN = 5000


def find(entity_code, Model, values, rule, scope_ast=None, exclude_pk=None, request=None):
    """Return the first matching record or None. `values` maps match path -> new value."""
    match = rule.get("match") or []
    compare = rule.get("compare", "exact")
    qs = Model.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if scope_ast:
        qs = qs.filter(zx.to_q(scope_ast, Model, access.expr_ctx(request)))
    if any(values.get(m) in (None, "") for m in match):
        return None  # a rule only applies when every matched field has a value
    if compare == "exact":
        flt = {}
        for m in match:
            v = values.get(m)
            flt[m.replace(".", "__")] = v.pk if hasattr(v, "_meta") else v
        return qs.filter(**flt).first()
    # normalised / fuzzy: narrow by any exact-able link first, then compare in Python
    narrowed = qs
    for m in match:
        v = values.get(m)
        if hasattr(v, "_meta"):
            narrowed = narrowed.filter(**{m.replace(".", "__"): v.pk})
    threshold = float(rule.get("threshold", 0.85))
    target = [values.get(m) for m in match]
    for rec in narrowed.order_by("-modified_at")[:MAX_SCAN]:
        theirs = [records.value_of(rec, m) for m in match]
        if compare == "normalised":
            if all(norm(a) == norm(b) for a, b in zip(target, theirs)):
                return rec
        else:
            text_pairs = [(a, b) for a, b in zip(target, theirs) if not hasattr(a, "_meta")]
            links_ok = all(norm(a) == norm(b) for a, b in zip(target, theirs) if hasattr(a, "_meta"))
            if links_ok and text_pairs:
                score = dice(" ".join(str(a) for a, _ in text_pairs), " ".join(str(b) for _, b in text_pairs))
                if score >= threshold:
                    return rec
    return None
