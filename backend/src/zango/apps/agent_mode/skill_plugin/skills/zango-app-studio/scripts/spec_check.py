#!/usr/bin/env python3
"""
spec_check.py - parse, normalise and lint an App Studio spec, then derive
everything the build needs.

    python3 spec_check.py <app_spec.yaml> --workspace <app workspace> [--quiet]

Writes into <workspace>/.zas/:
    spec.resolved.json   the normalised spec + derived names (every later phase reads this)
    spec.ui.json         the frontend config (copied to frontend/src/custom/ in Phase 6)
    holes.md             every plain-language item, with a stable ID and target function
    plan.md              build order, names, endpoints, pages per role
    issues.md            lint findings (also printed)

Exit code: 0 = no errors (warnings allowed), 1 = errors, 2 = cannot read the spec.
Contracts: references/contracts.md.
"""

import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write("PyYAML is required: pip install pyyaml\n")
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
_expr_spec = importlib.util.spec_from_file_location(
    "zas_expr", os.path.join(HERE, "..", "assets", "backend", "zas_core", "expr.py"))
X = importlib.util.module_from_spec(_expr_spec)
_expr_spec.loader.exec_module(X)

SKILL_VERSION = "0.1.0"

FIELD_TYPES = {
    "text", "long_text", "integer", "decimal", "money", "percent", "boolean",
    "date", "datetime", "time", "email", "phone", "url",
    "choice", "multi_choice", "link", "multi_link", "file", "image", "json",
}
KINDS = {"hero", "transactional", "child", "master"}
ACTIONS = {"view", "add", "edit", "delete", "export", "detail"}
ROW_ACTION_TYPES = {"edit", "form", "confirm", "navigate", "download", "delete"}
PAGE_TYPES = {"crud", "detail", "custom"}
# app.ui: the look, as choices tokens.css maps to values (references/design-system.md)
UI_RADIUS = ("sharp", "rounded", "soft")
UI_DENSITY = ("compact", "comfortable")
TAB_TYPES = {"summary", "related_table", "timeline", "fields", "custom"}
SECTION_TYPES = {"fields", "mini_table", "custom", "timeline", "stats"}
TONES = {"gray", "blue", "green", "amber", "red", "purple", "teal", "indigo", "pink"}
BANNER_TONES = {"info", "warning", "danger", "success"}
LAYOUTS = {"header_tabs", "header_tabs_sidebar", "header_sidebar_tabs_left"}
COLUMN_SOURCES = {"field", "status", "tags", "computed", "path"}
FORMATS = {"money", "percent", "number", "date", "datetime", "days", None}
BUILTIN = {
    "id": {"type": "integer", "label": "ID"},
    "created_at": {"type": "datetime", "label": "Created"},
    "modified_at": {"type": "datetime", "label": "Modified"},
    "created_by": {"type": "user", "label": "Created by"},
    "modified_by": {"type": "user", "label": "Modified by"},
}
RESERVED = {"id", "pk", "object_uuid", "created_at", "created_by", "modified_at", "modified_by",
            "objects", "save", "delete", "clean", "meta", "status", "tags", "check"}
# workflow colour names (engine renders white text on these) for each spec tone
WF_COLOR = {"gray": "gray", "blue": "blue", "green": "green", "amber": "orange", "red": "red",
            "purple": "purple", "teal": "#0E9384", "indigo": "#444CE7", "pink": "#DD2590"}
TONE_HEX = {"gray": "#344054", "blue": "#175CD3", "green": "#067647", "amber": "#B54708",
            "red": "#B42318", "purple": "#5925DC", "teal": "#107569", "indigo": "#3538CD",
            "pink": "#C11574"}


# ───────────────────────────── helpers ─────────────────────────────

DASH_BLOCKS = ("kpis", "bars", "list", "table", "board", "grid", "stack", "panel")
DASH_AGGS = ("count", "sum", "avg", "min", "max")


def _dash_value(val):
    val = val or {}
    for a in DASH_AGGS:
        if a in val:
            where = f" where {val['where']}" if val.get("where") else ""
            return f"{a} of {val[a]}{where}"
    return "?"


def _dash_block(b, depth=0):
    """One block of a declared dashboard, as the build agent reads it."""
    pad = "  " * depth
    if not isinstance(b, dict) or len(b) != 1:
        return [f"{pad}- (invalid block)"]
    (k, v), = b.items()
    if k in ("grid", "stack"):
        out = [f"{pad}- {'side by side' if k == 'grid' else 'one under another'}:"]
        for x in arr(v):
            out += _dash_block(x, depth + 1)
        return out
    if k == "panel":
        v = v or {}
        out = [f"{pad}- panel \"{v.get('title', '')}\":"]
        for x in arr(v.get("blocks")):
            out += _dash_block(x, depth + 1)
        return out
    if k == "kpis":
        tiles = []
        for t in arr(v):
            t = t or {}
            extra = "".join(f", {x} {t[x]}" for x in ("format", "tone", "icon") if t.get(x))
            tiles.append(f"\"{t.get('label', '')}\" = {_dash_value(t.get('value'))}{extra}"
                         + (f" (opens {t['go']})" if t.get("go") else ""))
        return [f"{pad}- KPI tiles: " + "; ".join(tiles)]
    v = v or {}
    where = f" where {v['where']}" if v.get("where") else ""
    opens = f"; rows open {v['go']}" if v.get("go") else "; rows open the record (360 page or drawer)"
    if k == "bars":
        val = v.get("value")
        measure = f"sum of {val['sum']}" if isinstance(val, dict) and val.get("sum") else "count"
        return [f"{pad}- bar chart \"{v.get('title', '')}\": {v.get('entity')}{where}, grouped by {v.get('group_by')}, {measure}"]
    if k == "list":
        parts = [f"primary {v.get('primary')}"] + [f"{x} {v[x]}" for x in ("secondary", "meta", "badge") if v.get(x)]
        return [f"{pad}- list \"{v.get('title', '')}\": {v.get('entity')}{where}, sorted by {v.get('sort') or '-created_at'}, "
                f"{v.get('limit', 8)} rows, {', '.join(parts)}{opens}"]
    if k == "table":
        return [f"{pad}- table \"{v.get('title', '')}\": {v.get('entity')}{where}, columns {', '.join(map(str, arr(v.get('columns'))))}, "
                f"sorted by {v.get('sort') or '-created_at'}, {v.get('limit', 10)} rows{opens}"]
    if k == "board":
        return [f"{pad}- board \"{v.get('title', '')}\": {v.get('entity')}{where}, a column per {v.get('group_by')} value, "
                f"cards show {(v.get('card') or {}).get('title') or 'the record'}{opens}"]
    return [f"{pad}- (unknown block {k})"]


def contract_text(node):
    """A custom screen's or requirement's contract (SCHEMA.md, contracts), appended to its hole text."""
    node = node or {}
    out = []
    reads = [f"{d.get('entity')}" + (f" via {d['via']}" if d.get("via") else "") + (f" where {d['where']}" if d.get("where") else "")
             for d in arr(node.get("data")) if isinstance(d, dict)]
    if reads:
        out.append("Reads: " + "; ".join(reads) + " (each role's row scoping applies).")
    acts = []
    for a in arr(node.get("interactions")):
        if not isinstance(a, dict):
            continue
        does = a.get("does") or (f"opens {a['go']}" if a.get("go") else "")
        if a.get("update"):
            does = (does + "; " if does else "") + f"saves {a['update'].get('entity')}.{a['update'].get('field')}"
        if a.get("transition"):
            does = (does + "; " if does else "") + f"runs transition {a['transition']}"
        if a.get("row_action"):
            does = (does + "; " if does else "") + f"runs row action {a['row_action']}"
        roles = f" (roles: {', '.join(arr(a['roles']))})" if a.get("roles") else ""
        acts.append(f"{a.get('event')} -> {does or 'see text'}{roles}")
    if acts:
        out.append("Interactions: " + "; ".join(acts) + ".")
    states = node.get("states") or {}
    if isinstance(states, dict) and states:
        out.append("States: " + "; ".join(f"{k} \"{v}\"" for k, v in states.items()) + ".")
    trig = node.get("trigger") or {}
    if isinstance(trig, dict) and trig.get("event"):
        what = trig.get("transition") or trig.get("tag") or trig.get("cron") or ""
        out.append(f"Trigger: {trig['event']}" + (f" {what}" if what else "") + (f" of {trig['entity']}" if trig.get("entity") else "") + ".")
    acc = [str(x) for x in arr(node.get("acceptance"))]
    if acc:
        out.append("Acceptance (test each): " + " ".join(f"({i}) {x}" for i, x in enumerate(acc, 1)))
    refs = [str(x) for x in arr(node.get("refs"))]
    if refs:
        out.append("Follows: " + ", ".join(refs) + ".")
    return (" " + " ".join(out)) if out else ""


def dashboard_text(P):
    """The hole text of a declared dashboard: what the user approved, block by block."""
    lines = [f"Dashboard declared block by block (spec.resolved.json pages.{P['code']}.blocks). Build every block "
             "exactly as declared, with each role's row scoping on every count, sum and list, and nothing else:"]
    for b in arr(P.get("blocks")):
        lines += _dash_block(b)
    if P.get("text"):
        lines.append("Also: " + str(P["text"]))
    return "\n".join(lines)



# --- app.design (open mode): the approved prototype's tokens on the runtime ---------------------
# app.design.tokens uses canonical names (SCHEMA.md, app.design); each maps onto the zas tokens
# (tokens.css) and the crud package's gray ramp, so standard screens take the prototype's look.
# config.ts applyTheme() injects the CSS (html:root beats the app.ui radius/density rules) and the
# Google Fonts link for families the runtime does not embed.
DESIGN_MAP = {
    "page": ["--z-ground"],
    "card": ["--z-card", "--color-base-white"],
    "sunk": ["--z-sunken", "--color-gray-100"],
    "text-strong": ["--color-gray-900"],
    "text": ["--z-text", "--color-gray-900", "--color-gray-800"],
    "text-2": ["--z-text2", "--z-sub", "--color-gray-700", "--color-gray-600"],
    "text-3": ["--z-muted", "--color-gray-500"],
    "text-faint": ["--z-faint", "--color-gray-400"],
    "border-faint": ["--z-bdf"],
    "border": ["--z-bd", "--color-gray-200"],
    "border-strong": ["--z-bds", "--z-ghost", "--color-gray-300"],
    "brand-strong": ["--b600", "--color-brand-600"],
    "brand-soft": ["--b50", "--color-brand-50", "--color-primary-light"],
    "radius-sm": ["--z-r-ctl"],
    "radius": ["--z-r-card"],
    "radius-lg": ["--z-r-head"],
    "shadow-sm": ["--z-shadow"],
    "shadow": ["--z-shadow"],
    "shadow-lg": ["--z-shadow-pop"],
    "ok": ["--t-green-fg"], "ok-bg": ["--t-green-bg"],
    "warn": ["--t-amber-fg"], "warn-bg": ["--t-amber-bg"],
    "bad": ["--t-red-fg", "--color-error-500"], "bad-bg": ["--t-red-bg"],
    "info": ["--t-blue-fg"], "info-bg": ["--t-blue-bg"],
}
TONE_OF = {"ok": "green", "warn": "amber", "bad": "red", "info": "blue"}
EMBEDDED_FONTS = {"inter", "jetbrains mono"}
_CSS_VALUE = re.compile(r"^[^;{}<>]{1,300}$")


def _token_defaults():
    """{--var: value} from the runtime's tokens.css :root block (the pinned gallery's values)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "frontend", "zas", "tokens.css")
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return {}
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    m = re.search(r":root\s*\{(.*?)\n\}", text, re.S)
    return {k: " ".join(v.split()) for k, v in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", m.group(1) if m else "")}


def _font_stack(family, fallback):
    return f'"{family}", {fallback}' if family else None


def design_css(design):
    """(css, google_fonts_url, problems) for app.design; ("", None, []) without tokens."""
    design = design if isinstance(design, dict) else {}
    tokens = design.get("tokens") if isinstance(design.get("tokens"), dict) else {}
    fonts = design.get("fonts") if isinstance(design.get("fonts"), dict) else {}
    problems, decl = [], OrderedDict()
    values = {}
    for name, value in tokens.items():
        value = str(value).strip()
        if not _CSS_VALUE.match(value) or "url(" in value.lower():
            problems.append(f"app.design.tokens.{name}: not a plain CSS value")
            continue
        values[name] = value
    for name, targets in DESIGN_MAP.items():
        if name in values:
            for t in targets:
                if t == "--z-shadow" and name == "shadow-sm" and "shadow" in values:
                    continue
                decl[t] = values[name]
    if "card" in values and "sunk" in values:
        decl["--z-head"] = f"color-mix(in srgb, {values['sunk']} 50%, {values['card']})"
        decl["--color-gray-50"] = decl["--z-head"]
    for name, tone in TONE_OF.items():
        if name in values and f"{name}-bg" in values:
            decl[f"--t-{tone}-bd"] = f"color-mix(in srgb, {values[name]} 30%, {values[name + '-bg']})"
    body = _font_stack(fonts.get("body"), '-apple-system, "Segoe UI", system-ui, sans-serif')
    mono = _font_stack(fonts.get("mono"), '"SF Mono", ui-monospace, Menlo, monospace')
    if body:
        decl["--z-font"] = body
    if mono:
        decl["--z-mono"] = mono
    if fonts.get("display"):
        decl["--z-display"] = _font_stack(fonts["display"], "var(--z-font)")
    # every other token stays available to custom screens as --p-<name>
    for name, value in values.items():
        if name not in DESIGN_MAP and name not in ("brand", "accent", "accent-soft", "nav"):
            decl[f"--p-{name}"] = value
    for name in ("accent", "accent-soft", "nav"):
        if name in values:
            decl[f"--p-{name}"] = values[name]
    css = ""
    if decl:
        # The form and crud packages load their own `:root` palettes after tokens.css (FormRenderer's
        # Submit came out #5048ed). Restating the tokens.css bridge here wins by specificity.
        for k, v in _token_defaults().items():
            if k.startswith(("--color-", "--zango-")):
                decl.setdefault(k, v)
        css = "html:root {\n" + "".join(f"  {k}: {v};\n" for k, v in decl.items()) + "}\n"
        # The component gallery keeps the default look for its goldens ([data-zas-pinned]).
        defaults = _token_defaults()
        pinned = [(k, defaults[k]) for k in decl if k in defaults]
        if pinned:
            css += "html:root [data-zas-pinned] {\n" + "".join(f"  {k}: {v};\n" for k, v in pinned) + "}\n"
        if body:
            # @zango-core/appbuilder sets `* { font-family: Inter }`; zero specificity keeps every
            # runtime font rule (mono, headings) in charge while beating that reset.
            css += ":where(.zas, .zas *, .zas-login, .zas-login *) { font-family: var(--z-font); }\n"
    families = []
    for fam in (fonts.get("body"), fonts.get("display"), fonts.get("mono")):
        if fam and fam.lower() not in EMBEDDED_FONTS and fam not in families:
            families.append(fam)
    url = None
    if families:
        url = "https://fonts.googleapis.com/css2?" + "&".join(
            "family=" + f.replace(" ", "+") + ":wght@400;500;600;700" for f in families
        ) + "&display=swap"
    return css, url, problems

def arr(x):
    if x is None:
        return []
    return list(x) if isinstance(x, (list, tuple)) else [x]


def titleize(s):
    """Same as the Studio preview's titleize: every word capitalised ("pi_email" → "Pi Email")."""
    s = re.sub(r"\s+", " ", re.sub(r"[_-]+", " ", str(s if s is not None else ""))).strip()
    return re.sub(r"\b\w", lambda m: m.group().upper(), s)


def pascal(s):
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[_\W]+", str(s)) if p)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


def url_part(code):
    return str(code).replace("_", "-")


def is_ident(s):
    return isinstance(s, str) and re.fullmatch(r"[a-z][a-z0-9_]*", s) is not None


def kv(lst):
    """Normalise `- name: {...}` / `- name` / `{key: ...}` lists to [{key, ...}]."""
    out = []
    if isinstance(lst, dict):
        lst = [{k: v} for k, v in lst.items()]
    for item in arr(lst):
        if isinstance(item, str):
            out.append({"key": item})
        elif isinstance(item, dict):
            if "key" in item and len(item) >= 1 and not (len(item) == 1 and isinstance(item["key"], dict)):
                out.append(dict(item))
            elif len(item) == 1:
                k, v = next(iter(item.items()))
                out.append({"key": k, **(v if isinstance(v, dict) else {})})
            else:
                out.append(dict(item))
    return out


class Linter:
    def __init__(self):
        self.items = []

    def error(self, where, msg, fix=None):
        self.items.append({"level": "error", "where": where, "msg": msg, "fix": fix})

    def warn(self, where, msg, fix=None):
        self.items.append({"level": "warn", "where": where, "msg": msg, "fix": fix})

    def intent(self, where, msg, fix=None):
        """Valid spec, but probably not what the author meant (a role that can act but never see, …).
        Does not stop the build; the report lists these under "Spec intent review"."""
        self.items.append({"level": "intent", "where": where, "msg": msg, "fix": fix})

    def errors(self):
        return [i for i in self.items if i["level"] == "error"]


# ───────────────────────────── normalisation ─────────────────────────────

def norm_choices(c, sets):
    if isinstance(c, str):
        c = sets.get(c, [])
    out = []
    for x in arr(c):
        if not isinstance(x, dict):
            out.append({"id": str(x), "label": titleize(x)})
        elif "id" in x:
            out.append({**x, "id": str(x["id"]), "label": str(x.get("label") or titleize(x["id"]))})
        elif len(x) == 1:
            k, v = next(iter(x.items()))
            item = {"id": str(k), "label": v if isinstance(v, str) else (v or {}).get("label") or titleize(k)}
            if isinstance(v, dict):
                item.update({kk: vv for kk, vv in v.items() if kk != "label"})
            out.append(item)
    return out


ARITH_RE = re.compile(r"^\s*[A-Za-z_][\w.]*(\s*[-+*/]\s*([A-Za-z_][\w.]*|\d+(\.\d+)?))+\s*$")


def norm_field(f, sets):
    f = dict(f)
    f["type"] = f.get("type") or "text"
    f["label"] = f.get("label") or titleize(f["key"])
    if "choices" in f:
        f["choice_set"] = f["choices"] if isinstance(f["choices"], str) else None
        f["choices"] = norm_choices(f["choices"], sets)
    f["required"] = bool(f.get("required"))
    f["readonly"] = bool(f.get("readonly"))
    if f.get("computed") is not None:
        comp = str(f["computed"])
        f["computed"] = {"expr": comp} if ARITH_RE.match(comp) else {"text": comp}
    if f.get("limit_choices"):
        f["limit_choices_src"] = f["limit_choices"]
    return f


def norm_codes(lst):
    out = []
    for s in arr(lst):
        if isinstance(s, str):
            out.append({"code": s})
        elif isinstance(s, dict) and "code" in s:
            out.append(dict(s))
        elif isinstance(s, dict) and len(s) == 1:
            k, v = next(iter(s.items()))
            out.append({"code": k, **(v if isinstance(v, dict) else {})})
    return out


def norm_access(a):
    if not a:
        return None
    out = OrderedDict()
    items = []
    if isinstance(a, list):
        for o in a:
            if isinstance(o, dict):
                items += list(o.items())
    else:
        items = list(a.items())
    for role, v in items:
        if v == "none" or v is None or (isinstance(v, dict) and v.get("no_access")):
            out[role] = {"actions": [], "rows": None, "none": True}
        else:
            out[role] = {"actions": [x for x in arr(v.get("actions") or v.get("can"))],
                         "rows": v.get("rows"), "none": False}
    return out


def norm_entity(e, mod, sets):
    E = copy.deepcopy(e)
    E["code"] = e["code"]
    E["name"] = e.get("name") or titleize(e["code"])
    E["plural"] = e.get("plural") or E["name"] + "s"
    E["kind"] = e.get("kind") or "transactional"
    E["module"] = mod["code"]
    E["fields"] = [norm_field(f, sets) for f in kv(e.get("fields"))]
    E["fmap"] = {f["key"]: f for f in E["fields"]}
    fm = E["fmap"]
    E["display"] = e.get("display") or ("name" if "name" in fm else next(
        (f["key"] for f in E["fields"] if f["type"] == "text"), "id"))

    w = e.get("workflow")
    if w:
        st = [{**s, "label": s.get("label") or titleize(s["code"]), "color": s.get("color") or "gray",
               "initial": bool(s.get("initial") or s.get("start")), "final": bool(s.get("final"))}
              for s in norm_codes(w.get("statuses") or w.get("states"))]
        initial = next((s["code"] for s in st if s["initial"]), st[0]["code"] if st else None)
        trs = []
        for t in arr(w.get("transitions") or w.get("steps")):
            t = dict(t)
            t["name"] = t.get("name") or slug(t.get("label") or t.get("do") or "step")
            t["label"] = t.get("label") or t.get("do") or titleize(t["name"])
            t["from"] = [str(x) for x in arr(t.get("from"))]
            t["roles"] = arr(t.get("roles") or t.get("by"))
            t["form"] = [norm_field(f, sets) for f in kv(t.get("form") or t.get("collects"))]
            t["system"] = t.get("trigger") == "system" or bool(t.get("automatic"))
            trs.append(t)
        tags = []
        for tg in norm_codes(w.get("tags") or w.get("labels")):
            tg["label"] = tg.get("label") or titleize(tg["code"])
            tg["color"] = tg.get("color") or "gray"
            for side in ("enable", "disable"):
                sd = tg.get(side)
                tg[side] = ({**sd, "roles": arr(sd.get("roles")),
                             "form": [norm_field(f, sets) for f in kv(sd.get("form"))]} if sd else None)
            tags.append(tg)
        E["workflow"] = {"statuses": st, "initial": initial, "transitions": trs, "tags": tags}
    else:
        E["workflow"] = None

    tb = dict(e.get("table") or {})
    cols = kv(tb.get("columns"))
    if not cols:
        cols = [{"key": f["key"]} for f in E["fields"]
                if f["type"] not in ("long_text", "json", "file", "image")][:6]
        if E["workflow"]:
            cols.append({"key": "status"})
    ncols = []
    for c in cols:
        src = c.get("source") or c.get("as")
        if src == "custom":
            src = "computed"
        if not src:
            if c["key"] == "status" and E["workflow"]:
                src = "status"
            elif c["key"] == "tags" and E["workflow"]:
                src = "tags"
            elif c["key"] in fm or c["key"] in BUILTIN:
                src = "field"
            elif c.get("path"):
                src = "path"
            else:
                src = "computed"
        if src == "computed" and c.get("path"):
            src = "path"
        f = fm.get(c["key"]) or BUILTIN.get(c["key"])
        ncols.append({**c, "source": src,
                      "label": c.get("label") or (f or {}).get("label") or titleize(c["key"]),
                      "roles": arr(c.get("roles")) or None})
    tb["columns"] = ncols
    tb["quick_filters"] = [{**q, "key": q.get("key") or slug(q.get("label") or f"qf{i}"),
                            "roles": arr(q.get("roles")) or None}
                           for i, q in enumerate(arr(tb.get("quick_filters")))]
    ras = []
    for a in arr(tb.get("row_actions") or tb.get("can_do")):
        a = dict(a)
        a["key"] = a.get("key") or slug(a.get("label") or a.get("do") or "action")
        a["label"] = a.get("label") or a.get("do") or titleize(a["key"])
        a["roles"] = arr(a.get("roles") or a.get("by")) or None
        a["type"] = a.get("type") or a.get("kind") or "confirm"
        a["form"] = [norm_field(f, sets) for f in kv(a.get("form"))]
        ras.append(a)
    tb["row_actions"] = ras
    tb["footer_totals"] = arr(tb.get("footer_totals"))
    E["table"] = tb
    E["access"] = norm_access(e.get("access") or tb.get("access"))
    E["form"] = copy.deepcopy(e.get("form") or {})
    E["validation"] = copy.deepcopy(e.get("validation") or {})
    E["custom_requirements"] = arr(e.get("custom_requirements"))
    return E


def form_items(E, fc, depth=0):
    """Resolve a create/edit form block to [{title, fields:[{key, ...override}]}]."""
    if not fc or depth > 3:
        return []
    if fc.get("same_as") and E["form"].get(fc["same_as"]):
        base = dict(E["form"][fc["same_as"]])
        merged = {**base, **{k: v for k, v in fc.items() if k not in ("same_as", "fields", "sections")}}
        if "fields" not in fc and "sections" not in fc:
            merged["fields"] = base.get("fields")
            merged["sections"] = base.get("sections")
        return form_items(E, merged, depth + 1)
    if fc.get("sections"):
        return [{"title": s.get("title"), "fields": kv(s.get("fields"))} for s in arr(fc["sections"])]
    return [{"title": None, "fields": kv(fc.get("fields"))}]


# ───────────────────────────── the checker ─────────────────────────────

class Spec:
    def __init__(self, raw, path):
        self.raw = raw
        self.path = path
        self.L = Linter()
        self.holes = []
        self.M = None

    # ---------- build ----------
    def build(self):
        s = self.raw
        L = self.L
        if not isinstance(s, dict):
            L.error("(root)", "the spec is not a YAML mapping")
            return
        def scan(node, where):
            # `{ text: a, b }` in YAML flow style splits at the comma: "b" becomes a key with no value
            if isinstance(node, dict):
                for k, v in node.items():
                    if v is None and isinstance(k, str) and " " in k.strip():
                        L.error(where, f"text was cut at a comma: {k!r} became a separate key",
                                "Quote the whole value: text: \"…, …\" (commas end a value inside { }).")
                    scan(v, f"{where}.{k}" if where else str(k))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    key = next(iter(v), None) if isinstance(v, dict) and len(v) == 1 else (v.get("code") or v.get("key") or v.get("name")) if isinstance(v, dict) else None
                    scan(v, f"{where}.{key}" if key else f"{where}[{i}]")
        scan(s, "")
        if s.get("spec_version") not in (1, "1"):
            L.warn("spec_version", f"expected spec_version: 1, got {s.get('spec_version')!r}")
        app = dict(s.get("app") or {})
        if not app.get("code"):
            L.error("app.code", "app.code is missing", "Add app.code (snake_case, e.g. vendor_hub).")
        elif not is_ident(app["code"]):
            L.error("app.code", f"app.code {app['code']!r} must be snake_case")
        app.setdefault("name", titleize(app.get("code", "app")))
        app.setdefault("locale", "en-US")
        app.setdefault("currency", "USD")
        app.setdefault("timezone", "UTC")
        app["theme"] = dict(app.get("theme") or {})
        app["theme"].setdefault("primary", "#4F46E5")
        ui = dict(app.get("ui") or {})
        for key, allowed, default in (("radius", UI_RADIUS, "rounded"), ("density", UI_DENSITY, "comfortable")):
            if ui.get(key) is not None and ui[key] not in allowed:
                L.error(f"app.ui.{key}", f"app.ui.{key} {ui[key]!r} is not one of {', '.join(allowed)}")
            ui[key] = ui[key] if ui.get(key) in allowed else default
        unknown = sorted(set(ui) - {"radius", "density"})
        if unknown:
            L.warn("app.ui", f"app.ui does not know {', '.join(unknown)} (only radius and density)")
        app["ui"] = {"radius": ui["radius"], "density": ui["density"]}
        if app.get("design") is not None:
            css, font_url, bad = design_css(app.get("design"))
            for b in bad:
                L.warn("app.design", b)
            brand = str(((app.get("design") or {}).get("tokens") or {}).get("brand") or "")
            if re.match(r"^#[0-9A-Fa-f]{6}$", brand):
                app["theme"]["primary"] = brand  # the runtime's --brand and every ramp follow it
            app["design_ui"] = {"css": css, "font_url": font_url,
                                "fonts": (app.get("design") or {}).get("fonts") or {}}
        sets = {k: norm_choices(v, {}) for k, v in (s.get("choice_sets") or {}).items()}

        roles = s.get("roles") or []
        if isinstance(roles, dict):
            roles = [{"name": k, **(v or {})} for k, v in roles.items()]
        R = OrderedDict()
        for r in roles:
            name = r.get("name") or r.get("code")
            if not name:
                L.error("roles", "a role has no name")
                continue
            if name in R:
                L.error(f"roles.{name}", "duplicate role name")
            if name in ("AnonymousUsers", "SystemUsers"):
                L.error(f"roles.{name}", f"{name} is a framework role and cannot be declared")
            if len(name) > 50:
                L.error(f"roles.{name}", "role names must be 50 characters or fewer")
            R[name] = {**r, "name": name, "menu": arr(r.get("menu")), "slug": slug(name)}

        mods, ents = [], OrderedDict()
        for mod in arr(s.get("modules")):
            if not mod or not mod.get("code"):
                L.error("modules", "a module has no code")
                continue
            m = {k: v for k, v in mod.items() if k != "entities"}
            m["name"] = m.get("name") or titleize(m["code"])
            m["url"] = url_part(m["code"])
            m["entities"] = []
            if not is_ident(m["code"]):
                L.error(f"modules.{m['code']}", "module code must be snake_case")
            if m["code"] in ("app", "zas_core", "packages"):
                L.error(f"modules.{m['code']}", f"module code {m['code']!r} is reserved")
            if any(x["code"] == m["code"] for x in mods):
                L.error(f"modules.{m['code']}", "duplicate module code")
            mods.append(m)
            for e in arr(mod.get("entities")):
                if not e or not e.get("code"):
                    L.error(f"modules.{m['code']}", "an entity has no code")
                    continue
                if e["code"] in ents:
                    L.error(f"entities.{e['code']}", "duplicate entity code (codes are app-wide)")
                    continue
                E = norm_entity(e, m, sets)
                ents[E["code"]] = E
                m["entities"].append(E["code"])

        pages = OrderedDict()
        for p in arr(s.get("pages")):
            if not p or not p.get("code"):
                L.error("pages", "a page has no code")
                continue
            P = dict(p)
            if P.get("type") == "dashboard":
                # A declared dashboard (blocks of KPIs, charts and lists) is built as a custom
                # page whose text is its blocks, until the runtime ships a dashboard component.
                P["declared"] = "dashboard"
                P["type"] = "custom"
                P["component"] = P.get("component") or "Dashboard" + pascal(P["code"])
                P["blocks"] = arr(P.get("blocks"))
                P["text"] = dashboard_text(P)
            P["title"] = P.get("title") or (ents.get(P.get("entity"), {}).get("plural")) or titleize(P["code"])
            P["export"] = P.get("component") if P.get("type") == "custom" and P.get("component") else "Page_" + P["code"]
            pages[P["code"]] = P
        dvs = OrderedDict()
        for v in arr(s.get("detail_views")):
            if not v or not v.get("code"):
                L.error("detail_views", "a detail view has no code")
                continue
            V = copy.deepcopy(v)
            V["tabs"] = arr(V.get("tabs"))
            dvs[V["code"]] = V
        for P in pages.values():
            if P.get("type") == "detail" and P.get("detail_view") in dvs:
                dvs[P["detail_view"]]["page"] = P["code"]
            if P.get("type") == "crud" and P.get("entity") in ents and not ents[P["entity"]].get("list_page"):
                ents[P["entity"]]["list_page"] = P["code"]
        for V in dvs.values():
            H = ents.get(V.get("hero"))
            if H and not H.get("detail_view"):
                H["detail_view"] = V["code"]

        self.M = {"spec_version": 1, "skill_version": SKILL_VERSION, "app": app, "choice_sets": sets,
                  "roles": R, "modules": mods, "entities": ents, "pages": pages, "detail_views": dvs,
                  "app_custom_requirements": arr(app.get("custom_requirements")),
                  "prototype_raw": s.get("prototype")}

    # ---------- path resolution ----------
    def resolve(self, E, path, allow_form=False, allow_reverse=False, allow_txn=False):
        """Resolve a dotted path on entity E. Returns (kind, info) or (None, reason).

        kinds: field, builtin, status, tags, link-end, form, user, reverse, txn
        """
        ents = self.M["entities"]
        if path is None:
            return None, "empty path"
        path = str(path)
        if path.startswith("form."):
            if not allow_form:
                return None, "form.* is only valid inside a form (limit_choices, show_when)"
            key = path[5:]
            return ("form", E["fmap"].get(key)) if key in E["fmap"] else (None, f"form field {key!r} not on {E['code']}")
        if path == "current_user" or path.startswith("current_user."):
            return "user", path
        cur = E
        parts = path.split(".")
        for i, part in enumerate(parts):
            last = i == len(parts) - 1
            m = re.fullmatch(r"(\w+)\[(.*)\]", part)
            if m:
                if not allow_reverse:
                    return None, f"{part!r}: [filter] paths are only valid in detail views"
                child = ents.get(m.group(1))
                if not child:
                    return None, f"{m.group(1)!r} is not an entity"
                if not any(f["type"] == "link" and f.get("to") == cur["code"] for f in child["fields"]):
                    return None, f"{child['code']} has no link to {cur['code']}"
                flt = m.group(2).strip()
                try:
                    X.parse(flt)
                except X.ExprError:
                    try:  # a bare field means "<field> is_true": vendor_contact[is_primary]
                        X.parse(flt + " is_true")
                    except X.ExprError as ex:
                        return None, f"filter in {part!r}: {ex}"
                cur = child
                if last:
                    return "reverse", child
                continue
            if part == "status" and cur.get("workflow"):
                return ("status", cur) if last else (None, "status has no sub-fields")
            if part == "tags" and cur.get("workflow"):
                return ("tags", cur) if last else (None, "tags has no sub-fields")
            if part in BUILTIN:
                if part in ("created_by", "modified_by") and not last:
                    return "builtin", BUILTIN[part]
                return ("builtin", BUILTIN[part]) if last else (None, f"{part} has no sub-fields")
            f = cur["fmap"].get(part)
            if not f:
                if allow_txn and last and i == 0 and part in self._txn_fields(cur):
                    return "txn", part
                return None, f"{part!r} is not a field of {cur['code']}"
            if last:
                return "field", f
            if f["type"] == "link":
                if f.get("to") == "app_user":
                    return "field", f
                cur = ents.get(f.get("to"))
                if not cur:
                    return None, f"{part!r} links to unknown entity {f.get('to')!r}"
            else:
                return None, f"{part!r} is not a link, cannot go further"
        return None, "unresolved"

    def _txn_fields(self, E):
        out = set()
        wf = E.get("workflow") or {}
        for t in wf.get("transitions", []):
            out |= {f["key"] for f in t["form"]}
        for tg in wf.get("tags", []):
            for side in ("enable", "disable"):
                if tg.get(side):
                    out |= {f["key"] for f in tg[side]["form"]}
        return out

    def check_expr(self, E, src, where, allow_form=False, allow_reverse=False):
        """Parse and resolve an expression. Returns the AST or None."""
        if src is None:
            return None
        try:
            ast = X.parse_condition(src)
        except X.ExprError as ex:
            self.L.error(where, f"expression: {ex}", "Use the grammar in references/spec/expressions.md.")
            return None
        ents = self.M["entities"]
        for n in X.walk(ast):
            if n["op"] == "role" and n["role"] not in self.M["roles"]:
                self.L.error(where, f"unknown role {n['role']!r} in current_user.role")
            if n["op"] == "has_tag":
                target = E
                if n.get("path"):
                    k, info = self.resolve(E, n["path"])
                    if k != "field" or info.get("type") != "link":
                        self.L.error(where, f"has_tag: {n['path']!r} is not a link")
                        continue
                    target = ents.get(info.get("to"))
                wf = (target or {}).get("workflow")
                if not wf:
                    self.L.error(where, f"has_tag {n['tag']}: {target['code'] if target else '?'} has no workflow")
                elif n["tag"] not in {t["code"] for t in wf["tags"]}:
                    if n["tag"] in {s["code"] for s in wf["statuses"]}:
                        self.L.error(where, f"{n['tag']!r} is a status, not a tag",
                                     f"Write `status != {n['tag']}` (or `status == {n['tag']}`) instead of `has_tag {n['tag']}`.")
                    else:
                        self.L.error(where, f"unknown tag {n['tag']!r} on {target['code']}")
            if n["op"] in ("cmp", "in", "test"):
                k, info = self.resolve(E, n["path"], allow_form=allow_form, allow_reverse=allow_reverse)
                if k is None:
                    self.L.error(where, f"{n['path']!r}: {info}")
                    continue
                vals = n.get("values") or ([n["value"]] if "value" in n else [])
                if k == "status":
                    codes = {s["code"] for s in info["workflow"]["statuses"]}
                    for v in vals:
                        w = v.get("word", v.get("lit"))
                        if isinstance(w, str) and w not in codes:
                            self.L.error(where, f"{w!r} is not a status of {info['code']}")
                elif k == "field" and info.get("choices") and n["op"] != "test":
                    ids = {c["id"] for c in info["choices"]}
                    for v in vals:
                        w = v.get("word", v.get("lit"))
                        if isinstance(w, str) and "word" in v and w not in ids and w not in E["fmap"]:
                            self.L.error(where, f"{w!r} is not a choice of {n['path']}")
                for v in vals:
                    if "path" in v:
                        k2, i2 = self.resolve(E, v["path"], allow_form=allow_form)
                        if k2 is None:
                            self.L.error(where, f"{v['path']!r}: {i2}")
        return ast

    # ---------- lint ----------
    def lint_dashboard(self, P):
        """Every block of a declared dashboard names real entities, fields, pages and expressions."""
        ents, pages, L = self.M["entities"], self.M["pages"], self.L

        def ent(code, w):
            E = ents.get(code)
            if E is None:
                L.error(w, f"entity {code!r} not found")
            return E

        def path(E, p, w, what):
            if E is not None and p:
                kind, info = self.resolve(E, str(p).lstrip("-"))
                if kind is None:
                    L.error(w, f"{what} {p!r}: {info}")

        def go(target, w):
            if target and str(target).split(":")[0] not in pages:
                L.error(w, f"go {target!r} is not a page")

        def visit(b, w):
            if not isinstance(b, dict) or len(b) != 1 or next(iter(b)) not in DASH_BLOCKS:
                L.error(w, f"a block is exactly one of {', '.join(DASH_BLOCKS)}")
                return
            (k, v), = b.items()
            if k in ("grid", "stack"):
                for i, x in enumerate(arr(v)):
                    visit(x, f"{w}.{k}[{i}]")
                return
            if k == "panel":
                for i, x in enumerate(arr((v or {}).get("blocks"))):
                    visit(x, f"{w}.panel.blocks[{i}]")
                return
            if k == "kpis":
                for i, t in enumerate(arr(v)):
                    tw, val = f"{w}.kpis[{i}]", (t or {}).get("value") or {}
                    aggs = [a for a in DASH_AGGS if a in val]
                    if len(aggs) != 1:
                        L.error(tw, f"value needs exactly one of {', '.join(DASH_AGGS)}")
                        continue
                    target = str(val[aggs[0]])
                    if aggs[0] == "count":
                        E = ent(target, tw)
                    else:
                        code, _, field = target.partition(".")
                        E = ent(code, tw)
                        path(E, field, tw, aggs[0])
                    if E is not None and val.get("where"):
                        self.check_expr(E, val["where"], tw + ".where")
                    go(t.get("go"), tw)
                return
            v = v or {}
            bw = f"{w}.{k}"
            E = ent(v.get("entity"), bw)
            if E is None:
                return
            if v.get("where"):
                self.check_expr(E, v["where"], bw + ".where")
            for key in ("group_by", "sort", "primary", "secondary", "meta", "badge"):
                path(E, v.get(key), bw, key)
            for c in arr(v.get("columns")):
                path(E, c, bw, "column")
            if isinstance(v.get("value"), dict):
                path(E, v["value"].get("sum"), bw, "sum")
            if k in ("bars", "board") and not v.get("group_by"):
                L.error(bw, f"{k} needs group_by")
            if k == "list" and not v.get("primary"):
                L.error(bw, "list needs primary")
            if k == "table" and not arr(v.get("columns")):
                L.error(bw, "table needs columns")
            go(v.get("go"), bw)

        if not P["blocks"]:
            L.error(f"pages.{P['code']}", "a dashboard needs blocks")
        for i, b in enumerate(P["blocks"]):
            visit(b, f"pages.{P['code']}.blocks[{i}]")

    def lint(self):
        M, L = self.M, self.L
        ents, roles, pages, dvs = M["entities"], M["roles"], M["pages"], M["detail_views"]

        def chk_roles(where, lst):
            for r in arr(lst):
                if r not in roles:
                    L.error(where, f"unknown role {r!r}", f"Declare it under roles, or use one of: {', '.join(roles)}")

        if not roles:
            L.error("roles", "no roles defined")
        for r in roles.values():
            w = f"roles.{r['name']}"
            if r.get("landing") and r["landing"] not in pages:
                L.error(w + ".landing", f"page {r['landing']!r} not in pages")
            elif r.get("landing") and r["landing"] not in {i.get("page") for it in r["menu"] for i in arr(it.get("items") or [it])}:
                L.warn(w + ".landing", f"landing page {r['landing']!r} is not in the role's menu: it will be added first")
            for it in r["menu"]:
                for i in arr(it.get("items") or [it]):
                    if i.get("page") and i["page"] not in pages:
                        L.error(w + ".menu", f"page {i['page']!r} not in pages")
                    elif i.get("page") and pages[i["page"]].get("type") == "detail":
                        L.error(w + ".menu", f"page {i['page']!r} is a detail page: it needs a record, so it cannot be a menu item",
                                "put the hero's list page in the menu instead")
                    if i.get("icon") and not re.fullmatch(r"[a-z0-9-]+", str(i["icon"])):
                        L.warn(w + ".menu", f"icon {i['icon']!r} is not a lucide icon name")
            if not r["menu"]:
                L.warn(w, "role has no menu: its users land on an empty app")

        routes = {}
        for p in pages.values():
            w = f"pages.{p['code']}"
            t = p.get("type")
            if t not in PAGE_TYPES:
                L.error(w, f"unknown page type {t!r}")
            if t == "crud" and p.get("entity") not in ents:
                L.error(w, f"entity {p.get('entity')!r} not found")
            if t == "detail" and p.get("detail_view") not in dvs:
                L.error(w, f"detail_view {p.get('detail_view')!r} not found")
            if t == "custom" and not p.get("component"):
                L.warn(w, "custom page has no component name; Page_<code> will be used")
            if t == "custom" and not p.get("text"):
                L.warn(w, "custom page has no text: the agent has nothing to build from")
            r = p.get("route")
            if not r or not str(r).startswith("/app"):
                L.error(w, f"route {r!r} must start with /app")
            elif r in routes:
                L.error(w, f"route {r} also used by page {routes[r]}")
            else:
                routes[r] = p["code"]
            if p.get("roles"):
                chk_roles(w, p["roles"])
            if p.get("declared") == "dashboard":
                self.lint_dashboard(p)

        # Typed custom requirements: a trigger names a real entity, transition or tag.
        reqs = [(f"app.custom_requirements[{i}]", cr, None) for i, cr in enumerate(M["app_custom_requirements"])]
        for E in ents.values():
            reqs += [(f"entities.{E['code']}.custom_requirements[{i}]", cr, E) for i, cr in enumerate(E["custom_requirements"])]
        for w, cr, owner in reqs:
            trig = (cr or {}).get("trigger") if isinstance(cr, dict) else None
            if not isinstance(trig, dict):
                continue
            T = ents.get(trig.get("entity")) if trig.get("entity") else owner
            if trig.get("entity") and T is None:
                L.error(w + ".trigger", f"entity {trig['entity']!r} not found")
                continue
            wf = (T or {}).get("workflow") or {}
            if trig.get("event") == "transition" and trig.get("transition") not in {t["name"] for t in wf.get("transitions", [])}:
                L.error(w + ".trigger", f"{trig.get('transition')!r} is not a transition of {(T or {}).get('code', '?')}")
            if trig.get("event") == "tag" and trig.get("tag") not in {t["code"] for t in wf.get("tags", [])}:
                L.error(w + ".trigger", f"{trig.get('tag')!r} is not a tag of {(T or {}).get('code', '?')}")
            if trig.get("event") == "schedule" and not trig.get("cron"):
                L.error(w + ".trigger", "a scheduled requirement needs cron (e.g. \"0 2 * * *\")")

        for E in ents.values():
            self.lint_entity(E, chk_roles)

        for V in dvs.values():
            self.lint_dv(V, chk_roles)

        # role ↔ page consistency
        for r in roles.values():
            for it in r["menu"]:
                for i in arr(it.get("items") or [it]):
                    p = pages.get(i.get("page"))
                    if p and p.get("type") == "crud":
                        E = ents.get(p.get("entity"))
                        if E and E["access"] and r["name"] not in E["access"]:
                            L.warn(f"roles.{r['name']}.menu", f"menu has {p['code']} but {r['name']} has no access to {E['code']}")
                    if p and p.get("roles") and r["name"] not in p["roles"]:
                        L.warn(f"roles.{r['name']}.menu", f"page {p['code']} lists roles that exclude {r['name']}")

        # cross-module FK cycles (Python import cycles)
        deps = defaultdict(set)
        for E in ents.values():
            for f in E["fields"]:
                T = ents.get(f.get("to")) if f["type"] in ("link", "multi_link") else None
                if T and T["module"] != E["module"]:
                    deps[E["module"]].add(T["module"])
        order, seen, temp = [], set(), set()

        def visit(m, stack):
            if m in seen:
                return
            if m in temp:
                L.error("modules", "modules link to each other in a cycle: " + " → ".join(stack + [m]),
                        "Move the entities that close the cycle into one module.")
                return
            temp.add(m)
            for d in sorted(deps[m]):
                visit(d, stack + [m])
            temp.discard(m)
            seen.add(m)
            order.append(m)

        for m in M["modules"]:
            visit(m["code"], [])
        M["module_order"] = order

    def lint_entity(self, E, chk_roles):
        L, M = self.L, self.M
        ents, roles, dvs, pages = M["entities"], M["roles"], M["detail_views"], M["pages"]
        w = f"entities.{E['code']}"
        if not is_ident(E["code"]):
            L.error(w, "entity code must be snake_case")
        if E["kind"] not in KINDS:
            L.error(w, f"unknown kind {E['kind']!r}")
        for f in E["fields"]:
            fw = f"{w}.fields.{f['key']}"
            if not is_ident(f["key"]):
                L.error(fw, "field name must be snake_case")
            if f["key"] in RESERVED:
                L.error(fw, f"{f['key']!r} is reserved (built-in field or Django name)", "Rename the field.")
            if f["type"] not in FIELD_TYPES:
                L.error(fw, f"unknown type {f['type']!r}")
            if f["type"] in ("link", "multi_link"):
                if f.get("to") != "app_user" and f.get("to") not in ents:
                    L.error(fw, f"links to unknown entity {f.get('to')!r}")
                if f["type"] == "multi_link":
                    L.warn(fw, "multi_link becomes a mapping model (Zango has no ManyToMany)")
                if f.get("on_delete") and f["on_delete"] not in ("cascade", "protect", "set_null"):
                    L.error(fw, f"on_delete must be cascade, protect or set_null")
                if f.get("display"):
                    T = ents.get(f.get("to"))
                    if T and f["display"] not in T["fmap"] and f["display"] not in BUILTIN:
                        L.error(fw, f"display {f['display']!r} is not a field of {T['code']}")
            if f["type"] in ("choice", "multi_choice"):
                if f.get("choice_set") and f["choice_set"] not in M["choice_sets"]:
                    L.error(fw, f"choice set {f['choice_set']!r} not found")
                elif not f.get("choices"):
                    L.error(fw, "choice field without choices")
                if f.get("default") is not None and f.get("choices") and str(f["default"]) not in {c["id"] for c in f["choices"]}:
                    L.error(fw, f"default {f['default']!r} is not one of the choices")
                for c in f.get("choices") or []:
                    if c.get("color") and c["color"] not in TONES:
                        L.warn(fw, f"choice colour {c['color']!r} is not a spec tone")
            if f.get("pattern"):
                try:
                    re.compile(f["pattern"])
                except re.error as ex:
                    L.error(fw, f"pattern does not compile: {ex}")
            if f.get("auto"):
                seq = (f["auto"] or {}).get("sequence")
                if not seq or not re.search(r"\{0+\}", str(seq)):
                    L.error(fw, "auto.sequence needs a {000…} counter, e.g. VEN-{00000}")
            if f.get("limit_choices"):
                if f["type"] != "link":
                    L.error(fw, "limit_choices only applies to link fields")
                else:
                    T = ents.get(f.get("to"))
                    if T:
                        ast = self.check_expr(T, f["limit_choices"], fw + ".limit_choices", allow_form=True)
                        if ast:
                            # form.* paths refer to THIS entity's form
                            for n in X.walk(ast):
                                for v in (n.get("values") or ([n["value"]] if "value" in n else [])):
                                    if "path" in v and v["path"].startswith("form.") and v["path"][5:] not in E["fmap"]:
                                        L.error(fw, f"{v['path']} is not a field of {E['code']}")
                            f["limit_choices"] = ast
            if f.get("label", "").endswith("yy") or re.search(r"\b(\w+)\1\b", f.get("label", "")):
                L.warn(fw, f"label {f['label']!r} looks like a typo")
            if f.get("computed") and not f.get("readonly"):
                L.warn(fw, "computed fields should be readonly")
            if f.get("default") == "today" and f["type"] not in ("date", "datetime"):
                L.error(fw, "default: today only works on date/datetime fields")

        if E["display"] not in E["fmap"] and E["display"] != "id":
            L.error(w, f"display field {E['display']!r} not found")
        if E.get("parent"):
            pe = E["parent"].get("entity")
            pf = E["parent"].get("field")
            if pe not in ents:
                L.error(w + ".parent", f"parent entity {pe!r} not found")
            elif pf not in E["fmap"] or E["fmap"][pf].get("to") != pe:
                L.error(w + ".parent", f"parent field {pf!r} must be a link to {pe}")
        if E["kind"] == "child" and not E.get("parent"):
            L.warn(w, "child entity without a parent block")
        au = E.get("app_user")
        if au:
            if au.get("role") not in roles:
                L.error(w + ".app_user", f"unknown role {au.get('role')!r}")
            for k in ("name", "email", "mobile"):
                if au.get(k) and au[k] not in E["fmap"]:
                    L.error(w + ".app_user", f"{k}: {au[k]!r} is not a field")
            if not au.get("email") and not au.get("mobile"):
                L.error(w + ".app_user", "needs email or mobile to create a login")
            co = au.get("create_on", "create")
            if co != "create":
                au["create_on_ast"] = self.check_expr(E, co, w + ".app_user.create_on")

        # access
        if E["access"]:
            for r, a in E["access"].items():
                aw = f"{w}.access.{r}"
                if r not in roles:
                    L.error(aw, f"unknown role {r!r}")
                for act in a["actions"]:
                    if act not in ACTIONS:
                        L.error(aw, f"unknown action {act!r}", f"Use one of {sorted(ACTIONS)}")
                if a["actions"] and "view" not in a["actions"]:
                    L.warn(aw, "actions without view: the role cannot open the list")
                rows = a["rows"]
                if rows in (None, "all", "created_by_me"):
                    continue
                if isinstance(rows, dict) and "own" in rows:
                    own = rows["own"]
                    owner = self._owner_entity(E, own)
                    if not owner:
                        L.error(aw + ".rows", f"own: {own!r} does not resolve to an entity")
                    elif not owner.get("app_user"):
                        L.error(aw + ".rows", f"own: {own!r} ends at {owner['code']}, which has no app_user block")
                    elif owner["app_user"].get("role") != r:
                        # `own` matches the record bound to the viewer's login; only `app_user.role` logins
                        # are bound, so for any other role this rule returns NO rows (it looks like saved
                        # records vanish). Suggest the usual intent: records whose parent names the user.
                        links = [f["key"] for f in owner["fields"] if f["type"] == "link" and f.get("to") == "app_user"]
                        hint = (f'rows: {{ where: "{own.replace("id", "").strip(".") + "." if own != "id" else ""}{links[0]} == current_user" }}'
                                if links else "a `where:` rule, or drop rows for an unscoped view")
                        L.error(aw + ".rows", f"own: {owner['code']} logins have role {owner['app_user'].get('role')!r}, "
                                f"not {r!r}: this role would see no rows", fix=f"Use {hint}.")
                elif isinstance(rows, dict) and "where" in rows:
                    rows["ast"] = self.check_expr(E, rows["where"], aw + ".rows.where")
                elif isinstance(rows, dict) and "text" in rows:
                    self.hole("rows", f"{w}.access.{r}.rows", rows["text"], E,
                              f"{E['code']}__rows__{slug(r)}", "(request, qs) -> qs")
                else:
                    L.error(aw + ".rows", f"cannot read rows {rows!r}")
        else:
            L.warn(w, "no access block: every role gets full access")

        # workflow
        wf = E["workflow"]
        if wf:
            ww = w + ".workflow"
            codes = {s["code"] for s in wf["statuses"]}
            if not wf["statuses"]:
                L.error(ww, "workflow has no statuses")
            if sum(1 for s in wf["statuses"] if s["initial"]) > 1:
                L.error(ww, "more than one initial status")
            for s in wf["statuses"]:
                if s["color"] not in TONES:
                    L.warn(ww, f"status {s['code']}: colour {s['color']!r} is not a spec tone")
            names = set()
            for t in wf["transitions"]:
                tw = f"{ww}.transitions.{t['name']}"
                if t["name"] in names:
                    L.error(tw, "duplicate transition name")
                names.add(t["name"])
                if not is_ident(t["name"]):
                    L.error(tw, "transition name must be snake_case")
                for fr in t["from"]:
                    if fr not in codes:
                        L.error(tw, f"from status {fr!r} not defined")
                if t.get("to") not in codes:
                    L.error(tw, f"to status {t.get('to')!r} not defined")
                if not t["from"]:
                    L.error(tw, "transition has no from")
                if t["system"]:
                    if t.get("roles"):
                        L.warn(tw, "system transition has roles: they are ignored")
                    self.hole("system_transition", tw, t.get("text") or f"When to move {t['from']} → {t['to']}", E,
                              f"{E['code']}__{t['name']}__run", "() -> int", sched=True)
                else:
                    chk_roles(tw, t["roles"])
                    if not t["roles"]:
                        L.warn(tw, "no roles: anyone with access can run it")
                if t.get("tone") and t["tone"] != "danger":
                    L.warn(tw, f"tone {t['tone']!r}: only `danger` is supported")
                if t.get("condition") is not None:
                    t["condition_ast"] = self.check_expr(E, t["condition"], tw + ".condition")
                    texts = X.text_nodes(t["condition_ast"]) if t["condition_ast"] else []
                    if texts:
                        self.hole("condition", tw + ".condition", " / ".join(texts), E,
                                  f"{E['code']}__{t['name']}__condition", "(request, obj) -> bool")
                    if not t.get("condition_msg"):
                        L.warn(tw, "condition without condition_msg: users won't see why it is blocked")
                if t.get("on_done"):
                    self.hole("on_done", tw + ".on_done", t["on_done"], E,
                              f"{E['code']}__{t['name']}__done", "(request, obj, form_data) -> None")
                same = [f["key"] for f in t["form"] if f["key"] in E["fmap"]]
                if same:
                    t["form_saves"] = same  # same-named fields are written to the record (contracts §6)
            prim = defaultdict(list)
            for t in wf["transitions"]:
                if t.get("primary"):
                    for fr in t["from"]:
                        prim[fr].append(t["name"])
            for fr, lst in prim.items():
                if len(lst) > 1:
                    L.warn(ww, f"status {fr}: more than one primary transition ({', '.join(lst)})")
            # engine expansion
            for t in wf["transitions"]:
                t["engine"] = ([{"name": t["name"], "from": t["from"][0]}] if len(t["from"]) == 1
                               else [{"name": f"{t['name']}__{fr}", "from": fr} for fr in t["from"]])
            tagcodes = set()
            for tg in wf["tags"]:
                tgw = f"{ww}.tags.{tg['code']}"
                if tg["code"] in tagcodes or tg["code"] in codes:
                    L.error(tgw, "tag code clashes with another tag or a status")
                tagcodes.add(tg["code"])
                if tg.get("system"):
                    self.hole("system_tag", tgw, tg.get("text") or f"When to set or clear {tg['label']}", E,
                              f"{E['code']}__tag_{tg['code']}__sync", "() -> int", sched=True)
                    continue
                for side in ("enable", "disable"):
                    sd = tg.get(side)
                    if not sd:
                        continue
                    chk_roles(tgw + "." + side, sd["roles"])
                    if sd.get("condition") is not None:
                        sd["condition_ast"] = self.check_expr(E, sd["condition"], f"{tgw}.{side}.condition")
                        tx = X.text_nodes(sd["condition_ast"]) if sd["condition_ast"] else []
                        if tx:
                            self.hole("tag_condition", f"{tgw}.{side}.condition", " / ".join(tx), E,
                                      f"{E['code']}__tag_{tg['code']}_{side}__condition", "(request, obj) -> bool")
                if not tg.get("enable"):
                    L.warn(tgw, "tag has no enable side and is not system: nobody can set it")

        # forms
        for kind in ("create", "edit"):
            fc = E["form"].get(kind)
            if not fc:
                continue
            fw = f"{w}.form.{kind}"
            if fc.get("roles"):
                chk_roles(fw, fc["roles"])
            secs = form_items(E, fc)
            keys = []
            for sec in secs:
                for it in sec["fields"]:
                    k = it["key"]
                    keys.append(k)
                    if k not in E["fmap"]:
                        L.error(fw, f"field {k!r} not found")
                        continue
                    f = E["fmap"][k]
                    if f.get("readonly") or f.get("auto") or f.get("computed"):
                        L.warn(fw, f"{k!r} is readonly/auto/computed and will not be editable on the form")
                    if it.get("show_when"):
                        it["show_when_ast"] = self.check_expr(E, it["show_when"], f"{fw}.{k}.show_when", allow_form=True)
            E["form"][kind + "_resolved"] = secs
            if kind == "create":
                prefilled = {p.get("field") for p in [E.get("parent") or {}] if p}
                for f in E["fields"]:
                    if f["required"] and not f.get("readonly") and not f.get("auto") and not f.get("computed") \
                            and f.get("default") is None and f["key"] not in keys and f["key"] not in prefilled:
                        L.warn(fw, f"required field {f['key']!r} is not on the create form and has no default: save will fail",
                               "Add it to the form, give it a default, or make it not required.")
                if fc.get("on_create"):
                    self.hole("on_create", fw + ".on_create", fc["on_create"], E,
                              f"{E['code']}__on_create", "(request, obj) -> None")
                ac = fc.get("after_create")
                if ac and ac not in ("list",) and ac not in dvs:
                    L.error(fw, f"after_create {ac!r} must be a detail view code or list")
            if kind == "edit":
                for st in arr(fc.get("editable_in")):
                    if not wf or st not in {s["code"] for s in wf["statuses"]}:
                        L.error(fw, f"editable_in: {st!r} is not a status")
                for i, rw in enumerate(arr(fc.get("readonly_when"))):
                    rw["ast"] = self.check_expr(E, rw.get("when"), f"{fw}.readonly_when[{i}]")
                    for k in arr(rw.get("fields")):
                        if k not in E["fmap"]:
                            L.error(fw, f"readonly_when field {k!r} not found")

        # validation
        v = E["validation"]
        for i, rule in enumerate(arr(v.get("rules"))):
            vw = f"{w}.validation.rules[{i}]"
            if rule.get("text"):
                self.hole("validation", vw, rule["text"], E, f"{E['code']}__validate__{i + 1}", "(form, cleaned) -> bool")
                if not rule.get("message"):
                    L.warn(vw, "text rule without message: the form error will be generic")
            if rule.get("when"):
                rule["when_ast"] = self.check_expr(E, rule["when"], vw + ".when")
            if rule.get("require_expr"):
                rule["require_ast"] = self.check_expr(E, rule["require_expr"], vw + ".require_expr")
            for k in arr(rule.get("require")):
                if k not in E["fmap"]:
                    L.error(vw, f"require: {k!r} not found")
            if rule.get("on_fail") and rule["on_fail"] not in ("block", "warn"):
                L.error(vw, "on_fail must be block or warn")
            if not rule.get("text") and not rule.get("require") and not rule.get("require_expr"):
                L.error(vw, "rule needs require, require_expr or text")
        dc = v.get("duplicate_check") or {}
        if dc:
            if (dc.get("scope") or {}).get("where"):
                dc["scope_ast"] = self.check_expr(E, dc["scope"]["where"], f"{w}.validation.duplicate_check.scope")
            for i, rule in enumerate(arr(dc.get("rules"))):
                dw = f"{w}.validation.duplicate_check.rules[{i}]"
                for k in arr(rule.get("match")):
                    kk, info = self.resolve(E, k)
                    if kk not in ("field", "builtin"):
                        L.error(dw, f"match {k!r}: {info}")
                if rule.get("compare", "exact") not in ("exact", "normalised", "fuzzy"):
                    L.error(dw, "compare must be exact, normalised or fuzzy")
                if rule.get("on_match", "block") not in ("block", "warn"):
                    L.error(dw, "on_match must be block or warn")
                if rule.get("compare") == "fuzzy" and not (0 < float(rule.get("threshold", 0.85)) <= 1):
                    L.error(dw, "threshold must be between 0 and 1")

        # computed fields
        for f in E["fields"]:
            c = f.get("computed")
            if not c:
                continue
            if "expr" in c:
                for tok in re.findall(r"[A-Za-z_][\w.]*", c["expr"]):
                    kk, info = self.resolve(E, tok)
                    if kk is None:
                        L.error(f"{w}.fields.{f['key']}.computed", f"{tok!r}: {info}")
            else:
                self.hole("computed", f"{w}.fields.{f['key']}.computed", c["text"], E,
                          f"{E['code']}__compute__{f['key']}", "(obj) -> value")

        # table
        tb = E["table"]
        tw = w + ".table"
        for c in tb["columns"]:
            cw = f"{tw}.columns.{c['key']}"
            if c["source"] not in COLUMN_SOURCES:
                L.error(cw, f"unknown source {c['source']!r}")
            if c["source"] == "field" and c["key"] not in E["fmap"] and c["key"] not in BUILTIN:
                L.error(cw, f"{c['key']!r} is not a field")
            if c["source"] in ("status", "tags") and not wf:
                L.error(cw, f"{c['source']} column needs a workflow")
            if c["source"] == "path":
                kk, info = self.resolve(E, c.get("path"))
                if kk is None:
                    L.error(cw, f"path {c.get('path')!r}: {info}")
            if c["source"] == "computed":
                if not c.get("shows"):
                    L.error(cw, "computed column needs `shows` describing the value")
                else:
                    self.hole("column", cw, c["shows"], E, f"{E['code']}__col__{c['key']}", "(obj) -> value")
            if c.get("link_to") and c["link_to"] not in dvs:
                L.error(cw, f"link_to {c['link_to']!r} is not a detail view")
            if c.get("format") not in FORMATS:
                L.error(cw, f"unknown format {c.get('format')!r}")
            if c.get("display"):
                f = E["fmap"].get(c["key"])
                T = ents.get((f or {}).get("to"))
                if not T or (c["display"] not in T["fmap"] and c["display"] not in BUILTIN):
                    L.error(cw, f"display {c['display']!r} does not resolve")
            if c.get("highlight"):
                c["highlight"]["ast"] = self.check_expr(E, c["highlight"].get("when"), cw + ".highlight")
            if c.get("roles"):
                chk_roles(cw, c["roles"])
        ds = tb.get("default_sort")
        if ds and ds.lstrip("-") not in E["fmap"] and ds.lstrip("-") not in BUILTIN:
            L.error(tw + ".default_sort", f"{ds!r} is not a field")
        for q in tb["quick_filters"]:
            q["ast"] = self.check_expr(E, q.get("where"), f"{tw}.quick_filters.{q['key']}")
            if q.get("roles"):
                chk_roles(f"{tw}.quick_filters.{q['key']}", q["roles"])
        rc = tb.get("row_click")
        if rc and "#" in str(rc):
            # <view>#<tab>: the row opens its parent's 360 on the tab that lists this entity
            vc, tc = str(rc).split("#", 1)
            V = dvs.get(vc)
            tab = next((t for t in arr((V or {}).get("tabs")) if t.get("code") == tc), None)
            if not V:
                L.error(tw + ".row_click", f"{rc!r}: {vc!r} is not a detail view")
            elif not tab or tab.get("type") != "related_table" or tab.get("entity") != E["code"]:
                L.error(tw + ".row_click", f"{rc!r}: {vc} has no related_table tab {tc!r} listing {E['code']}",
                        f"use <view>#<tab> where the tab lists {E['code']}, or a detail view, drawer or none")
        elif rc and rc not in ("none", "drawer") and rc not in dvs:
            L.error(tw + ".row_click", f"{rc!r} is not a detail view, <view>#<tab>, none or drawer")
        for k in tb["footer_totals"]:
            if k not in E["fmap"]:
                L.error(tw + ".footer_totals", f"{k!r} is not a field")
        keys = set()
        for a in tb["row_actions"]:
            aw = f"{tw}.row_actions.{a['key']}"
            if a["key"] in keys:
                L.error(aw, "duplicate row action key")
            keys.add(a["key"])
            if a["type"] not in ROW_ACTION_TYPES:
                L.error(aw, f"unknown type {a['type']!r}")
            if a.get("roles"):
                chk_roles(aw, a["roles"])
            if a.get("show_when"):
                a["show_when_ast"] = self.check_expr(E, a["show_when"], aw + ".show_when")
            if a["type"] == "edit" and not E["form"].get("edit"):
                L.error(aw, "edit action but the entity has no form.edit")
            if a["type"] == "navigate":
                to = a.get("to")
                if isinstance(to, dict):
                    if to.get("field") not in E["fmap"]:
                        L.error(aw, f"navigate to field {to.get('field')!r} not found")
                elif to not in dvs and to not in pages and not str(to or "").startswith(("http", "/")):
                    L.error(aw, f"navigate to {to!r} is not a detail view, page or URL")
            if a["type"] == "form" and not a["form"]:
                L.error(aw, "form action has no form fields")
            if a["type"] in ("form", "confirm") and a.get("on_done"):
                self.hole("row_action", aw, a["on_done"], E, f"{E['code']}__action__{a['key']}",
                          "(request, obj, form_data) -> dict")
            if a["type"] == "download":
                self.hole("row_action", aw, a.get("text") or "Generate the file", E,
                          f"{E['code']}__action__{a['key']}", "(request, obj, form_data) -> HttpResponse")
            if a["type"] in ("form", "confirm") and not a.get("on_done"):
                L.warn(aw, f"{a['type']} action has no on_done: it will do nothing")

        for i, cr in enumerate(E["custom_requirements"]):
            self.hole("requirement", f"{w}.custom_requirements[{i}]",
                      f"[{cr.get('area', 'backend')}] {cr.get('title', '')}: {cr.get('text', '')}" + contract_text(cr), E,
                      f"{E['code']}__req__{i + 1}", "see text", area=cr.get("area"))

    def _owner_entity(self, E, own):
        if own == "id":
            return E
        k, info = self.resolve(E, own)
        if k == "field" and info.get("type") == "link":
            return self.M["entities"].get(info.get("to"))
        return None

    def lint_dv(self, V, chk_roles):
        L, M = self.L, self.M
        ents, dvs, pages = M["entities"], M["detail_views"], M["pages"]
        w = f"detail_views.{V['code']}"
        H = ents.get(V.get("hero"))
        if not H:
            L.error(w, f"hero entity {V.get('hero')!r} not found")
            return
        if not V.get("page"):
            L.warn(w, "no page of type detail points at this view")
        if V.get("layout", "header_tabs") not in LAYOUTS:
            L.error(w, f"unknown layout {V.get('layout')!r}")
        if V.get("roles"):
            chk_roles(w, V["roles"])
            for r in V["roles"]:
                acc = (H["access"] or {}).get(r)
                if H["access"] and (not acc or "detail" not in acc["actions"]):
                    L.warn(w, f"{r} is in roles but has no `detail` access on {H['code']}")
        if V.get("back_to") and V["back_to"] not in pages:
            L.error(w + ".back_to", f"page {V['back_to']!r} not found")

        hd = V.get("header") or {}
        txn_fields = self._txn_fields(H)

        def chk_tpl(where, tpl):
            for ph in re.findall(r"\{([^}]+)\}", str(tpl)):
                k, info = self.resolve(H, ph.strip(), allow_reverse=True, allow_txn=True)
                if k is None:
                    L.error(where, f"{{{ph}}}: {info}")
                elif k == "txn":
                    L.warn(where, f"{{{ph}}} is a transition form field: it shows the value from the latest transition that collected it")

        def chk_path(where, p):
            if not p:
                return
            if "{" in str(p):
                chk_tpl(where, p)
                return
            k, info = self.resolve(H, p, allow_reverse=True)
            if k is None:
                L.error(where, f"{p!r}: {info}")

        if hd.get("title"):
            chk_path(w + ".header.title", hd["title"])
        for s in arr(hd.get("subtitle")):
            chk_path(w + ".header.subtitle", s)
        av = hd.get("avatar") or {}
        for k in ("image", "fallback_initials"):
            if av.get(k):
                chk_path(w + ".header.avatar", av[k])
        for i, b in enumerate(arr(hd.get("badges"))):
            if b.get("source") in ("status", "tags") and not H["workflow"]:
                L.error(w + ".header.badges", f"{b['source']} badge needs a workflow")
            if b.get("field"):
                chk_path(w + ".header.badges", b["field"])
            if b.get("roles"):
                chk_roles(w + ".header.badges", b["roles"])
            if b.get("show_when"):
                b["show_when_ast"] = self.check_expr(H, b["show_when"], f"{w}.header.badges[{i}].show_when")
        for i, f in enumerate(arr(hd.get("facts"))):
            fw = f"{w}.header.facts[{i}]"
            if f.get("field"):
                chk_path(fw, f["field"])
            if f.get("path"):
                chk_path(fw, f["path"])
            if f.get("value"):
                chk_tpl(fw, f["value"])
            if f.get("link_to") and f["link_to"] not in dvs:
                L.error(fw, f"link_to {f['link_to']!r} is not a detail view")
            if f.get("roles"):
                chk_roles(fw, f["roles"])
            if f.get("show_when"):
                f["show_when_ast"] = self.check_expr(H, f["show_when"], fw + ".show_when")
        acts = hd.get("actions") or {}
        for i, b in enumerate(arr(acts.get("buttons"))):
            bw = f"{w}.header.actions.buttons[{i}]"
            if b.get("roles"):
                chk_roles(bw, b["roles"])
            if b.get("show_when"):
                b["show_when_ast"] = self.check_expr(H, b["show_when"], bw + ".show_when")
            if b.get("row_action") and b["row_action"] not in {a["key"] for a in H["table"]["row_actions"]}:
                L.error(bw, f"row_action {b['row_action']!r} is not a row action of {H['code']}")
            if b.get("type") == "create_related":
                T = ents.get(b.get("entity"))
                if not T:
                    L.error(bw, f"entity {b.get('entity')!r} not found")
                else:
                    for k, val in (b.get("prefill") or {}).items():
                        if k not in T["fmap"]:
                            L.error(bw, f"prefill {k!r} is not a field of {T['code']}")
                        elif val == "hero" and T["fmap"][k].get("to") != H["code"]:
                            L.error(bw, f"prefill {k}: hero is {H['code']} but {k} links to {T['fmap'][k].get('to')}")
                    self.add_parent(T, H, next((k for k, v in (b.get("prefill") or {}).items() if v == "hero"), None), bw)
        for i, b in enumerate(arr(hd.get("banners"))):
            bw = f"{w}.header.banners[{i}]"
            if b.get("tone", "info") not in BANNER_TONES:
                L.error(bw, f"banner tone must be one of {sorted(BANNER_TONES)}")
            b["show_when_ast"] = self.check_expr(H, b.get("show_when"), bw + ".show_when")
            chk_tpl(bw, b.get("text", ""))

        for i, s in enumerate(arr(V.get("stats"))):
            sw = f"{w}.stats[{i}]"
            val = s.get("value") or {}
            if val.get("count") or val.get("sum"):
                ent = val.get("count") or str(val.get("sum")).split(".")[0]
                T = ents.get(ent)
                if not T:
                    L.error(sw, f"entity {ent!r} not found")
                    continue
                if val.get("sum"):
                    fld = str(val["sum"]).split(".", 1)[1] if "." in str(val["sum"]) else None
                    if not fld or fld not in T["fmap"]:
                        L.error(sw, f"sum field {val['sum']!r} not found")
                self.add_parent(T, H, val.get("via"), sw)
                if val.get("where"):
                    val["where_ast"] = self.check_expr(T, val["where"], sw + ".where")
            elif val.get("field"):
                chk_path(sw, val["field"])
            elif val.get("text"):
                self.hole("stat", sw, val["text"], H, f"{V['code']}__stat__{i + 1}", "(request, obj) -> number | None",
                          module=H["module"])
            else:
                L.error(sw, "value needs count, sum, field or text")
            if s.get("link_to_tab") and s["link_to_tab"] not in {t.get("code") for t in V["tabs"]}:
                L.error(sw, f"link_to_tab {s['link_to_tab']!r} is not a tab")
            tn = s.get("tone")
            if isinstance(tn, str) and tn not in TONES:
                L.error(sw, f"tone {tn!r} is not a spec tone")
            if s.get("roles"):
                chk_roles(sw, s["roles"])

        def chk_section(sec, sw, key):
            t = sec.get("type", "fields")
            if t not in SECTION_TYPES:
                L.error(sw, f"unknown section type {t!r}")
            if sec.get("roles"):
                chk_roles(sw, sec["roles"])
            if sec.get("show_when"):
                sec["show_when_ast"] = self.check_expr(H, sec["show_when"], sw + ".show_when")
            if t == "fields":
                for it in kv(sec.get("fields")):
                    chk_path(sw, it["key"])
                ei = sec.get("editable_inline")
                if ei:
                    if ei.get("roles"):
                        chk_roles(sw, ei["roles"])
                    if ei.get("show_when"):
                        ei["show_when_ast"] = self.check_expr(H, ei["show_when"], sw + ".editable_inline")
            if t == "mini_table":
                T = ents.get(sec.get("entity"))
                if not T:
                    L.error(sw, f"entity {sec.get('entity')!r} not found")
                    return
                self.add_parent(T, H, sec.get("via"), sw)
                for c in arr(sec.get("columns")):
                    ck = c if isinstance(c, str) else next(iter(c))
                    if ck not in T["fmap"] and ck not in BUILTIN and ck not in ("status", "tags") \
                            and ck not in {x["key"] for x in T["table"]["columns"]}:
                        L.error(sw, f"column {ck!r} not found on {T['code']}")
                if sec.get("see_all_tab") and sec["see_all_tab"] not in {x.get("code") for x in V["tabs"]}:
                    L.error(sw, f"see_all_tab {sec['see_all_tab']!r} is not a tab")
            if t == "custom":
                self.hole("custom_panel", sw, f"{sec.get('title', '')}: {sec.get('text', '')}" + contract_text(sec), H,
                          f"{V['code']}__custom__{key}", "(request, obj) -> dict", module=H["module"],
                          slot=pascal(sec.get("title") or key))
            if t == "timeline":
                self.chk_sources(H, sec.get("sources"), sw)

        for i, sec in enumerate(arr(V.get("sidebar"))):
            chk_section(sec, f"{w}.sidebar[{i}]", f"sidebar_{i + 1}")
        if V.get("sidebar") and V.get("layout", "header_tabs") == "header_tabs":
            L.warn(w, "sidebar is ignored by layout header_tabs")

        codes = set()
        for t in V["tabs"]:
            tw = f"{w}.tabs.{t.get('code')}"
            if not t.get("code"):
                L.error(w + ".tabs", "a tab has no code")
                continue
            if t["code"] in codes:
                L.error(tw, "duplicate tab code")
            codes.add(t["code"])
            tt = t.get("type")
            if tt not in TAB_TYPES:
                L.error(tw, f"unknown tab type {tt!r}")
            if t.get("roles"):
                chk_roles(tw, t["roles"])
            if t.get("show_when"):
                t["show_when_ast"] = self.check_expr(H, t["show_when"], tw + ".show_when")
            if tt in ("summary", "fields"):
                for j, sec in enumerate(arr(t.get("sections"))):
                    chk_section(sec, f"{tw}.sections[{j}]", f"{t['code']}_{j + 1}")
            if tt == "timeline":
                self.chk_sources(H, t.get("sources"), tw)
            if tt == "custom":
                self.hole("custom_tab", tw, f"{t.get('label', t['code'])}: {t.get('text', '')}" + contract_text(t), H,
                          f"{V['code']}__custom__{t['code']}", "(request, obj) -> dict", module=H["module"],
                          slot=pascal(t.get("label") or t["code"]) + "Tab")
            if tt == "related_table":
                T = ents.get(t.get("entity"))
                if not T:
                    L.error(tw, f"entity {t.get('entity')!r} not found")
                    continue
                par = self.add_parent(T, H, t.get("via"), tw)
                if par:
                    t["param"] = par["param"]
                    t["preset"] = par.get("fk")
                cols = t.get("columns", "inherit")
                if isinstance(cols, list):
                    for c in cols:
                        ck = c if isinstance(c, str) else next(iter(c))
                        if ck not in T["fmap"] and ck not in BUILTIN and ck not in ("status", "tags") \
                                and ck not in {x["key"] for x in T["table"]["columns"]}:
                            L.error(tw, f"column {ck!r} not found on {T['code']}")
                add = t.get("add")
                if add not in (None, False):
                    add = add if isinstance(add, dict) else {}
                    if par and not par.get("fk") and not add.get("prefill"):
                        L.warn(tw, f"add on a two-hop tab (via {t.get('via')}): the parent cannot be preset; the user will pick it")
                    for k, val in (add.get("prefill") or {}).items():
                        if k not in T["fmap"]:
                            L.error(tw, f"prefill {k!r} is not a field of {T['code']}")
                    if add.get("roles"):
                        chk_roles(tw + ".add", add["roles"])
                    if add.get("show_when"):
                        add["show_when_ast"] = self.check_expr(H, add["show_when"], tw + ".add.show_when")
                    if not T["form"].get("create"):
                        L.error(tw, f"add is on but {T['code']} has no form.create")
                    t["add"] = add
                cb = t.get("count_badge")
                if isinstance(cb, dict) and cb.get("where"):
                    cb["ast"] = self.check_expr(T, cb["where"], tw + ".count_badge")
                rc = t.get("row_click")
                if rc and rc not in ("none", "drawer") and rc not in dvs \
                        and rc not in {a["key"] for a in T["table"]["row_actions"]}:
                    L.error(tw, f"row_click {rc!r} is not a detail view, row action, drawer or none")
                if t.get("group_by") and t["group_by"] not in T["fmap"]:
                    L.error(tw, f"group_by {t['group_by']!r} is not a field")
                if t.get("quick_filters") not in (None, "inherit") and not isinstance(t.get("quick_filters"), list):
                    L.error(tw, "quick_filters must be inherit or a list")
                for k in arr(t.get("footer_totals")):
                    if k not in T["fmap"]:
                        L.error(tw, f"footer_totals {k!r} is not a field")
                acc = T["access"]
                if acc and t.get("roles"):
                    for r in t["roles"]:
                        if r not in acc:
                            L.warn(tw, f"{r} sees this tab but has no access to {T['code']}")
        for i, cr in enumerate(arr(V.get("custom_requirements"))):
            self.hole("requirement", f"{w}.custom_requirements[{i}]",
                      f"[{cr.get('area', 'frontend')}] {cr.get('title', '')}: {cr.get('text', '')}" + contract_text(cr), H,
                      f"{V['code']}__req__{i + 1}", "see text", area=cr.get("area"), module=H["module"])

    def chk_sources(self, H, sources, where):
        for s in arr(sources):
            T = self.M["entities"].get(s.get("entity"))
            if not T:
                self.L.error(where, f"timeline source {s.get('entity')!r} not found")
                continue
            if T["code"] != H["code"] or s.get("via"):
                self.add_parent(T, H, s.get("via"), where, timeline=True)
            for ev in arr(s.get("events")):
                if ev not in ("created", "updated", "transition", "tag", "action"):
                    self.L.error(where, f"unknown timeline event {ev!r}")

    def add_parent(self, T, H, via, where, timeline=False):
        """Register the parent param on child T for hero H (contracts §3)."""
        if not via:
            links = [f["key"] for f in T["fields"] if f["type"] == "link" and f.get("to") == H["code"]]
            if len(links) == 1:
                via = links[0]
            else:
                self.L.error(where, f"via is missing and {T['code']} has {len(links)} links to {H['code']}")
                return None
        parts = str(via).split(".")
        cur = T
        for p in parts:
            f = cur["fmap"].get(p)
            if not f or f["type"] != "link":
                self.L.error(where, f"via {via!r} does not resolve on {T['code']} ({p!r} is not a link)")
                return None
            cur = self.M["entities"].get(f.get("to"))
            if not cur:
                self.L.error(where, f"via {via!r}: {p} links to an unknown entity")
                return None
        if cur["code"] != H["code"]:
            self.L.error(where, f"via {via!r} ends at {cur['code']}, expected {H['code']}")
            return None
        lookup = "__".join(parts) + "__object_uuid"
        pm = T.setdefault("parents", OrderedDict())
        for param, info in pm.items():
            if info["lookup"] == lookup:
                return info
        param = f"{H['code']}_uuid"
        if param in pm:
            param = f"{H['code']}__{parts[0]}_uuid"
        info = {"param": param, "lookup": lookup, "hero": H["code"], "via": via,
                "fk": parts[0] if len(parts) == 1 else None}
        pm[param] = info
        return info

    # ---------- holes ----------
    def hole(self, kind, where, text, E, fn, sig, sched=False, area=None, module=None, slot=None):
        mod = module or E["module"]
        frontend = kind in ("custom_panel", "custom_tab", "custom_page") or area == "frontend"
        if frontend and slot:
            target = f"frontend/src/custom/slots/{slot}.tsx::{slot}"
            backend = f"backend/{mod}/hooks.py::{fn}"
        elif area == "frontend":
            target = "frontend/src/custom/slots/ (see text)"
            backend = None
        else:
            target = f"backend/{mod}/{'tasks' if (sched or area == 'scheduled') else 'hooks'}.py::{fn}"
            backend = None
        self.holes.append({"kind": kind, "where": where, "text": " ".join(str(text).split()), "entity": E["code"],
                           "module": mod, "function": fn, "signature": sig, "target": target,
                           "data_hook": backend, "slot": slot, "scheduled": bool(sched or area == "scheduled")})

    def prototype_screens(self):
        """Open mode (SCHEMA.md, prototype): each prototype screen's build class. theme = the standard
        page in app.design's tokens; rebuild = the approved screen ported onto a slot (a custom page, or
        a standard page the analyst marked rebuild: true with a why); prototype-only = not built."""
        M, L = self.M, self.L
        raw = M.get("prototype_raw")
        if raw is None:
            M["prototype"] = None
            return
        rows, seen = [], set()
        for i, sc in enumerate(arr((raw or {}).get("screens"))):
            w = f"prototype.screens[{i}]"
            sid = str((sc or {}).get("id") or "")
            if not sid:
                L.error(w, "a prototype screen has no id")
                continue
            if sid in seen:
                L.error(w, f"screen {sid!r} is listed twice")
                continue
            seen.add(sid)
            why = str(sc.get("why") or "").strip()
            if sc.get("only") == "prototype":
                rows.append({"id": sid, "cls": "prototype-only", "reason": why or "not built",
                             "menu": sc.get("menu") if isinstance(sc.get("menu"), dict) else None})
                continue
            m = re.fullmatch(r"/(pages|detail_views)/@([A-Za-z0-9_]+)", str(sc.get("maps") or ""))
            if not m:
                L.error(w + ".maps", f"screen {sid!r} maps to {sc.get('maps')!r}",
                        "use /pages/@<code> or /detail_views/@<code>, or only: prototype with a why")
                continue
            kind, code = m.groups()
            row = {"id": sid, "maps": sc["maps"],
                   "not_built": [x for x in arr(sc.get("not_built")) if isinstance(x, dict)]}
            if kind == "pages":
                P = M["pages"].get(code)
                if not P:
                    L.error(w + ".maps", f"screen {sid!r}: page {code!r} not in pages")
                    continue
                if P["type"] == "detail" and P.get("detail_view") in M["detail_views"]:
                    row.update(kind="view", code=P["detail_view"], page=code)
                else:
                    row.update(kind="page", code=code, page=code)
                custom = P["type"] == "custom"
                what = {"crud": "list page", "detail": "360 page"}.get(P["type"], "dashboard" if P.get("declared") else "custom page")
            else:
                V = M["detail_views"].get(code)
                if not V:
                    L.error(w + ".maps", f"screen {sid!r}: detail view {code!r} not in detail_views")
                    continue
                row.update(kind="view", code=code, page=V.get("page") or M["entities"].get(V.get("hero"), {}).get("list_page"))
                custom, what = False, "360 page"
            if custom:
                row.update(cls="rebuild", reason=f"{what} in the spec")
            elif sc.get("rebuild"):
                if not why:
                    L.error(w, f"screen {sid!r}: rebuild: true needs a why (what the standard {what} can't show)")
                row.update(cls="rebuild", reason=why or "rebuild: true", forced=True)
            else:
                row.update(cls="theme", reason=f"standard {what} in app.design's tokens")
            rows.append(row)
        M["prototype"] = {"hash": (raw or {}).get("hash"), "screens": rows}

    def page_holes(self):
        done = set()
        for r in (self.M.get("prototype") or {}).get("screens") or []:
            if not r.get("forced") or (r["kind"], r["code"]) in done:
                continue
            done.add((r["kind"], r["code"]))
            comp = "Rebuild" + pascal(r["code"])
            if r["kind"] == "page":
                P = self.M["pages"][r["code"]]
                kind, where = "rebuild_page", f"pages.{r['code']}"
                text = (f"Rebuild list page {r['code']} ({P['title']}) from the approved prototype screen: {r['reason']}. "
                        f"Data: props.data = {{ entity, endpoint, page }}; rows with api.useTableRows(endpoint), "
                        "row actions and forms through the zas kit (RecordDrawer, ZasTable parts). The 360 route stays standard.")
            else:
                kind, where = "rebuild_view", f"detail_views.{r['code']}"
                text = (f"Rebuild 360 view {r['code']} from the approved prototype screen: {r['reason']}. "
                        "Data: props.zas (the 360 payload: header, stats, panels, actions), props.record, props.refresh; "
                        "transitions and actions through api.runTransition / runRowAction.")
            self.holes.append({"kind": kind, "where": where, "text": text, "entity": None, "module": None,
                               "function": comp, "signature": "SlotProps", "slot": comp,
                               "target": f"frontend/src/custom/slots/{comp}.tsx::{comp}", "data_hook": None,
                               "scheduled": False})
        for p in self.M["pages"].values():
            if p.get("type") == "custom":
                comp = p.get("component") or "Page_" + p["code"]
                self.holes.append({"kind": "custom_page", "where": f"pages.{p['code']}",
                                   "text": " ".join((str(p.get("text", "")) + contract_text(p)).split()), "entity": None, "module": None,
                                   "function": comp, "signature": "SlotProps", "slot": comp,
                                   "target": f"frontend/src/custom/slots/{comp}.tsx::{comp}", "data_hook": None,
                                   "scheduled": False})
        for i, cr in enumerate(self.M["app_custom_requirements"]):
            self.holes.append({"kind": "requirement", "where": f"app.custom_requirements[{i}]",
                               "text": f"[{cr.get('area', 'backend')}] {cr.get('title', '')}: {cr.get('text', '')}" + contract_text(cr),
                               "entity": None, "module": None, "function": f"app__req__{i + 1}", "signature": "see text",
                               "target": "backend/<module>/hooks.py (agent decides)", "data_hook": None, "slot": None,
                               "scheduled": cr.get("area") == "scheduled"})

    def number_holes(self, existing):
        """Stable IDs: keep the ID (and status) of a spec path seen before."""
        used = {v["id"] for v in existing.values()}
        nxt = max([int(i[2:]) for i in used] + [0]) + 1
        for h in self.holes:
            old = existing.get(h["where"])
            if old:
                h["id"], h["status"] = old["id"], old["status"]
            else:
                h["id"], h["status"] = f"H-{nxt:02d}", "todo"
                nxt += 1

    # ---------- derive ----------
    def derive(self):
        M = self.M
        ents = M["entities"]
        for E in ents.values():
            P = pascal(E["code"])
            mod = next(m for m in M["modules"] if m["code"] == E["module"])
            E["names"] = {
                "model": P, "view": P + "CrudView", "table": P + "Table", "form": P + "Form",
                "edit_form": P + "EditForm", "workflow": P + "Workflow", "detail": P + "Detail",
                "url": url_part(E["code"]) + "/", "endpoint": f"/{mod['url']}/{url_part(E['code'])}/",
                "url_name": E["code"],
            }
            E.setdefault("parents", OrderedDict())
            # policies: one per distinct feature set
            pol = OrderedDict()
            acc = E["access"] or OrderedDict((r, {"actions": sorted(ACTIONS), "rows": None, "none": False})
                                             for r in M["roles"])
            for r, a in acc.items():
                if a.get("none") or "view" not in a["actions"]:
                    continue
                feats = []
                if "add" in a["actions"] and (not (E["form"].get("create") or {}).get("roles")
                                              or r in E["form"]["create"]["roles"]):
                    feats.append("add")
                if "export" in a["actions"]:
                    feats.append("download")
                key = ",".join(feats)
                pol.setdefault(key, {"features": feats, "roles": []})["roles"].append(r)
            E["policies"] = [{"name": f"{P}Access{i + 1}", **v} for i, v in enumerate(pol.values())]
            E["access_resolved"] = acc
            # status tones
            if E["workflow"]:
                for s in E["workflow"]["statuses"]:
                    s["wf_color"] = WF_COLOR.get(s["color"], "gray")
            # module-level entity order (links inside the module first)
        for m in M["modules"]:
            order, seen = [], set()

            def visit(code, stack=()):
                if code in seen or code in stack:
                    return
                for f in ents[code]["fields"]:
                    t = f.get("to")
                    if f["type"] == "link" and t in ents and ents[t]["module"] == m["code"] and t != code:
                        visit(t, stack + (code,))
                seen.add(code)
                order.append(code)

            for c in m["entities"]:
                visit(c)
            m["entity_order"] = order

        # 360 tabs whose entity a 360 viewer cannot list: ZasDetail hides the tab for that role
        def can(code, role, action):
            E = ents.get(code)
            if not E or not E["access"]:
                return True
            a = E["access_resolved"].get(role)
            return bool(a) and not a.get("none") and action in a["actions"]
        dv_list = dvs.values() if isinstance((dvs := M["detail_views"]), dict) else dvs
        for V in dv_list:
            viewers = V.get("roles") or [r for r in M["roles"] if can(V["hero"], r, "detail")]
            for t in V.get("tabs") or []:
                if t.get("type") != "related_table" or not t.get("entity"):
                    continue
                hidden = [r for r in viewers if not can(t["entity"], r, "view")]
                if hidden:
                    self.L.warn(f"detail_views.{V['code']}.tabs.{t.get('code')}",
                                f"hidden for {', '.join(hidden)}: no view access to {t['entity']}",
                                f"add {', '.join(hidden)} to {t['entity']}.access with [view] if they should see it")

    # ---------- intent review ----------
    def intent(self):
        """Cross-checks between access, workflow, forms, tables and 360s: each finding is a place where
        the spec lets a role do something it cannot see (or see something it cannot reach)."""
        M, L = self.M, self.L
        ents = M["entities"]
        roles = [r for r in M["roles"] if r not in ("AnonymousUsers", "SystemUsers")]

        def acc(code, role):
            E = ents.get(code)
            if not E:
                return None
            if not E["access"]:
                return {"actions": list(ACTIONS), "rows": None}
            a = E["access_resolved"].get(role)
            return None if not a or a.get("none") else a

        def can(code, role, action):
            a = acc(code, role)
            return bool(a) and action in a["actions"]

        def blind(code, rs):
            return [r for r in rs or [] if r in M["roles"] and not can(code, r, "view")]

        for E in ents.values():
            c = E["code"]
            wf = E.get("workflow") or {}
            for t in wf.get("transitions", []):
                b = blind(c, t.get("roles"))
                if b and not t.get("system"):
                    L.intent(f"entities.{c}.workflow.transitions.{t['name']}.roles",
                             f"{', '.join(b)} may run {t['label']!r} but cannot see any {E['plural'].lower()}",
                             f"add [view] for {', '.join(b)} in {c}.access, or remove them from roles")
            for tg in wf.get("tags", []):
                for side in ("enable", "disable"):
                    b = blind(c, (tg.get(side) or {}).get("roles"))
                    if b:
                        L.intent(f"entities.{c}.workflow.tags.{tg['code']}.{side}.roles",
                                 f"{', '.join(b)} may {side} {tg['label']!r} but cannot see any {E['plural'].lower()}")
            cr = (E.get("form") or {}).get("create") or {}
            if E["access"]:
                adders = [r for r in roles if can(c, r, "add")]
                for r in cr.get("roles") or []:
                    if r in M["roles"] and r not in adders:
                        L.intent(f"entities.{c}.form.create.roles", f"{r} is in form.create.roles but has no add in access, so it gets no Add button",
                                 f"add add to {c}.access.{r}.actions, or drop {r} from form.create.roles")
                if cr.get("roles"):
                    for r in adders:
                        if r not in cr["roles"]:
                            L.intent(f"entities.{c}.access.{r}", f"{r} has add on {c} but is not in form.create.roles, so Add stays hidden")
                ed = (E.get("form") or {}).get("edit") or {}
                for r in ed.get("roles") or []:
                    if r in M["roles"] and not can(c, r, "edit"):
                        L.intent(f"entities.{c}.form.edit.roles", f"{r} is in form.edit.roles but has no edit in access, so Edit never shows")
                # a role that adds records it may not see afterwards
                for r in adders:
                    rows = (acc(c, r) or {}).get("rows")
                    if isinstance(rows, dict) and rows.get("ast"):
                        head = re.split(r"[\s.=!<>]", rows.get("where", "").strip(), 1)[0]
                        f = next((x for x in E["fields"] if x["key"] == head), None)
                        if f and f["type"] != "link" and head not in ("created_by",):
                            L.intent(f"entities.{c}.access.{r}.rows",
                                     f"{r} can add {E['plural'].lower()} but only sees rows where {rows['where']}: a record it adds "
                                     f"disappears from its list unless the form sets {head} that way",
                                     "scope by a parent link the form offers (e.g. site.<user link> == current_user), or by created_by_me")
            for a in (E.get("table") or {}).get("row_actions", []):
                b = blind(c, a.get("roles"))
                if b:
                    L.intent(f"entities.{c}.table.row_actions.{a['key']}.roles", f"{', '.join(b)} listed but cannot see any {E['plural'].lower()}")
            for q in (E.get("table") or {}).get("quick_filters", []):
                b = blind(c, q.get("roles"))
                if b:
                    L.intent(f"entities.{c}.table.quick_filters.{q['key']}.roles", f"quick filter for {', '.join(b)}, who cannot open this list")
            # a child listed wider than its parent: the role sees children of parents it cannot open
            par = (E.get("parent") or {}).get("entity")
            if par in ents and E["access"] and ents[par]["access"]:
                for r in roles:
                    ca, pa = acc(c, r), acc(par, r)
                    if ca and "view" in ca["actions"] and pa and pa.get("rows") not in (None, "all") and ca.get("rows") in (None, "all"):
                        L.intent(f"entities.{c}.access.{r}.rows",
                                 f"{r} sees every {E['name'].lower()} but only some {ents[par]['plural'].lower()} (rows on {par} are scoped)",
                                 f"scope {c} the same way, e.g. rows: {{ where: \"{E['parent'].get('field', par)}.<…> == current_user\" }}")
        for V in (M["detail_views"].values() if isinstance(M["detail_views"], dict) else M["detail_views"]):
            H = V["hero"]
            for r in V.get("roles") or []:
                if r in M["roles"] and not can(H, r, "detail"):
                    L.intent(f"detail_views.{V['code']}.roles", f"{r} is a 360 viewer but has no detail on {H}: it gets the no-access page")
            for b in ((V.get("header") or {}).get("actions") or {}).get("buttons") or []:
                if b.get("type") == "create_related" and b.get("entity") in ents:
                    no = [r for r in b.get("roles") or [] if r in M["roles"] and not can(b["entity"], r, "add")]
                    if no:
                        L.intent(f"detail_views.{V['code']}.header.actions.buttons.{b.get('key')}",
                                 f"{', '.join(no)} get {b.get('label')!r} but cannot add {b['entity']}")
            for t in V.get("tabs") or []:
                ad = t.get("add") or {}
                if t.get("entity") in ents and ad:
                    no = [r for r in ad.get("roles") or [] if r in M["roles"] and not can(t["entity"], r, "add")]
                    if no:
                        L.intent(f"detail_views.{V['code']}.tabs.{t.get('code')}.add.roles",
                                 f"{', '.join(no)} get {ad.get('label')!r} but cannot add {t['entity']}")

    # ---------- test plan (what Claude writes in test_fixtures.py / test_scenarios.py) ----------
    def test_plan_md(self):
        M = self.M
        ents = M["entities"]
        out = [f"# Test plan: {M['app']['name']}", "",
               "Written by spec_check from the spec. Claude turns it into `.zas/test_fixtures.py` (data the generated",
               "API tests cannot invent) and `.zas/test_scenarios.py` (one behaviour test per plain-language item).",
               "Contracts and helpers: references/testing.md §Fixtures and §Scenarios.", "",
               "## Fixture needs", ""]
        n = 0

        def paths(ast, acc):
            if isinstance(ast, dict):
                if ast.get("path"):
                    acc.add(ast["path"])
                for v in ast.values():
                    paths(v, acc)
            elif isinstance(ast, list):
                for v in ast:
                    paths(v, acc)
            return acc

        for E in ents.values():
            c = E["code"]
            for r, a in (E.get("access_resolved") or {}).items():
                rows = (a or {}).get("rows")
                if isinstance(rows, dict) and "current_user" in str(rows.get("where", "")):
                    n += 1
                    out.append(f"- **values({c})**: {r} only sees rows where `{rows['where']}`. Records the tests create for "
                               f"{r} must satisfy it (set the link to the test {r} user's pk from the form's options).")
                if isinstance(rows, dict) and "own" in rows and E.get("app_user") is None:
                    n += 1
                    out.append(f"- **record_for / bind**: {r} sees only records of its own `{rows['own']}`; bind the test {r} login "
                               "to the record the test uses (see the app_user note below).")
            if E.get("app_user"):
                au = E["app_user"]
                n += 1
                out.append(f"- **app_user {c}**: the test {au.get('role')} login is bound when a {c} with `{au.get('email')}` = the "
                           f"test user's email reaches `{au.get('create_on', 'create')}`. Create ONE such record for {au.get('role')} "
                           "tests (`bound_site`-style helper) and give other records a different email: a hook that disables the "
                           "login (e.g. on close-out) would otherwise lock the test user out.")
            for rule in (E.get("validation") or {}).get("rules") or []:
                if rule.get("text") or rule.get("require_expr"):
                    n += 1
                    out.append(f"- **values({c})**: generated values must pass `{rule.get('require_expr') or rule.get('text')}`.")
            saved = {}
            for t in (E.get("workflow") or {}).get("transitions", []):
                for k in t.get("form_saves") or [f["key"] for f in t.get("form") or []]:
                    saved.setdefault(k, t["name"])
            for t in (E.get("workflow") or {}).get("transitions", []):
                cond = t.get("condition")
                if not cond:
                    continue
                txt = cond.get("text") if isinstance(cond, dict) and "text" in cond else json.dumps(cond)[:160]
                txt = " ".join(str(txt).split()).strip('"')
                n += 1
                out.append(f"- **before_transition({c}, {t['name']})**: make `{txt}` true first.")
                for p in sorted(paths(t.get("condition_ast") or {}, set())):
                    if p in saved:
                        out.append(f"  - **transition_values({c}, {saved[p]})**: `{p}` comes from that form; post a value that passes.")
        if not n:
            out.append("None: the generated tests can create and walk every record on their own.")
        out += ["", "## Scenarios to write", "",
                "One `@scenario(\"H-NN\", \"…\")` per row (status `covered`/`blocked` excepted). Trigger, then assert:", "",
                "| Hole | Kind | Spec text | How to test |", "|---|---|---|---|"]
        how = {
            "condition": "walk the record to the `from` status: `ctx.transitions(e, uuid, role)[t]` is False; create the data the text asks for; now True",
            "on_done": "run the transition (`ctx.run`, with `data=` for a form); assert the field/tag/login/message the text names",
            "system_tag": "set up data on both sides of the rule; `ctx.call('<module>.tasks.<fn>')`; assert `ctx.tags` on each",
            "system_transition": "set up data; `ctx.call(...)` the task; assert `ctx.status`",
            "requirement": "trigger what the text describes (save, transition, `ctx.call` a scheduled task); assert the outcome or `ctx.outbox(since, event)`",
            "on_create": "create a record; assert the side effect",
            "computed": "create/change the inputs; assert `ctx.field(e, uuid, field)` equals the formula",
            "column": "assert the list row (`ctx.record(e, uuid, role)[col]`) shows the described value",
            "stat": "assert `ctx.detail(hero, uuid, role)['stats']` value against the formula",
            "custom_panel": "assert `ctx.detail(...)['custom'][key]` (items, counts, visibility) in two record states",
            "custom_tab": "assert `ctx.detail(...)['custom'][key]`",
            "custom_page": "call the page's data endpoint as each role in `pages[].roles` and one role outside them (expect 403)",
            "validation": "create values that break the rule; expect the refusal with the spec message",
            "rows": "as the role, list rows; assert only matching records appear",
            "row_action": "run the action; assert its result",
            "tag_condition": "toggle the tag before/after making the text true",
        }
        for h in self.holes:
            out.append(f"| {h['id']} | {h['kind']} | {h['text'][:140].replace('|', '/')} | {how.get(h['kind'], 'trigger it; assert what the text says')} |")
        return "\n".join(out) + "\n"

    # ---------- outputs ----------
    def _ui_column(self, E, c):
        """One list column for the React runtime: display keys plus what the toolbar needs
        (filterable → an inline filter; a link column carries its target entity)."""
        col = {k: c.get(k) for k in ("key", "label", "source", "format", "link_to", "display")
               if c.get(k) is not None}
        for k in ("filterable", "sortable", "searchable"):
            if c.get(k):
                col[k] = True
        f = next((x for x in E["fields"] if x["key"] == c["key"]), None) if c.get("source") == "field" else None
        if f:
            col["type"] = f["type"]
            if f["type"] == "link":
                col["to"] = f.get("to")
                col.setdefault("display", f.get("display") or (self.M["entities"].get(f.get("to"), {}).get("display")))
        return col

    def ui_json(self):
        M = self.M
        ents, dvs, pages = M["entities"], M["detail_views"], M["pages"]
        out = {"app": {"code": M["app"].get("code"), "name": M["app"]["name"],
                       "description": M["app"].get("description", ""), "locale": M["app"]["locale"],
                       "currency": M["app"]["currency"], "brand": M["app"]["theme"]["primary"], "ui": M["app"]["ui"],
                       **({"design": M["app"]["design_ui"]} if M["app"].get("design_ui") else {}),
                       "roles": [{"name": r["name"], "description": r.get("description", "")} for r in M["roles"].values()],
                       "modules": [{"code": m["code"], "name": m["name"], "description": m.get("description", "")}
                                   for m in M["modules"]]},
               "pages": {}, "entities": {}, "detail_views": {}, "slots": {}, "menus": {}}
        for p in pages.values():
            out["pages"][p["code"]] = {k: p.get(k) for k in ("type", "route", "title", "entity", "detail_view", "roles")
                                       if p.get(k) is not None}
            out["pages"][p["code"]]["export"] = p.get("component") if p.get("type") == "custom" and p.get("component") else p["export"]
        for E in ents.values():
            tb = E["table"]
            out["entities"][E["code"]] = {
                "name": E["name"], "plural": E["plural"], "kind": E["kind"], "endpoint": E["names"]["endpoint"],
                "display": E["display"], "list_page": E.get("list_page"), "detail_view": E.get("detail_view"),
                "statuses": {s["code"]: {"label": s["label"], "tone": s["color"]} for s in (E["workflow"] or {}).get("statuses", [])},
                "tags": {t["code"]: {"label": t["label"], "tone": t["color"]} for t in (E["workflow"] or {}).get("tags", [])},
                "choices": {f["key"]: {c["id"]: {"label": c["label"], "tone": c.get("color")} for c in f["choices"]}
                            for f in E["fields"] if f.get("choices")},
                "columns": [self._ui_column(E, c) for c in tb["columns"]],
                # every field, for the record drawer and inline filters (type, link target, display attr)
                "fields": [{k: v for k, v in {"key": f["key"], "label": f["label"], "type": f["type"],
                                              "to": f.get("to") if f["type"] == "link" else None,
                                              "display": f.get("display") if f["type"] == "link" else None}.items()
                            if v is not None} for f in E["fields"]],
                "quick_filters": [{"key": q["key"], "label": q["label"], "default": bool(q.get("default"))}
                                  for q in tb["quick_filters"]],
                "row_click": tb.get("row_click") or (E.get("detail_view") or "drawer"),
                "add_button": tb.get("add_button") or f"Add {E['name']}",
                "footer_totals": tb["footer_totals"],
                "parents": {k: {"hero": v["hero"], "fk": v["fk"]} for k, v in E["parents"].items()},
                "navigate": {a["key"]: a["to"] for a in tb["row_actions"]
                             if a["type"] == "navigate" and isinstance(a.get("to"), str)},
                "field_links": {a["key"]: a["to"]["field"] for a in tb["row_actions"]
                                if a["type"] == "navigate" and isinstance(a.get("to"), dict)},
                "downloads": [a["key"] for a in tb["row_actions"] if a["type"] == "download"],
            }
        for V in dvs.values():
            if V.get("hero") not in ents:
                continue
            tabs = []
            for t in V["tabs"]:
                T = {k: t.get(k) for k in ("code", "label", "type", "entity", "param", "columns", "row_click",
                                           "empty_state", "group_by", "footer_totals", "default_sort", "icon",
                                           "quick_filters", "page_size")
                     if t.get(k) is not None}
                T["label"] = t.get("label") or titleize(t["code"])
                if t.get("type") == "related_table":
                    add = t.get("add")
                    T["add"] = None if add in (None, False) else {"label": (add or {}).get("label") or f"Add {ents[t['entity']]['name']}",
                                                                   "prefill": (add or {}).get("prefill") or {}}
                    T["preset"] = t.get("preset")
                if t.get("type") == "custom":
                    T["slot"] = pascal(t.get("label") or t["code"]) + "Tab"
                tabs.append(T)
            side = []
            for i, s in enumerate(arr(V.get("sidebar"))):
                item = {"type": s.get("type", "fields"), "title": s.get("title"), "key": f"sidebar_{i + 1}"}
                if s.get("type") == "custom":
                    item["slot"] = pascal(s.get("title") or item["key"])
                side.append(item)
            out["detail_views"][V["code"]] = {
                "hero": V["hero"], "layout": V.get("layout", "header_tabs"), "back_to": V.get("back_to"),
                "page": V.get("page"), "states": V.get("states") or {}, "tabs": tabs, "sidebar": side,
                "sticky_header": any("sticky" in str(cr.get("title", "")).lower() for cr in arr(V.get("custom_requirements"))),
            }
        for h in self.holes:
            if h["kind"] == "rebuild_page" and h["where"][6:] in out["pages"]:
                out["pages"][h["where"][6:]]["rebuild"] = h["slot"]
            if h["kind"] == "rebuild_view" and h["where"][13:] in out["detail_views"]:
                out["detail_views"][h["where"][13:]]["rebuild"] = h["slot"]
        for h in self.holes:
            if h.get("slot"):
                out["slots"][h["slot"]] = {"export": h["slot"], "hole": h["id"], "kind": h["kind"],
                                           "data_key": h["function"].split("__custom__")[-1] if "__custom__" in h["function"] else None}
        for r in M["roles"].values():
            items = []
            for it in r["menu"]:
                if it.get("group"):
                    items.append({"group": it["group"], "icon": it.get("icon"),
                                  "items": [{"page": i["page"], "label": i.get("label") or pages.get(i["page"], {}).get("title"),
                                             "icon": i.get("icon")} for i in arr(it.get("items"))]})
                else:
                    items.append({"page": it.get("page"), "label": it.get("label") or pages.get(it.get("page"), {}).get("title"),
                                  "icon": it.get("icon")})
            out["menus"][r["name"]] = {"landing": r.get("landing"), "items": items}
        return out

    def plan_md(self, spec_hash):
        M = self.M
        ents = M["entities"]
        L = [f"# Build plan: {M['app']['name']} (`{M['app'].get('code')}`)", "",
             f"Spec hash `{spec_hash}` · skill {SKILL_VERSION} · generated {datetime.datetime.now():%Y-%m-%d %H:%M}", "",
             "## Module order", "", "Build modules in this order (links point backwards only):", ""]
        mods = {m["code"]: m for m in M["modules"]}
        for i, code in enumerate(M.get("module_order") or [m["code"] for m in M["modules"]]):
            m = mods[code]
            L.append(f"{i + 1}. `backend/{code}/` (URL `^{m['url']}/`): " + ", ".join(f"`{e}`" for e in m["entity_order"]))
        L += ["", "## Entities", "",
              "| Entity | Kind | Model | Endpoint | Workflow | 360 | Parent params |", "|---|---|---|---|---|---|---|"]
        for E in ents.values():
            wf = E["workflow"]
            wfs = f"{len(wf['statuses'])} statuses, {sum(len(t['engine']) for t in wf['transitions'])} engine transitions, {len(wf['tags'])} tags" if wf else "—"
            par = ", ".join(f"`{k}`→`{v['lookup']}`" for k, v in E["parents"].items()) or "—"
            L.append(f"| `{E['code']}` | {E['kind']} | `{E['names']['model']}` | `{E['names']['endpoint']}` | {wfs} | "
                     f"{E.get('detail_view') or '—'} | {par} |")
        L += ["", "## Policies", "", "| View | Policy | Roles | Features |", "|---|---|---|---|"]
        for E in ents.values():
            for p in E["policies"]:
                L.append(f"| `{E['names']['view']}` | `{p['name']}` | {', '.join(p['roles'])} | {', '.join(p['features']) or '—'} |")
        L += ["", "## Pages per role", ""]
        for r in M["roles"].values():
            items = []
            for it in r["menu"]:
                for i in arr(it.get("items") or [it]):
                    items.append(i.get("page"))
            L.append(f"- **{r['name']}** → lands on `{r.get('landing')}`; menu: " + ", ".join(f"`{x}`" for x in items if x))
        L += ["", "## Pages", "", "| Page | Type | Route | Component |", "|---|---|---|---|"]
        for p in M["pages"].values():
            comp = {"crud": "ZasListPage", "detail": "served by the hero's list page (detail-view route)",
                    "custom": "slot " + (p.get("component") or p["export"])}.get(p.get("type"), "?")
            L.append(f"| `{p['code']}` | {p.get('type')} | `{p.get('route')}` | {comp} |")
        n = defaultdict(int)
        for h in self.holes:
            n[h["kind"]] += 1
        L += ["", f"## Custom code: {len(self.holes)} holes", "",
              ", ".join(f"{k} {v}" for k, v in sorted(n.items())), "", "Details: `holes.md`.", ""]
        if (M.get("prototype") or {}).get("screens"):
            L += ["", proto_classes_md(M["prototype"]["screens"], [])]
        return "\n".join(L)

    def holes_md(self):
        L = ["# Holes", "", "Every plain-language item in the spec. Work them in Phase 4; keep the ID in the",
             "`# zas:hole H-NN` marker above the function. Status: todo → done | needs-review | blocked | covered (runtime already does it; say how in Text).", "",
             "| ID | Kind | Spec path | Text | Target | Signature | Status |", "|---|---|---|---|---|---|---|"]
        for h in self.holes:
            text = h["text"].replace("|", "\\|")
            tgt = h["target"] + (f" (data: `{h['data_hook']}`)" if h.get("data_hook") else "")
            L.append(f"| {h['id']} | {h['kind']} | `{h['where']}` | {text} | `{tgt}` | `{h['signature']}` | {h['status']} |")
        return "\n".join(L) + "\n"


BUNDLE_KINDS = ("custom_page", "custom_tab", "custom_panel")


def attach_bundle(holes, out):
    """Point each custom screen's hole at what the user approved for it (.zas/bundle/, written by the
    platform before this script runs): its sketch to port, its kit outline and its screenshots."""
    try:
        with open(os.path.join(out, "bundle", "manifest.json"), encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        return
    screens = {s["folder"].split("/", 1)[-1]: s for s in manifest.get("screens") or []}
    for h in holes:
        if h["kind"] not in BUNDLE_KINDS:
            continue
        folder = re.sub(r"\[(\d+)\]", r".\1", h["where"])
        s = screens.get(folder)
        if not s or not s.get("sketched"):
            continue
        h["bundle"] = f".zas/bundle/screens/{folder}/"
        note = (f" Approved look: `{h['bundle']}`. Before writing it, Read its shot.*.png and sketch.js: the"
                " build has to look like the screenshot. Port ui.* calls onto the zas kit and hand-drawn markup"
                " with the sketch's own styles (custom-code.md, \"Porting a sketch\").")
        if s.get("markup") or any(v.get("hand_written") for v in s.get("variants") or []):
            note += " It has hand-drawn parts (raw HTML and styles in the sketch): port them, do not simplify them."
        h["text"] += note


PROTO_CLASSES_START = "<!-- spec_check: build classes -->"


def attach_prototype(S, out):
    """Open mode (.zas/bundle/prototype/, written by the platform): point each rebuild hole at its approved
    screen, warn about screens the spec doesn't map, and write the theme / rebuild table into index.md."""
    bundle = os.path.join(out, "bundle", "prototype")
    try:
        with open(os.path.join(bundle, "manifest.json"), encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        return
    M, L = S.M, S.L
    proto = M.get("prototype")
    rows = (proto or {}).get("screens") or []
    listed = {r["id"] for r in rows}
    missing = [sc.get("id") for sc in manifest.get("screens") or [] if sc.get("id") and sc["id"] not in listed]
    if proto is None:
        L.warn("prototype", "open mode: the spec has no prototype.screens, so no screen is mapped to a page",
               "add prototype.screens (SCHEMA.md, prototype); until then every page is built standard and themed")
    elif missing:
        L.warn("prototype.screens", f"prototype screens not in prototype.screens: {', '.join(missing)}",
               "map each to its page, or mark it only: prototype with a why")
    by_target = {}
    for h in S.holes:
        by_target.setdefault(h["where"], h)
    for r in rows:
        if r["cls"] != "rebuild":
            continue
        where = f"pages.{r['page']}" if r["kind"] == "page" else f"detail_views.{r['code']}"
        h = by_target.get(where)
        if r["kind"] == "view" and not r.get("forced"):
            h = None
        if not h or h.get("bundle"):
            continue
        h["bundle"] = f".zas/bundle/prototype/screens/{r['id']}/"
        h["text"] += (f" Approved look: `{h['bundle']}` (prototype screen {r['id']}). Before writing it, Read its"
                      " shot.<role>.png and dom.<role>.html: port the markup onto the zas kit with this slot's data,"
                      " keep every data-zas-ref / data-zas-action marker, and take styles from css.used.css as zas"
                      " classes or token-only inline styles (open-mode.md, \"Screens\").")
        shows = must_show(os.path.join(bundle, "screens", r["id"]), r.get("not_built"))
        if shows:
            h["text"] += f" It must show, in these words: {shows}."
        r["slot"] = h["slot"]
    idx = os.path.join(bundle, "index.md")
    try:
        text = open(idx, encoding="utf-8").read()
    except OSError:
        return
    text = (text.split(PROTO_CLASSES_START)[0].rstrip() + "\n\n" + PROTO_CLASSES_START + "\n"
            + proto_classes_md(rows, missing) + soon_md(rows, manifest))
    with open(idx, "w", encoding="utf-8") as f:
        f.write(text)


def must_show(screen_dir, not_built=None):
    """A rebuilt screen's labels (proto_landmarks.py, over every role's dom), minus what the spec says
    it leaves out: what the slot must show."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import proto_landmarks as PL

    skip = {PL.norm(x.get("text")) for x in not_built or []}
    seen, out = set(), []
    try:
        names = sorted(f for f in os.listdir(screen_dir) if f.startswith("dom."))
    except OSError:
        return ""
    for f in names:
        marks = PL.landmarks(open(os.path.join(screen_dir, f), encoding="utf-8").read())
        for kind in ("heading", "column", "tab", "button", "label"):
            for t in marks.get(kind, []):
                if PL.norm(t) not in seen and PL.norm(t) not in skip:
                    seen.add(PL.norm(t))
                    out.append(f"{kind} '{t}'")
    return ", ".join(out)


def soon_items(rows, manifest):
    """makeShell's `soon` entries: not-built screens kept in the menu (prototype.screens[].menu),
    in the prototype's order, each new group placed after the group the prototype shows before it."""
    order = []
    for sc in manifest.get("screens") or []:
        g = (sc or {}).get("group")
        if g and g not in order:
            order.append(g)
    titles = {sc.get("id"): sc.get("title") for sc in manifest.get("screens") or [] if isinstance(sc, dict)}
    # in the prototype's order, whatever order the spec lists its screens in
    rank = {sc.get("id"): i for i, sc in enumerate(manifest.get("screens") or []) if isinstance(sc, dict)}
    out = []
    for r in rows:
        m = r.get("menu")
        if r["cls"] != "prototype-only" or not m:
            continue
        item = {"label": m.get("label") or titles.get(r["id"]) or r["id"]}
        for k in ("group", "icon", "roles"):
            if m.get(k):
                item[k] = m[k]
        g = m.get("group")
        if g in order and order.index(g) > 0:
            item["after"] = order[order.index(g) - 1]
        out.append((rank.get(r["id"], len(rank)), item))
    return [item for _, item in sorted(out, key=lambda x: x[0])]


def soon_md(rows, manifest):
    items = soon_items(rows, manifest)
    if not items:
        return ""
    return ("\n## Shell: screens kept in the menu, greyed out\n\n"
            "Pass these to `makeShell` as `soon` in `src/custom/Shell.tsx`, exactly as written:\n\n"
            "```json\n" + json.dumps(items, indent=2) + "\n```\n")


def proto_classes_md(rows, missing):
    L = ["## Build: theme or rebuild (spec_check)", "",
         "Theme: the standard page, in app.design's tokens (plus an optional token-only "
         "`src/custom/screens/<page>.css`). Rebuild: port the screen onto its slot. Never rebuild a themed screen; "
         "if it can't match, say so in the build report (open-mode.md, \"Screens\").", "",
         "| Screen | Maps | Class | Reason | Builds as |", "|---|---|---|---|---|"]
    for r in rows:
        builds = (f"slot `{r['slot']}`" if r.get("slot") else
                  "-" if r["cls"] == "prototype-only" else
                  f"page `{r.get('page')}`" if r.get("kind") == "page" else f"360 `{r.get('code')}`")
        L.append(f"| `{r['id']}` | {r.get('maps') or '-'} | {r['cls']} | {str(r.get('reason', '')).replace('|', '/')} | {builds} |")
    for sid in missing:
        L.append(f"| `{sid}` | - | unmapped | not in the spec's prototype.screens | standard if it has a page; report it |")
    left = [(r["id"], x) for r in rows for x in r.get("not_built") or []]
    if left:
        L += ["", "Not built from the prototype (the spec's not_built; say so in the build report):", ""]
        L += [f"- `{sid}`: {x.get('text')} ({x.get('why')})" for sid, x in left]
    return "\n".join(L) + "\n"


def read_existing_holes(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\|\s*(H-\d+)\s*\|\s*\w+\s*\|\s*`([^`]+)`\s*\|.*\|\s*([\w-]+)\s*\|\s*$", line)
        if m:
            out[m.group(2)] = {"id": m.group(1), "status": m.group(3)}
    return out


def strip_internal(M):
    """JSON-safe copy without the fmap index."""
    M = copy.deepcopy(M)
    for E in M["entities"].values():
        E.pop("fmap", None)
    return M


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--workspace", help="app workspace; outputs go to <workspace>/.zas/")
    ap.add_argument("--out", help="output dir (default <workspace>/.zas)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--audit-holes", action="store_true",
                    help="with --workspace: check every hole's function/slot exists with its marker; exit 1 on gaps")
    a = ap.parse_args(argv)
    try:
        text = open(a.spec, encoding="utf-8").read()
        raw = yaml.safe_load(text)
    except Exception as ex:
        print(f"Cannot read {a.spec}: {ex}", file=sys.stderr)
        return 2
    spec_hash = hashlib.sha256(text.encode()).hexdigest()[:12]
    S = Spec(raw, a.spec)
    S.build()
    if S.M:
        S.lint()
        S.prototype_screens()
        S.page_holes()
        S.derive()
        S.intent()
    out = a.out or (os.path.join(a.workspace, ".zas") if a.workspace else None)
    issues = S.L.items
    errs = S.L.errors()

    if out and S.M:
        os.makedirs(out, exist_ok=True)
        attach_bundle(S.holes, out)
        attach_prototype(S, out)
        S.number_holes(read_existing_holes(os.path.join(out, "holes.md")))
        resolved = strip_internal(S.M)
        resolved["spec_hash"] = spec_hash
        resolved["holes"] = S.holes
        resolved["issues"] = issues
        with open(os.path.join(out, "spec.resolved.json"), "w", encoding="utf-8") as f:
            json.dump(resolved, f, indent=1, ensure_ascii=False, default=str)
        with open(os.path.join(out, "spec.ui.json"), "w", encoding="utf-8") as f:
            json.dump(S.ui_json(), f, indent=1, ensure_ascii=False)
        with open(os.path.join(out, "holes.md"), "w", encoding="utf-8") as f:
            f.write(S.holes_md())
        with open(os.path.join(out, "plan.md"), "w", encoding="utf-8") as f:
            f.write(S.plan_md(spec_hash))
        with open(os.path.join(out, "test_plan.md"), "w", encoding="utf-8") as f:
            f.write(S.test_plan_md())
        with open(os.path.join(out, "issues.md"), "w", encoding="utf-8") as f:
            f.write("# Spec issues\n\n" + ("\n".join(
                f"- **{i['level']}** `{i['where']}`: {i['msg']}" + (f" Fix: {i['fix']}" if i.get("fix") else "")
                for i in issues) or "None.") + "\n")
    elif S.M:
        S.number_holes({})

    if not a.quiet:
        for i in issues:
            tag = {"error": "ERROR", "intent": "intent"}.get(i["level"], "warn ")
            print(f"{tag}  {i['where']}: {i['msg']}" + (f"\n       fix: {i['fix']}" if i.get("fix") else ""))
        if S.M:
            print(f"\n{len(S.M['entities'])} entities in {len(S.M['modules'])} modules, {len(S.M['pages'])} pages, "
                  f"{len(S.M['detail_views'])} detail views, {len(S.M['roles'])} roles, {len(S.holes)} holes.")
        n_int = sum(1 for i in issues if i["level"] == "intent")
        print(f"{len(errs)} errors, {len(issues) - len(errs) - n_int} warnings, {n_int} intent findings."
              + (f" Outputs in {out}" if out else ""))
    if a.audit_holes and a.workspace and S.M and not errs:
        return audit_holes(a.workspace, S.holes)
    return 1 if errs else 0


def audit_holes(ws, holes):
    """Every hole: target function (and data hook) defined, `zas:hole H-NN` marker present,
    status not todo. Prints one line per problem."""
    cache, problems = {}, []

    def src(rel):
        if rel not in cache:
            try:
                cache[rel] = open(os.path.join(ws, rel), encoding="utf-8").read()
            except OSError:
                cache[rel] = None
        return cache[rel]

    def defined(target):
        if not target or "::" not in target:
            return True  # free-form target (frontend requirement): judged by status only
        rel, fn = target.split("::", 1)
        text = src(rel)
        if text is None:
            return False
        pats = [rf"^def {re.escape(fn)}\(", rf"^async def {re.escape(fn)}\("] if rel.endswith(".py") else \
            [rf"function {re.escape(fn)}\b", rf"const {re.escape(fn)}\b", rf"export \{{[^}}]*\b{re.escape(fn)}\b"]
        return any(re.search(p, text, re.M) for p in pats)

    for h in holes:
        st = h.get("status", "todo")
        if st == "todo":
            problems.append(f"{h['id']} todo        {h['target']}")
            continue
        if st in ("blocked", "covered"):  # covered = the runtime already does it (e.g. the timeline); no code
            continue
        for tgt in (h.get("target"), h.get("data_hook")):
            if not defined(tgt):
                problems.append(f"{h['id']} missing     {tgt}  (status says {st})")
        rel = (h.get("target") or "").split("::", 1)[0]
        text = src(rel) if "::" in (h.get("target") or "") else None
        if text and f"zas:hole {h['id']}" not in text:
            problems.append(f"{h['id']} no marker   {rel}  (add `zas:hole {h['id']}` above the function)")
    counts = {}
    for h in holes:
        counts[h.get("status", "todo")] = counts.get(h.get("status", "todo"), 0) + 1
    print("holes: " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    for p in problems:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
