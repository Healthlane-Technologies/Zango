"""
zas_core.expr - the App Studio expression grammar.

One parser, three consumers:
  * scripts/spec_check.py  - lint (pure Python, no Django import at module load)
  * to_q(...)              - Django Q for querysets (rows, quick filters, limit_choices, stats)
  * evaluate(...)          - bool for one record (show_when, conditions, banners)

Grammar: see references/contracts.md section 7.

AST nodes are plain dicts so they can be JSON-dumped into spec.resolved.json:
  {"op": "and"|"or", "args": [...]}      {"op": "not", "arg": node}
  {"op": "cmp", "path": "a.b", "cmp": "==", "value": V}
  {"op": "in", "path": "a", "values": [V...], "neg": bool}
  {"op": "test", "path": "a", "test": "is_set"|"is_empty"|"is_true"|"is_false"}
  {"op": "has_tag", "tag": "code", "path": "" | "purchase_order"}
  {"op": "role", "cmp": "==", "role": "Finance"}
  {"op": "text", "text": "..."}          {"op": "const", "value": True}
  V = {"lit": x} | {"word": "w"} | {"path": "a.b"} | {"today": n} | {"user": "attr"|""}
A "word" is a bare identifier that is either a literal (choice value) or a field
on the same record (end_date > start_date). It is resolved against the model.
"""

import re

__all__ = [
    "ExprError", "parse", "parse_condition", "walk", "paths_of", "text_nodes",
    "to_q", "evaluate", "current_status", "current_tags",
]


class ExprError(ValueError):
    pass


# ───────────────────────────── tokenizer ─────────────────────────────

_TOKEN_RE = re.compile(
    r"""
    \s*(?:
      (?P<str>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
    | (?P<op>==|!=|>=|<=|>|<)
    | (?P<punct>[()\[\],])
    | (?P<num>-?\d+(?:\.\d+)?(?![\w.]))
    | (?P<word>[A-Za-z_][\w.]*(?:\[[^\]]*\])?(?:[+-]\d+)?)
    )""",
    re.VERBOSE,
)

_KEYWORDS = {"and", "or", "not", "in", "not_in", "is_set", "is_empty",
             "is_true", "is_false", "has_tag"}
_TESTS = {"is_set", "is_empty", "is_true", "is_false"}
_CMP = {"==", "!=", ">", ">=", "<", "<="}


def _tokenize(s):
    pos, out = 0, []
    s = s.strip()
    while pos < len(s):
        m = _TOKEN_RE.match(s, pos)
        if not m or m.end() == pos:
            raise ExprError(f"cannot read expression near: {s[pos:pos + 20]!r}")
        pos = m.end()
        kind = m.lastgroup
        val = m.group(kind)
        if kind == "str":
            out.append(("str", bytes(val[1:-1], "utf-8").decode("unicode_escape")))
        elif kind == "num":
            out.append(("num", float(val) if "." in val else int(val)))
        else:
            out.append((kind, val))
    return out


# ───────────────────────────── parser ─────────────────────────────

class _P:
    def __init__(self, toks, src):
        self.t, self.i, self.src = toks, 0, src

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else (None, None)

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def expect(self, kind, val=None):
        k, v = self.take()
        if k != kind or (val is not None and v != val):
            raise ExprError(f"expected {val or kind} in {self.src!r}")
        return v

    def is_word(self, w, k=0):
        kind, v = self.peek(k)
        return kind == "word" and v == w

    def parse(self):
        node = self.or_()
        if self.peek()[0] is not None:
            raise ExprError(f"unexpected {self.peek()[1]!r} in {self.src!r}")
        return node

    def or_(self):
        args = [self.and_()]
        while self.is_word("or"):
            self.take()
            args.append(self.and_())
        return args[0] if len(args) == 1 else {"op": "or", "args": args}

    def and_(self):
        args = [self.not_()]
        while self.is_word("and"):
            self.take()
            args.append(self.not_())
        return args[0] if len(args) == 1 else {"op": "and", "args": args}

    def not_(self):
        if self.is_word("not"):
            self.take()
            return {"op": "not", "arg": self.not_()}
        return self.atom()

    def atom(self):
        kind, v = self.peek()
        if kind == "punct" and v == "(":
            self.take()
            node = self.or_()
            self.expect("punct", ")")
            return node
        if kind == "word" and v == "has_tag":
            self.take()
            k2, tag = self.take()
            if k2 != "word":
                raise ExprError(f"has_tag needs a tag code in {self.src!r}")
            return {"op": "has_tag", "tag": tag, "path": ""}
        if kind != "word" or v in _KEYWORDS:
            raise ExprError(f"expected a field path, got {v!r} in {self.src!r}")
        self.take()
        path = v
        # path has_tag x  -> tag on a related record
        if self.is_word("has_tag"):
            self.take()
            _, tag = self.take()
            return {"op": "has_tag", "tag": tag, "path": path}
        k2, v2 = self.peek()
        if k2 == "word" and v2 in _TESTS:
            self.take()
            return {"op": "test", "path": path, "test": v2}
        if k2 == "word" and v2 in ("in", "not_in"):
            self.take()
            neg = v2 == "not_in"
            self.expect("punct", "[")
            vals = []
            if not (self.peek()[0] == "punct" and self.peek()[1] == "]"):
                vals.append(self.value())
                while self.peek() == ("punct", ","):
                    self.take()
                    vals.append(self.value())
            self.expect("punct", "]")
            return {"op": "in", "path": path, "values": vals, "neg": neg}
        if k2 == "word" and v2 == "not" and self.is_word("in", 1):
            self.take(); self.take()
            self.expect("punct", "[")
            vals = [self.value()]
            while self.peek() == ("punct", ","):
                self.take()
                vals.append(self.value())
            self.expect("punct", "]")
            return {"op": "in", "path": path, "values": vals, "neg": True}
        if k2 == "op":
            self.take()
            val = self.value()
            if path == "current_user.role":
                role = val.get("lit", val.get("word"))
                if v2 not in ("==", "!="):
                    raise ExprError("current_user.role supports only == and !=")
                return {"op": "role", "cmp": v2, "role": role}
            return {"op": "cmp", "path": path, "cmp": v2, "value": val}
        raise ExprError(f"{path!r} needs an operator in {self.src!r}")

    def value(self):
        kind, v = self.take()
        if kind == "str":
            return {"lit": v}
        if kind == "num":
            return {"lit": v}
        if kind == "word":
            low = v.lower()
            if low in ("true", "false"):
                return {"lit": low == "true"}
            if low in ("null", "none"):
                return {"lit": None}
            m = re.fullmatch(r"today([+-]\d+)?", v)
            if m:
                return {"today": int(m.group(1) or 0)}
            if v == "current_user" or v.startswith("current_user."):
                return {"user": v[len("current_user."):] if "." in v else ""}
            if "." in v:
                return {"path": v}
            return {"word": v}
        raise ExprError(f"expected a value, got {v!r}")


def parse(src):
    """Parse one expression string into an AST dict."""
    if not isinstance(src, str) or not src.strip():
        raise ExprError("empty expression")
    return _P(_tokenize(src), src).parse()


def parse_condition(node):
    """Parse a spec condition: a string, a list (= all), or {all|any|text}."""
    if node is None:
        return None
    if isinstance(node, bool):
        return {"op": "const", "value": node}
    if isinstance(node, str):
        return parse(node)
    if isinstance(node, list):
        args = [parse_condition(n) for n in node]
        return args[0] if len(args) == 1 else {"op": "and", "args": args}
    if isinstance(node, dict):
        if "all" in node or "any" in node:
            key = "all" if "all" in node else "any"
            args = [parse_condition(n) for n in (node.get(key) or [])]
            if node.get("text"):
                args.append({"op": "text", "text": node["text"]})
            return {"op": "and" if key == "all" else "or", "args": args}
        if "text" in node:
            return {"op": "text", "text": node["text"]}
    raise ExprError(f"cannot read condition {node!r}")


def walk(node):
    """Yield every node in the tree."""
    if not node:
        return
    yield node
    for a in node.get("args", []):
        yield from walk(a)
    if node.get("arg"):
        yield from walk(node["arg"])


def paths_of(node):
    """(path, kind) for every field reference, for linting."""
    out = []
    for n in walk(node):
        if n["op"] in ("cmp", "in", "test"):
            out.append((n["path"], "left"))
            vals = n.get("values") or ([n["value"]] if "value" in n else [])
            for v in vals:
                if "path" in v:
                    out.append((v["path"], "right"))
                if "word" in v:
                    out.append((v["word"], "word"))
        if n["op"] == "has_tag" and n.get("path"):
            out.append((n["path"], "left"))
    return out


def text_nodes(node):
    return [n["text"] for n in walk(node) if n["op"] == "text"]


# ───────────────────────────── runtime helpers ─────────────────────────────
# Everything below imports Django lazily so spec_check.py can import this file.

def _wf_models():
    from ...packages.workflow.base.models import WorkflowState, WorkflowTransaction
    return WorkflowState, WorkflowTransaction


def current_status(obj):
    """Current workflow status code of one record, or None."""
    WorkflowState, _ = _wf_models()
    ws = WorkflowState.objects.filter(obj_uuid=obj.object_uuid).first()
    return ws.current_state if ws else None


def current_tags(obj):
    """Set of enabled tag codes on one record."""
    _, WorkflowTransaction = _wf_models()
    latest = {}
    for name, to_state in (
        WorkflowTransaction.objects.filter(obj_uuid=obj.object_uuid, transition_type="tag")
        .order_by("id").values_list("transition_name", "to_state")
    ):
        latest[name] = to_state
    return {k for k, v in latest.items() if v == "enabled"}


def _today(n=0):
    import datetime
    try:
        from django.utils import timezone
        d = timezone.localdate()
    except Exception:
        d = datetime.date.today()
    return d + datetime.timedelta(days=n)


def _role_name(ctx):
    req = (ctx or {}).get("request")
    if req is not None and getattr(req, "_zas_role_name", None):
        return req._zas_role_name
    try:
        from zango.core.utils import get_current_role
        role = get_current_role()
        return role.name if role else None
    except Exception:
        return None


def _user_value(attr, ctx):
    req = (ctx or {}).get("request")
    user = getattr(req, "user", None)
    if not attr:
        return user
    if attr == "role":
        return _role_name(ctx)
    # current_user.<entity> -> the record bound through app_user (app_objects)
    resolver = (ctx or {}).get("user_record")
    if resolver:
        return resolver(attr)
    return getattr(user, attr, None)


def _model_field(model, path):
    """Return the final Django field for a dotted path, or None."""
    cur = model
    field = None
    for part in path.split("."):
        try:
            field = cur._meta.get_field(part)
        except Exception:
            return None
        cur = getattr(field, "related_model", None) or cur
    return field


def _is_text_field(field):
    return field is not None and field.get_internal_type() in ("CharField", "TextField", "EmailField", "URLField")


def _resolve_value(v, model, path, ctx):
    """Turn a value node into a Python value or an F() expression for to_q."""
    from django.db.models import F
    if "lit" in v:
        return v["lit"]
    if "today" in v:
        return _today(v["today"])
    if "user" in v:
        return _user_value(v["user"], ctx)
    if "path" in v:
        if v["path"].startswith("form."):
            return ((ctx or {}).get("form") or {}).get(v["path"][5:])
        return F(v["path"].replace(".", "__"))
    w = v["word"]
    left = _model_field(model, path) if model is not None and path else None
    if left is not None and getattr(left, "choices", None):
        return w
    if model is not None and _model_field(model, w) is not None:
        return F(w)
    return w


def _status_q(model, prefix, values, ctx):
    """Q for '<prefix>.status in values' via the workflow state table."""
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q
    WorkflowState, _ = _wf_models()
    target = model
    if prefix:
        for part in prefix.split("."):
            target = target._meta.get_field(part).related_model
    ct = ContentType.objects.get_for_model(target)
    uuids = WorkflowState.objects.filter(content_type=ct, current_state__in=list(values)).values("obj_uuid")
    lookup = (prefix.replace(".", "__") + "__" if prefix else "") + "object_uuid__in"
    return Q(**{lookup: uuids})


def _tag_q(model, prefix, tag):
    from django.db.models import Max, Q
    _, WorkflowTransaction = _wf_models()
    last_ids = (
        WorkflowTransaction.objects.filter(transition_type="tag", transition_name=tag)
        .values("obj_uuid").annotate(last=Max("id")).values_list("last", flat=True)
    )
    uuids = list(
        WorkflowTransaction.objects.filter(id__in=list(last_ids), to_state="enabled")
        .values_list("obj_uuid", flat=True)
    )
    lookup = (prefix.replace(".", "__") + "__" if prefix else "") + "object_uuid__in"
    return Q(**{lookup: uuids})


def _split_status(path):
    """'purchase_order.status' -> ('purchase_order', True); 'status' -> ('', True)."""
    if path == "status":
        return "", True
    if path.endswith(".status"):
        return path[: -len(".status")], True
    return path, False


_LOOKUP = {">": "gt", ">=": "gte", "<": "lt", "<=": "lte"}


def to_q(node, model, ctx=None):
    """Compile an AST to a Django Q against `model`.

    ctx: {"request": request, "form": {...}, "user_record": fn}
    text nodes raise: a plain-language condition must go through its hook.
    """
    from django.db.models import Q
    if node is None:
        return Q()
    op = node["op"]
    if op == "const":
        return Q() if node["value"] else Q(pk__in=[])
    if op == "and":
        q = Q()
        for a in node["args"]:
            q &= to_q(a, model, ctx)
        return q
    if op == "or":
        q = Q(pk__in=[])
        for a in node["args"]:
            q |= to_q(a, model, ctx)
        return q
    if op == "not":
        return ~to_q(node["arg"], model, ctx)
    if op == "text":
        raise ExprError("plain-language condition cannot run as a query; call its hook")
    if op == "role":
        ok = (_role_name(ctx) == node["role"]) == (node["cmp"] == "==")
        return Q() if ok else Q(pk__in=[])
    if op == "has_tag":
        return _tag_q(model, node.get("path", ""), node["tag"])

    path = node["path"]
    if path.startswith("form."):
        raise ExprError("form.* can only appear on the right-hand side of a query")
    prefix, is_status = _split_status(path)
    lk = path.replace(".", "__")
    field = _model_field(model, path) if not is_status else None

    if op == "test":
        t = node["test"]
        if t in ("is_true", "is_false"):
            return Q(**{lk: t == "is_true"})
        empty = Q(**{lk + "__isnull": True})
        if _is_text_field(field):
            empty |= Q(**{lk: ""})
        return ~empty if t == "is_set" else empty

    if op == "in":
        vals = [_resolve_value(v, model, path, ctx) for v in node["values"]]
        q = _status_q(model, prefix, vals, ctx) if is_status else Q(**{lk + "__in": vals})
        return ~q if node["neg"] else q

    if op == "cmp":
        val = _resolve_value(node["value"], model, path, ctx)
        c = node["cmp"]
        if is_status:
            q = _status_q(model, prefix, [val], ctx)
            return ~q if c == "!=" else q
        if c in ("==", "!="):
            q = Q(**{lk + "__isnull": True}) if val is None else Q(**{lk: val})
            return ~q if c == "!=" else q
        return Q(**{lk + "__" + _LOOKUP[c]: val})

    raise ExprError(f"unknown node {op}")


def _get_path(obj, path, ctx):
    if path.startswith("form."):
        return ((ctx or {}).get("form") or {}).get(path[5:])
    if path.startswith("current_user"):
        return _user_value(path[len("current_user."):] if "." in path else "", ctx)
    cur = obj
    parts = path.split(".")
    for i, part in enumerate(parts):
        if cur is None:
            return None
        if part == "status" and i == len(parts) - 1:
            fn = (ctx or {}).get("status_of", current_status)
            return fn(cur)
        if part == "tags" and i == len(parts) - 1:
            fn = (ctx or {}).get("tags_of", current_tags)
            return fn(cur)
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
    return cur


def _eval_value(v, obj, path, ctx):
    if "lit" in v:
        return v["lit"]
    if "today" in v:
        return _today(v["today"])
    if "user" in v:
        return _user_value(v["user"], ctx)
    if "path" in v:
        return _get_path(obj, v["path"], ctx)
    w = v["word"]
    left_model = getattr(obj, "_meta", None)
    if left_model is not None and path and not path.endswith("status"):
        try:
            f = obj._meta.get_field(path.split(".")[0])
            if getattr(f, "choices", None):
                return w
        except Exception:
            pass
    if left_model is not None:
        try:
            obj._meta.get_field(w)
            return getattr(obj, w)
        except Exception:
            pass
    return w


def _norm(x):
    """Compare model instances by pk, decimals with numbers, dates with strings."""
    import decimal
    if hasattr(x, "_meta") and hasattr(x, "pk"):
        return x.pk
    if isinstance(x, decimal.Decimal):
        return float(x)
    return x


def _cmp(a, c, b):
    a, b = _norm(a), _norm(b)
    if c == "==":
        return a == b or (a is not None and b is not None and str(a) == str(b))
    if c == "!=":
        return not _cmp(a, "==", b)
    if a is None or b is None:
        return False
    try:
        if c == ">":
            return a > b
        if c == ">=":
            return a >= b
        if c == "<":
            return a < b
        if c == "<=":
            return a <= b
    except TypeError:
        return False
    return False


def evaluate(node, obj, ctx=None):
    """Evaluate an AST against one record. ctx keys:
    request, form (dict), status_of(obj), tags_of(obj), text(node) -> bool, user_record(attr).
    A text node calls ctx["text"]; with no handler it counts as True (shown) so a
    missing hook never hides UI silently - the hook list in holes.md is the guard.
    """
    if node is None:
        return True
    op = node["op"]
    if op == "const":
        return bool(node["value"])
    if op == "and":
        return all(evaluate(a, obj, ctx) for a in node["args"])
    if op == "or":
        return any(evaluate(a, obj, ctx) for a in node["args"])
    if op == "not":
        return not evaluate(node["arg"], obj, ctx)
    if op == "text":
        fn = (ctx or {}).get("text")
        return bool(fn(node)) if fn else True
    if op == "role":
        return (_role_name(ctx) == node["role"]) == (node["cmp"] == "==")
    if op == "has_tag":
        target = _get_path(obj, node["path"], ctx) if node.get("path") else obj
        if target is None:
            return False
        fn = (ctx or {}).get("tags_of", current_tags)
        return node["tag"] in fn(target)
    path = node["path"]
    left = _get_path(obj, path, ctx)
    if op == "test":
        t = node["test"]
        if t == "is_true":
            return left is True or left in (1, "true", "True")
        if t == "is_false":
            return not left
        empty = left is None or left == ""
        if hasattr(left, "field") and hasattr(left, "name") and not hasattr(left, "_meta"):
            empty = not left.name  # FieldFile: an empty file field is falsy by name
        if isinstance(left, (list, tuple, set, dict)):
            empty = len(left) == 0
        return (not empty) if t == "is_set" else empty
    if op == "in":
        vals = [_eval_value(v, obj, path, ctx) for v in node["values"]]
        hit = any(_cmp(left, "==", v) for v in vals)
        return (not hit) if node["neg"] else hit
    if op == "cmp":
        return _cmp(left, node["cmp"], _eval_value(node["value"], obj, path, ctx))
    raise ExprError(f"unknown node {op}")
