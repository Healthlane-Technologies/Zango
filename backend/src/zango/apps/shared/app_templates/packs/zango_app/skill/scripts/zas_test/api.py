"""
Layer 1: API tests generated from <ws>/.zas/spec.resolved.json, run against the live app as
each role's test user. The spec is the oracle: every check names the spec path it proves.

    python3 -m zas_test.api --workspace <ws> [--only access,create,…] [--role "Finance"] [--dry-run]

Groups (in run order):
  access       per entity × role: list endpoint answers for viewers, refuses others; Add refused without `add`
  create       per entity: a creator role creates a record (form schema → values); auto sequences filled;
               `require` validation rules and exact duplicate `block` rules refuse what they should
  transitions  per engine transition: allowed role moves the record to `to`; a viewer outside `roles` is refused
  tags         per tag side: allowed role toggles it; others refused; system tags refused for everyone
  row_actions  per row action: listed for allowed roles only; runs (no "not implemented"); download returns a url
  scoping      rows: {own} (bound login sees only its record, other records → not_found), {where: status …}
  detail       per 360 × role: viewers get zas.access ok, others no_access; each related tab lists the child
               created through it (parent param) and not another parent's; timeline answers

Records the tests need are created through the API by a role allowed to create them, and walked
through transitions to the statuses a test needs. When a transition's condition needs data the
generator cannot invent (a verified document, a matching PAN), write <ws>/.zas/test_fixtures.py:

    def values(ctx, entity, role[, params]):           -> dict   extra/override create values (params: the create URL params, e.g. a 360 parent)
    def before_transition(ctx, entity, name, uuid, role)          prepare data (create + verify a document …)
    def transition_values(ctx, entity, name, role)       -> dict   override transition form values
    def record_for(ctx, entity, role)                    -> uuid   the hero a role should open (bound logins)

`ctx` offers create(entity, role=None, values=None) -> uuid, run(entity, uuid, transition, role=None)
-> (ok, msg), session(role), record(entity, uuid, role=None) -> row dict.
Results: <ws>/.zas/test_results.json (layer "api"). Exit 1 when any check fails.
"""

import argparse
import datetime
import importlib.util
import io
import json
import os
import random
import re
import string
import sys
import traceback
from collections import deque

from . import auth, load_json, print_summary, save_results

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "assets", "backend"))
from zas_core import expr as zx  # noqa: E402  (pure Python at import time)

GROUPS = ["access", "create", "transitions", "tags", "row_actions", "scoping", "detail"]
NOT_IMPL = "is not implemented yet"
PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8ffff3f0005fe02fea7d6a5d80000000049454e44ae426082")
PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"


# ───────────────────────── values ─────────────────────────

def rnd(n=6):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def sample_regex(pattern):
    """A string matching a simple anchored regex: literals, escapes, [classes], \\d \\w, {n} {n,m} ? + *.
    Returns None for anything it cannot handle (alternation, lookarounds)."""
    p = pattern.strip("^$")
    if "|" in p or "(?" in p:
        return None
    out, i = [], 0

    def klass(body):
        chars, j, neg = [], 0, body.startswith("^")
        if neg:
            return None
        while j < len(body):
            if j + 2 < len(body) and body[j + 1] == "-":
                chars += [chr(c) for c in range(ord(body[j]), ord(body[j + 2]) + 1)]
                j += 3
            elif body[j] == "\\" and j + 1 < len(body):
                chars += {"d": list(string.digits), "w": list(string.ascii_letters + string.digits)}.get(body[j + 1], [body[j + 1]])
                j += 2
            else:
                chars.append(body[j])
                j += 1
        return chars

    while i < len(p):
        c = p[i]
        if c == "[":
            j = p.index("]", i)
            pool = klass(p[i + 1:j])
            if pool is None:
                return None
            i = j + 1
        elif c == "\\":
            pool = {"d": list(string.digits), "w": list(string.ascii_letters), "s": [" "]}.get(p[i + 1], [p[i + 1]])
            i += 2
        elif c == "(" or c == ")":
            i += 1
            continue
        elif c == ".":
            pool = list(string.ascii_letters)
            i += 1
        else:
            pool = [c]
            i += 1
        lo = hi = 1
        if i < len(p) and p[i] == "{":
            j = p.index("}", i)
            parts = p[i + 1:j].split(",")
            lo = int(parts[0])
            hi = int(parts[1]) if len(parts) > 1 and parts[1] else lo
            i = j + 1
        elif i < len(p) and p[i] in "?+*":
            lo, hi = {"?": (1, 1), "+": (1, 3), "*": (1, 2)}[p[i]]
            i += 1
        out += [random.choice(pool) for _ in range(random.randint(lo, hi))]
    s = "".join(out)
    return s if re.fullmatch(pattern.strip("^$"), s) else None


def value_for(f, prop, unique_tag):
    """(form value, file tuple or None) for one spec field, using the form schema's options."""
    t = f.get("type", "text")
    enum = prop.get("enum") or (prop.get("items") or {}).get("enum") or []
    if f.get("pattern"):
        v = sample_regex(f["pattern"])
        if v:
            return v, None
    if t in ("choice", "link", "multi_choice") or enum:
        if not enum:
            return None, None
        d = str(f.get("default")) if f.get("default") is not None else None
        v = d if d in enum else enum[0]
        return ([v] if t == "multi_choice" else v), None
    if t in ("file", "image"):
        acc = [a.lower().lstrip(".") for a in (f.get("accept") or [])]
        if t == "image" or (acc and "pdf" not in acc):
            return None, (f"zas_{unique_tag}.png", PNG, "image/png")
        return None, (f"zas_{unique_tag}.pdf", PDF, "application/pdf")
    today = datetime.date.today()
    if t == "date":
        return today.isoformat(), None
    if t == "datetime":
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), None
    if t == "time":
        return "10:00", None
    if t in ("integer",):
        return str(max(int(f.get("min") or 0), 1)), None
    if t in ("decimal", "money", "percent"):
        return str(max(float(f.get("min") or 0), 100.0 if t != "percent" else 10.0)), None
    if t == "boolean":
        return "true", None
    if t == "email":
        return f"zas.{unique_tag}@example.test", None
    if t == "phone":
        return "98" + "".join(random.choice(string.digits) for _ in range(8)), None
    if t == "url":
        return f"https://example.test/{unique_tag}", None
    if t == "json":
        return "{}", None
    if t == "long_text":
        return f"Generated by zas_test ({unique_tag}).", None
    mx = int(f.get("max_length") or 255)
    return f"Test {f.get('label') or f['key']} {unique_tag}"[:mx], None


# ───────────────────────── context ─────────────────────────

class Skip(Exception):
    pass


class Ctx:
    def __init__(self, ws, roles_filter=None):
        self.ws = ws
        self.M = load_json(ws, "spec.resolved.json")
        self.E = self.M["entities"]
        self.results = []
        self.sessions, self.login_errors = {}, {}
        self.roles_filter = roles_filter
        self.made = {}  # entity -> [uuid]
        self.fixtures = self._fixtures()

    # ----- plumbing -----
    def _fixtures(self):
        p = os.path.join(self.ws, ".zas", "test_fixtures.py")
        if not os.path.exists(p):
            return None
        spec = importlib.util.spec_from_file_location("zas_test_fixtures", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def login_all(self):
        roles = [r for r in self.M["roles"] if r not in ("AnonymousUsers", "SystemUsers")]
        self.sessions, self.login_errors = auth.sessions(self.ws, roles)

    def session(self, role):
        if role not in self.sessions:
            raise Skip(f"no logged-in test user for {role}: {self.login_errors.get(role, 'not in test_users.json')}")
        return self.sessions[role]

    def add(self, id, title, role, path, status, detail=""):
        self.results.append({"layer": "api", "id": id, "title": title, "role": role, "spec_path": path,
                             "status": status, "detail": str(detail)[:600]})

    def check(self, id, title, role, path, fn):
        if self.roles_filter and role and role not in self.roles_filter:
            return
        try:
            good, detail = fn()
            self.add(id, title, role, path, "pass" if good else "fail", detail if not good else "")
        except Skip as e:
            self.add(id, title, role, path, "skip", e)
        except Exception as e:  # a test crash is a failure, with the trace tail
            self.add(id, title, role, path, "fail", f"{e!r} {traceback.format_exc(limit=2)[-300:]}")

    # ----- spec helpers -----
    def ep(self, ent):
        return self.E[ent]["names"]["endpoint"]

    def acc(self, ent, role):
        E = self.E[ent]
        if not E.get("access"):
            return {"actions": ["view", "add", "edit", "delete", "export", "detail"], "rows": None}
        a = (E.get("access_resolved") or {}).get(role)
        return None if not a or a.get("none") else a

    def can(self, ent, role, action):
        a = self.acc(ent, role)
        return bool(a) and action in a["actions"]

    def roles(self):
        return [r for r in self.M["roles"] if r not in ("AnonymousUsers", "SystemUsers")]

    def creators(self, ent):
        cr = (self.E[ent].get("form") or {}).get("create") or {}
        if not cr and not self.E[ent]["fields"]:
            return []
        return [r for r in self.roles() if self.can(ent, r, "add") and (not cr.get("roles") or r in cr["roles"])]

    # ----- HTTP -----
    @staticmethod
    def js(r):
        try:
            return r.json()
        except ValueError:
            return {"_status": r.status_code, "_text": r.text[:200]}

    @staticmethod
    def body(j):
        return j.get("response", j) if isinstance(j, dict) else j

    def get(self, role, path, **params):
        r = self.session(role).get(path, params=params)
        return r.status_code, self.js(r)

    def post(self, role, path, params, data=None, files=None):
        r = self.session(role).post(path, params=params, data=data or {}, files=files)
        return r.status_code, self.js(r)

    # ----- records -----
    def schema(self, role, ent, params=None):
        code, j = self.get(role, self.ep(ent), action="initialize_form", **(params or {}))
        if code != 200:
            raise Skip(f"initialize_form as {role} → HTTP {code}")
        return ((self.body(j).get("form") or {}).get("json_schema")) or {}

    def needed_fields(self, ent):
        """Fields to fill besides required ones: those read by workflow conditions, create_on and app_user."""
        E = self.E[ent]
        need = set()
        wf = E.get("workflow") or {}
        for t in wf.get("transitions", []):
            for p, _kind in zx.paths_of(t.get("condition_ast")) if t.get("condition_ast") else []:
                need.add(p.split(".")[0].split("[")[0])
        au = E.get("app_user") or {}
        need |= {au.get(k) for k in ("name", "email", "mobile") if au.get(k)}
        return need

    def create(self, ent, role=None, values=None, params=None):
        """Create one record through the create form; returns object_uuid."""
        roles = [role] if role else self.creators(ent)
        roles = [r for r in roles if r in self.sessions] or roles
        if not roles:
            raise Skip(f"no role can create {ent}")
        role = roles[0]
        E = self.E[ent]
        tag = rnd()
        sch = self.schema(role, ent, params)
        props = sch.get("properties") or {}
        required = set(sch.get("required") or [])
        fmap = {f["key"]: f for f in E["fields"]}
        want = required | (self.needed_fields(ent) & set(props))
        vals = {}
        if self.fixtures and hasattr(self.fixtures, "values"):
            fv = self.fixtures.values
            takes_params = len(__import__("inspect").signature(fv).parameters) >= 4
            vals.update((fv(self, ent, role, params) if takes_params else fv(self, ent, role)) or {})
        vals.update(values or {})  # values the test passes explicitly win over fixture defaults
        data, files = {}, {}

        def fill(k):
            if k in vals:
                data[k] = vals[k]
                return
            f = fmap.get(k) or {"key": k, "type": "boolean" if k == "zas_confirm" else "text"}
            dv = (props.get(k) or {}).get("default")
            if dv not in (None, "") and f.get("type") not in ("file", "image"):
                # the form's own default (e.g. the parent FK preset on a 360 tab) is what a browser posts
                data[k] = ("true" if dv else "false") if isinstance(dv, bool) else str(dv)
                return
            if f.get("type") == "link" and not (props.get(k) or {}).get("enum") and f.get("to") in self.E and f["to"] != ent:
                self.create(f["to"])  # make an option exist, then re-read the form
                props[k] = (self.schema(role, ent, params).get("properties") or {}).get(k, {})
            v, fl = value_for(f, props.get(k, {}), tag)
            if fl:
                files[k] = fl
            elif v is not None:
                data[k] = v
        for k in sorted(want | set(vals)):
            if k in props or k in vals:
                fill(k)
        if "zas_confirm" in props:
            data["zas_confirm"] = "true"
        # a browser submits every schema default (an omitted checkbox would save False)
        for k, p in props.items():
            if k not in data and k not in files and isinstance(p, dict) and p.get("default") is not None:
                dv = p["default"]
                data[k] = ("true" if dv else "false") if isinstance(dv, bool) else str(dv)
        last = None
        for _ in range(3):
            code, j = self.post(role, self.ep(ent), {"form_type": "create_form", **(params or {})}, data,
                                {k: v for k, v in files.items()} or None)
            b = self.body(j)
            if code == 200 and (b or {}).get("object_uuid"):
                uid = str(b["object_uuid"])
                self.made.setdefault(ent, []).append(uid)
                return uid
            errs = (b or {}).get("errors") or {}
            missing = [k for k in errs if k in props and k not in data and k not in files]
            last = f"HTTP {code}: {json.dumps(errs or b)[:400]}"
            if not missing:
                break
            for k in missing:
                fill(k)
        raise AssertionError(f"create {ent} as {role} failed: {last}")

    def rows(self, role, ent, **params):
        code, j = self.get(role, self.ep(ent), view="table", action="get_table_data", start=0, length=500, **params)
        if code != 200:
            return None, code
        return j.get("data", self.body(j).get("data") if isinstance(self.body(j), dict) else None) or [], code

    def record(self, ent, uuid, role=None):
        for r in [role] if role else self.roles():
            if r not in self.sessions or not self.can(ent, r, "view"):
                continue
            rows, _ = self.rows(r, ent)
            for row in rows or []:
                if str(row.get("object_uuid")) == str(uuid):
                    return row
        return None

    def status_of(self, ent, uuid):
        for r in self.roles():
            if r in self.sessions and self.can(ent, r, "view"):
                code, j = self.get(r, self.ep(ent), view="detail", action="fetch_item_details", object_uuid=uuid)
                b = self.body(j) or {}
                st = ((b.get("zas") or {}).get("record") or {}).get("status")
                if st:
                    return st
                wd = b.get("workflow_details") or {}
                st = (wd.get("current_status_meta") or {}).get("status") or wd.get("current_status")
                if st:
                    return st
                row = self.record(ent, uuid, r)
                if row and row.get("workflow_status"):
                    ws = row["workflow_status"]
                    return ws.get("status") if isinstance(ws, dict) else ws
        return None

    # ----- workflow -----
    def engine(self, ent, name, from_status):
        t = next(t for t in self.E[ent]["workflow"]["transitions"] if t["name"] == name)
        return next((e["name"] for e in t["engine"] if e["from"] == from_status), None)

    def run(self, ent, uuid, name, role=None, data=None):
        t = next(t for t in self.E[ent]["workflow"]["transitions"] if t["name"] == name)
        st = self.status_of(ent, uuid)
        eng = self.engine(ent, name, st)
        if eng is None:
            return False, f"{name} does not start from {st}"
        role = role or next((r for r in t["roles"] if r in self.sessions), None) or next(iter(self.sessions), None)
        if self.fixtures and hasattr(self.fixtures, "before_transition"):
            self.fixtures.before_transition(self, ent, name, uuid, role)
        payload, files = dict(data or {}), {}
        if t.get("form") and data is None:
            tag = rnd()
            for f in t["form"]:
                v, fl = value_for(f, {"enum": [c["id"] for c in f.get("choices") or []]}, tag)
                if fl:
                    files[f["key"]] = fl
                elif v is not None:
                    payload[f["key"]] = v
            if self.fixtures and hasattr(self.fixtures, "transition_values"):
                payload.update(self.fixtures.transition_values(self, ent, name, role) or {})
        code, j = self.post(role, self.ep(ent), {"view": "workflow", "action": "process_transition", "transition_type": "status",
                                                  "transition_name": eng, "object_uuid": uuid}, payload, files or None)
        b = self.body(j) or {}
        return (code == 200 and j.get("success", True) is not False), (b.get("message") if isinstance(b, dict) else b) or f"HTTP {code}"

    def path_to(self, ent, target):
        wf = self.E[ent]["workflow"]
        start = wf["initial"]
        if target == start:
            return []
        seen, q = {start}, deque([(start, [])])
        while q:
            st, path = q.popleft()
            for t in wf["transitions"]:
                if t.get("system") or st not in t["from"]:
                    continue
                if t["to"] == target:
                    return path + [t["name"]]
                if t["to"] not in seen:
                    seen.add(t["to"])
                    q.append((t["to"], path + [t["name"]]))
        return None

    def record_in(self, ent, status, values=None):
        """A fresh record walked to `status`; Skip with the blocking step when it cannot get there."""
        path = self.path_to(ent, status) if self.E[ent].get("workflow") else []
        if path is None:
            raise Skip(f"{status} is not reachable from {self.E[ent]['workflow']['initial']} by manual transitions")
        uid = self.create(ent, values=values)
        for name in path:
            good, msg = self.run(ent, uid, name)
            if not good:
                raise Skip(f"could not reach {status}: {name} refused ({msg}). Add a before_transition fixture "
                           f"(.zas/test_fixtures.py) that prepares the data {name} needs")
        return uid


def status_set(ast, statuses):
    """The statuses for which a status-only expression is true, or None if it reads anything else."""
    if not ast:
        return None
    op = ast.get("op")
    if op == "cmp" and ast.get("path") == "status" and ast.get("cmp") in ("==", "!="):
        v = (ast.get("value") or {}).get("word")
        return {v} if ast["cmp"] == "==" else set(statuses) - {v}
    if op == "in" and ast.get("path") == "status":
        vals = {x.get("word") for x in ast.get("values", [])}
        return set(statuses) - vals if ast.get("neg") else vals
    if op in ("and", "or"):
        parts = [status_set(a, statuses) for a in ast["args"]]
        if any(p is None for p in parts):
            return None
        out = parts[0]
        for p in parts[1:]:
            out = out & p if op == "and" else out | p
        return out
    if op == "not":
        s = status_set(ast.get("arg"), statuses)
        return None if s is None else set(statuses) - s
    return None


# ───────────────────────── groups ─────────────────────────

def g_access(C):
    for ent, E in C.E.items():
        for role in C.roles():
            view = C.can(ent, role, "view")
            path = f"entities.{ent}.access.{role}"

            def t_list(ent=ent, role=role, view=view):
                code, j = C.get(role, C.ep(ent), action="get_table_metadata")
                okay = code == 200 and j.get("success", True) is not False
                return (okay == view), f"expected {'200' if view else 'refusal'}, got HTTP {code}"
            C.check(f"access.list.{ent}.{slug(role)}", f"{'can' if view else 'cannot'} open the {E['plural']} list", role, path, t_list)

            if view and not C.can(ent, role, "add"):
                def t_add(ent=ent, role=role):
                    code, j = C.post(role, C.ep(ent), {"form_type": "create_form"}, {})
                    return code >= 400 or j.get("success") is False, f"create was not refused (HTTP {code})"
                C.check(f"access.add.{ent}.{slug(role)}", f"cannot add {E['name']}", role, path + ".actions", t_add)


def g_create(C):
    for m in C.M["module_order"] if C.M.get("module_order") else [m["code"] for m in C.M["modules"]]:
        mod = next(x for x in C.M["modules"] if x["code"] == m)
        for ent in mod.get("entity_order") or mod["entities"]:
            E = C.E[ent]
            if not C.creators(ent):
                continue

            def t_create(ent=ent, E=E):
                uid = C.create(ent)
                row = C.record(ent, uid)
                if row is None:
                    return False, f"created {uid} but no role that can view {ent} lists it"
                bad = []
                for f in E["fields"]:
                    seq = (f.get("auto") or {}).get("sequence")
                    if seq and f["key"] in row:
                        pat = "^" + re.sub(r"\\\{0+\\\}", lambda m2: r"\d{%d,}" % (len(m2.group()) - 4), re.escape(seq))
                        pat = pat.replace(r"\{YYYY\}", r"\d{4}").replace(r"\{YY\}", r"\d{2}")
                        if not re.match(pat, str(row[f["key"]])):
                            bad.append(f"{f['key']}={row[f['key']]!r} does not match {seq}")
                return not bad, "; ".join(bad)
            C.check(f"create.{ent}", f"create a {E['name']}", (C.creators(ent) or [None])[0], f"entities.{ent}.form.create", t_create)

            for i, rule in enumerate((E.get("validation") or {}).get("rules") or []):
                w = rule.get("when_ast")
                if not rule.get("require") or (w and not (w.get("op") == "cmp" and w.get("cmp") == "==" and "." not in w.get("path", ""))):
                    continue

                def t_rule(ent=ent, rule=rule, w=w):
                    vals = {w["path"]: (w["value"].get("word") or w["value"].get("str") or w["value"].get("num"))} if w else {}
                    try:
                        C.create(ent, values={**vals, **{k: "" for k in rule["require"]}})
                    except AssertionError as e:
                        return (rule.get("message") or "") in str(e) or "required" in str(e).lower(), f"refused, but not with the rule's message: {e}"
                    return False, "the record was created although the rule should refuse it"
                C.check(f"create.rule.{ent}.{i + 1}", f"rule refuses: {rule.get('message') or rule['require']}", None,
                        f"entities.{ent}.validation.rules[{i}]", t_rule)

            for i, rule in enumerate(((E.get("validation") or {}).get("duplicate_check") or {}).get("rules") or []):
                if rule.get("compare", "exact") != "exact" or rule.get("on_match", "block") != "block" or any("." in m for m in rule["match"]):
                    continue

                def t_dupe(ent=ent, rule=rule):
                    first = C.create(ent)
                    row = C.record(ent, first)
                    if not row or any(m not in row for m in rule["match"]):
                        raise Skip("matched fields are not table columns; cannot read the first record's values")
                    try:
                        C.create(ent, values={m: row[m] for m in rule["match"]})
                    except AssertionError as e:
                        return True, str(e)
                    return False, "a duplicate was created"
                C.check(f"create.dupe.{ent}.{i + 1}", f"duplicate {rule['match']} is blocked", None,
                        f"entities.{ent}.validation.duplicate_check.rules[{i}]", t_dupe)


def g_transitions(C):
    for ent, E in C.E.items():
        wf = E.get("workflow")
        if not wf:
            continue
        for t in wf["transitions"]:
            if t.get("system"):
                continue
            for fr in t["from"]:
                path = f"entities.{ent}.workflow.transitions.{t['name']}"
                allowed = [r for r in (t["roles"] or C.roles()) if r in C.sessions] or (t["roles"] or [None])

                def t_ok(ent=ent, t=t, fr=fr, role=allowed[0]):
                    uid = C.record_in(ent, fr)
                    good, msg = C.run(ent, uid, t["name"], role)
                    if not good:
                        return False, f"refused: {msg}"
                    if NOT_IMPL in str(msg):
                        return False, msg
                    st = C.status_of(ent, uid)
                    return st == t["to"], f"status is {st}, expected {t['to']}"
                C.check(f"transition.{ent}.{t['name']}.{fr}", f"{t['label']} ({fr} → {t['to']})", allowed[0], path, t_ok)

                others = [r for r in C.roles() if t["roles"] and r not in t["roles"] and C.can(ent, r, "view")]
                if others:
                    def t_refused(ent=ent, t=t, fr=fr, role=others[0]):
                        uid = C.record_in(ent, fr)
                        good, msg = C.run(ent, uid, t["name"], role)
                        return not good, "the transition ran for a role not in its roles"
                    C.check(f"transition.refused.{ent}.{t['name']}.{fr}", f"{t['label']} refused", others[0], path + ".roles", t_refused)


def g_tags(C):
    for ent, E in C.E.items():
        wf = E.get("workflow")
        if not wf:
            continue
        for tg in wf["tags"]:
            path = f"entities.{ent}.workflow.tags.{tg['code']}"
            for side, state in (("enable", "enabled"), ("disable", "disabled")):
                sd = tg.get(side)
                if tg.get("system") or not sd:
                    viewers = [r for r in C.roles() if C.can(ent, r, "view")]
                    if not viewers:
                        continue

                    def t_never(ent=ent, tg=tg, state=state, role=viewers[0]):
                        uid = C.create(ent)
                        code, j = C.post(role, C.ep(ent), {"view": "workflow", "action": "process_transition", "transition_type": "tag",
                                                           "transition_name": tg["code"], "transition_state": state, "object_uuid": uid})
                        return not (code == 200 and j.get("success") is not False), "a tag side the spec does not allow was applied"
                    C.check(f"tag.never.{ent}.{tg['code']}.{side}", f"{tg['label']}: {side} not possible", viewers[0], path, t_never)
                    continue
                roles = [r for r in (sd.get("roles") or C.roles()) if r in C.sessions] or [None]

                def t_tag(ent=ent, tg=tg, side=side, state=state, sd=sd, role=roles[0]):
                    s = status_set(sd.get("condition_ast"), [x["code"] for x in E["workflow"]["statuses"]])
                    if sd.get("condition_ast") and s is None:
                        raise Skip("condition is not status-only; prove it with a fixture")
                    uid = C.record_in(ent, sorted(s)[0]) if s else C.create(ent)
                    if side == "disable":
                        en = tg.get("enable") or {}
                        r2 = next((r for r in (en.get("roles") or C.roles()) if r in C.sessions), role)
                        C.post(r2, C.ep(ent), {"view": "workflow", "action": "process_transition", "transition_type": "tag",
                                               "transition_name": tg["code"], "transition_state": "enabled", "object_uuid": uid},
                               {f["key"]: value_for(f, {}, rnd())[0] for f in (en.get("form") or [])})
                    data = {f["key"]: value_for(f, {"enum": [c["id"] for c in f.get("choices") or []]}, rnd())[0] for f in sd.get("form") or []}
                    code, j = C.post(role, C.ep(ent), {"view": "workflow", "action": "process_transition", "transition_type": "tag",
                                                       "transition_name": tg["code"], "transition_state": state, "object_uuid": uid}, data)
                    return code == 200 and j.get("success") is not False, f"HTTP {code}: {json.dumps(C.body(j))[:300]}"
                C.check(f"tag.{ent}.{tg['code']}.{side}", f"{tg['label']}: {side}", roles[0], f"{path}.{side}", t_tag)


def g_row_actions(C):
    for ent, E in C.E.items():
        for a in (E.get("table") or {}).get("row_actions") or []:
            if a["type"] == "navigate":
                continue
            path = f"entities.{ent}.table.row_actions.{a['key']}"
            if a["type"] == "edit":
                ed = (E.get("form") or {}).get("edit") or {}
                allowed = [r for r in C.roles() if C.can(ent, r, "edit") and (not ed.get("roles") or r in ed["roles"])
                           and (not a.get("roles") or r in a["roles"])]
            else:
                allowed = [r for r in (a.get("roles") or C.roles()) if C.can(ent, r, "view")]
            if a["type"] == "delete":
                allowed = [r for r in allowed if C.can(ent, r, "delete")]
            denied = [r for r in C.roles() if C.can(ent, r, "view") and r not in allowed]
            s = status_set(a.get("show_when_ast"), [x["code"] for x in (E.get("workflow") or {}).get("statuses", [])])
            if a.get("show_when_ast") and s is None:
                continue

            def fresh(ent=ent, s=s, E=E, a=a):
                ed = ((E.get("form") or {}).get("edit") or {}).get("editable_in")
                pool = sorted((s or set()) & set(ed)) if (ed and a["type"] == "edit" and s) else sorted(s or ed or [])
                return C.record_in(ent, pool[0]) if pool and E.get("workflow") else C.create(ent)

            if allowed:
                def t_run(ent=ent, a=a, role=allowed[0], fresh=fresh):
                    uid = fresh()
                    row = C.record(ent, uid, role)
                    if row is None:
                        return False, f"{role} cannot see the record"
                    keys = [x.get("key") for x in row.get("row_actions") or []]
                    if a["key"] not in keys:
                        return False, f"not offered in the row menu (offered: {keys})"
                    if a["type"] in ("edit", "form"):
                        code, j = C.get(role, C.ep(ent), action="initialize_form", action_type="row", action_key=a["key"], object_uuid=uid)
                        props = (((C.body(j) or {}).get("form") or {}).get("json_schema") or {}).get("properties") or {}
                        fmap = {f["key"]: f for f in E["fields"] + a.get("form", [])}
                        data = {}
                        for k, p in props.items():
                            f = fmap.get(k) or {"key": k}
                            dv = p.get("default")
                            if dv not in (None, "") and f.get("type") not in ("file", "image") \
                                    and k not in [x["key"] for x in a.get("form", [])]:
                                # an edit form posts the record's current values back, as a browser does
                                data[k] = ("true" if dv else "false") if isinstance(dv, bool) else str(dv)
                                continue
                            v, _ = value_for(f, p, rnd())
                            if v is not None and (k in [x["key"] for x in a.get("form", [])] or (dv in (None, "") and k in fmap and fmap[k].get("required"))):
                                data[k] = v
                        code, j = C.post(role, C.ep(ent), {"action_type": "row", "form_type": "row_action_form", "action_key": a["key"],
                                                           "object_uuid": uid}, data)
                    else:
                        code, j = C.post(role, C.ep(ent), {"action_type": "row", "action_key": a["key"], "object_uuid": uid})
                    b = C.body(j) or {}
                    msg = b.get("message", "") if isinstance(b, dict) else str(b)
                    if NOT_IMPL in msg:
                        return False, msg
                    if a["type"] == "download" and not b.get("url"):
                        return False, f"download returned no url: {json.dumps(b)[:200]}"
                    return code == 200 and j.get("success") is not False, f"HTTP {code}: {json.dumps(b)[:300]}"
                C.check(f"row_action.{ent}.{a['key']}", f"{a['label']} runs", allowed[0], path, t_run)
            if denied:
                def t_denied(ent=ent, a=a, role=denied[0], fresh=fresh):
                    uid = fresh()
                    row = C.record(ent, uid, role)
                    keys = [x.get("key") for x in (row or {}).get("row_actions") or []]
                    if a["key"] in keys:
                        return False, f"offered to {role}"
                    params = {"action_type": "row", "action_key": a["key"], "object_uuid": uid}
                    if a["type"] in ("edit", "form"):
                        params["form_type"] = "row_action_form"
                    code, j = C.post(role, C.ep(ent), params)
                    return not (code == 200 and j.get("success") is not False), f"ran for {role} (HTTP {code})"
                C.check(f"row_action.refused.{ent}.{a['key']}", f"{a['label']} refused", denied[0], path + ".roles", t_denied)


def g_scoping(C):
    users = auth.load_users(C.ws).get("users", [])
    for ent, E in C.E.items():
        statuses = [x["code"] for x in (E.get("workflow") or {}).get("statuses", [])]
        for role, a in (E.get("access_resolved") or {}).items():
            if not E.get("access") or not a or a.get("none") or role not in C.roles():
                continue
            rows = a.get("rows")
            path = f"entities.{ent}.access.{role}.rows"
            if isinstance(rows, dict) and rows.get("ast"):
                s = status_set(rows["ast"], statuses)
                if s is None:
                    continue

                def t_where(ent=ent, role=role, s=s):
                    inside = C.record_in(ent, sorted(s)[0])
                    outside_st = [x for x in statuses if x not in s]
                    out = None
                    for st in outside_st:
                        try:
                            out = C.record_in(ent, st)
                            break
                        except Skip:
                            continue
                    got, code = C.rows(role, ent)
                    ids = {str(r.get("object_uuid")) for r in got or []}
                    if inside not in ids:
                        return False, f"a record in {sorted(s)[0]} is missing from {role}'s list"
                    if out and out in ids:
                        return False, f"a record outside {sorted(s)} is listed for {role}"
                    return True, ""
                C.check(f"scoping.where.{ent}.{slug(role)}", f"{role} sees only {E['plural']} where {rows.get('where')}", role, path, t_where)
            elif isinstance(rows, dict) and "own" in rows and rows["own"] == "id" and E.get("app_user"):
                au = E["app_user"]
                u = next((u for u in users if role in u.get("roles", [])), None)
                if not u:
                    continue

                def t_own(ent=ent, role=role, au=au, u=u):
                    co = au.get("create_on_ast")
                    s = status_set(co, statuses) if co else None
                    vals = {au["email"]: u["email"]} if au.get("email") else {}
                    mine = C.record_in(ent, sorted(s)[0], values=vals) if s else C.create(ent, values=vals)
                    other = C.create(ent)
                    C.sessions.pop(role, None)
                    C.sessions[role] = auth.login(C.ws, role)  # re-login: the binding is read at login
                    got, code = C.rows(role, ent)
                    ids = {str(r.get("object_uuid")) for r in got or []}
                    if ids != {mine}:
                        return False, f"{role} lists {len(ids)} records; expected only its own ({mine in ids=})"
                    code, j = C.get(role, C.ep(ent), view="detail", action="fetch_item_details", object_uuid=other)
                    st = ((C.body(j) or {}).get("zas") or {}).get("access")
                    return st == "not_found" or code in (403, 404), f"another {ent} opened for {role} (access={st}, HTTP {code})"
                C.check(f"scoping.own.{ent}.{slug(role)}", f"{role} sees only its own {E['name']}", role, path, t_own)


def g_detail(C):
    for vcode, V in (C.M.get("detail_views") or {}).items():
        hero = V["hero"]
        path = f"detail_views.{vcode}"
        viewers = [r for r in C.roles() if (not V.get("roles") or r in V["roles"]) and C.can(hero, r, "detail")]
        holder = {}

        def hero_uuid(hero=hero, holder=holder):
            if "uid" not in holder:
                holder["uid"] = C.create(hero)
            return holder["uid"]

        for role in C.roles():
            def t_open(role=role, ok_role=role in viewers, hero=hero):
                if not C.can(hero, role, "view") and not ok_role:
                    raise Skip(f"{role} has no access to {hero}")
                uid = None
                if ok_role and C.fixtures and hasattr(C.fixtures, "record_for"):
                    uid = C.fixtures.record_for(C, hero, role)  # e.g. the record a bound login owns
                uid = uid or hero_uuid()
                code, j = C.get(role, C.ep(hero), view="detail", action="fetch_item_details", object_uuid=uid)
                zas = (C.body(j) or {}).get("zas") or {}
                st = zas.get("access")
                if ok_role:
                    if st != "ok" or zas.get("error"):
                        return False, f"access={st} error={zas.get('error')}"
                    bad = [s["label"] for s in zas.get("stats", []) if s.get("value") is not None and not isinstance(s["value"], (int, float))]
                    return not bad, f"non-numeric stats: {bad}"
                return st in ("no_access", "not_found") or code in (403, 404), f"opened for {role} (access={st})"
            C.check(f"detail.open.{vcode}.{slug(role)}", f"{'opens' if role in viewers else 'refused'}: {vcode}", role, path + ".roles", t_open)

        for t in V.get("tabs") or []:
            if t.get("type") == "related_table" and t.get("entity") and t.get("param"):
                child = t["entity"]
                r0 = next((r for r in viewers if C.can(child, r, "view")), None)
                if not r0:
                    continue

                def t_tab(t=t, child=child, role=r0):
                    uid = None
                    maker = (C.creators(child) or [None])[0]
                    if maker and C.fixtures and hasattr(C.fixtures, "record_for"):
                        uid = C.fixtures.record_for(C, hero, maker)  # a scoped creator adds under a hero it can see
                    uid = uid or hero_uuid()
                    other = C.create(hero)
                    one_hop = (C.E[child].get("parents") or {}).get(t["param"], {}).get("fk")
                    if not one_hop or not C.creators(child):
                        raise Skip("two-hop tab or nobody can add the child: listing checked only")
                    kid = C.create(child, params={t["param"]: uid})
                    got, code = C.rows(role, child, **{t["param"]: uid})
                    ids = {str(r.get("object_uuid")) for r in got or []}
                    got2, _ = C.rows(role, child, **{t["param"]: other})
                    ids2 = {str(r.get("object_uuid")) for r in got2 or []}
                    if kid not in ids:
                        return False, f"child created from the tab is not listed under its parent (HTTP {code})"
                    if kid in ids2:
                        return False, "child is listed under another parent: the parent filter is not applied"
                    return True, ""
                C.check(f"detail.tab.{vcode}.{t['code']}", f"tab {t['label']}: add + list by parent", r0, f"{path}.tabs.{t['code']}", t_tab)
            if t.get("type") == "timeline" and viewers:
                def t_tl(t=t, role=viewers[0]):
                    code, j = C.get(role, C.ep(hero), view="detail", action="zas_timeline", object_uuid=hero_uuid(), tab=t["code"])
                    return code == 200 and j.get("success") is not False, f"HTTP {code}"
                C.check(f"detail.timeline.{vcode}.{t['code']}", f"timeline {t['label']} answers", viewers[0], f"{path}.tabs.{t['code']}", t_tl)


def save_records(ws, made):
    """Records created by this run, per entity (newest last); the UI layer opens 360s on them."""
    p = os.path.join(ws, ".zas", "test_records.json")
    try:
        old = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    for ent, ids in made.items():
        old[ent] = (old.get(ent, []) + ids)[-20:]
    with open(p, "w", encoding="utf-8") as f:
        json.dump(old, f, indent=1)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


RUNNERS = {"access": g_access, "create": g_create, "transitions": g_transitions, "tags": g_tags,
           "row_actions": g_row_actions, "scoping": g_scoping, "detail": g_detail}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--only", help="comma-separated groups: " + ",".join(GROUPS))
    ap.add_argument("--role", action="append", help="limit to checks run as this role (repeatable)")
    ap.add_argument("--dry-run", action="store_true", help="list the planned checks without calling the app")
    a = ap.parse_args(argv)
    groups = [g.strip() for g in (a.only or ",".join(GROUPS)).split(",") if g.strip()]
    C = Ctx(a.workspace, a.role)
    if a.dry_run:
        C.check = lambda id, title, role, path, fn: C.add(id, title, role, path, "skip", "dry run")
        C.sessions = {r: None for r in C.roles()}
    else:
        C.login_all()
        for r, e in C.login_errors.items():
            print(f"login {r}: {e}", file=sys.stderr)
    for g in groups:
        RUNNERS[g](C)
    if a.dry_run:
        for r in C.results:
            print(f"{r['id']:<60} {r['role'] or '':<24} {r['title']}")
        print(f"\n{len(C.results)} checks planned")
        return 0
    save_results(a.workspace, "api", C.results, {"groups": groups})
    save_records(a.workspace, C.made)
    print_summary("api", C.results)
    return 1 if any(r["status"] == "fail" for r in C.results) else 0


if __name__ == "__main__":
    sys.exit(main())
