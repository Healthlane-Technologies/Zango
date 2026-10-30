"""
design_diff: the built app's styles against the approved prototype, element by element (open mode,
template apps: the prototype is the kit page).

The approved page (.zas/bundle/prototype/prototype.html) and the built app draw the same pieces with two
vocabularies: the kit page's `.z-*` / `.d-*` classes and the runtime's `.zas-*` (scripts/kit_vocab.py
pairs them). For every mapped prototype screen and persona this opens both in a browser, finds each
part (kit_vocab.PARTS: the 360 header, its facts, stat cards, tabs, cards, table headers, buttons, the
shell…) and compares their computed styles: colours and gradients, borders, radius, shadows, type,
spacing, and the ::before/::after decorations. Data does not matter: the two pages show different
records, but a header's background is the same whatever it shows.

What blocks: a difference on what the creator changed. With a baseline (.zas/bundle/prototype/
baseline.html, the page the creator started from: the template's), the same parts are read on it too,
and a difference blocks when the approved value differs from the baseline's: the creator asked for it.
Without one, a difference blocks when its part is named by a changed CSS rule (changes.json
"look.touched"). Blocking differences fail `design.style.<screen>.<role>` and go to the build's style
rounds. Every other difference is listed but passes: the template's kit and the runtime are close, not
identical.

    python3 -m zas_test.design --workspace <ws> --only style

Writes .zas/style_diff.json, .zas/style_diff.md (every difference, blocking first) and
.zas/style_fix.css (the approved values on the runtime selectors: a starting point for kit.css).
"""

import json
import os
import re
import sys

from . import auth, browser, in_scope, scope

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))  # scripts/: kit_vocab

import kit_vocab as V  # noqa: E402

STYLE_CHECK = "design.style"
WIDTH, HEIGHT = 1280, 900
# Compared once per persona (on its first screen): the shell is the same on every screen.
SHELL = {"sidebar", "brand_mark", "nav_item", "nav_item_on", "nav_group", "user_card", "top_bar", "content"}
PSEUDO_PROPS = ("background-color", "background-image", "width", "height", "border-top-left-radius")
# where a decoration sits: carried into style_fix.css, not compared (it moves with the box's size)
PSEUDO_PLACE = ("top", "right", "bottom", "left")

STYLES_JS = """([parts, pseudo]) => {
  const vis = el => {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && cs.visibility !== 'hidden' && cs.display !== 'none';
  };
  const pick = (cs, names) => Object.fromEntries(names.map(n => [n, cs.getPropertyValue(n).trim()]));
  const out = {};
  for (const [id, sel, names] of parts) {
    let els = [];
    try { els = Array.from(document.querySelectorAll(sel)).filter(vis); }
    catch (e) { out[id] = {count: 0, error: String(e)}; continue; }
    if (!els.length) { out[id] = {count: 0}; continue; }
    const el = els[0], r = {count: els.length, props: pick(getComputedStyle(el), names)};
    for (const pe of ['::before', '::after']) {
      const cs = getComputedStyle(el, pe);
      if (cs.content && cs.content !== 'none' && cs.content !== 'normal' && cs.display !== 'none')
        r[pe] = pick(cs, pseudo);
    }
    out[id] = r;
  }
  return out;
}"""

# ───────────────────────── values ─────────────────────────

COLOR = re.compile(r"rgba?\([^)]*\)|color\(srgb[^)]*\)|#[0-9a-fA-F]{3,8}\b|\btransparent\b")
NUMBER = re.compile(r"-?\d*\.?\d+(?:e-?\d+)?")
COLOUR_TOL, ALPHA_TOL = 6, 0.06


def parse_colour(c):
    """(r, g, b, a) in 0-255 / 0-1, or None."""
    c = c.strip().lower()
    if c == "transparent":
        return (0, 0, 0, 0.0)
    if c.startswith("#"):
        h = c[1:]
        if len(h) in (3, 4):
            h = "".join(x * 2 for x in h)
        try:
            vals = [int(h[i:i + 2], 16) for i in range(0, len(h), 2)]
        except ValueError:
            return None
        return (*vals[:3], vals[3] / 255 if len(vals) > 3 else 1.0)
    nums = [float(x) for x in NUMBER.findall(c)]
    if c.startswith("color(srgb") and len(nums) >= 3:
        return (nums[0] * 255, nums[1] * 255, nums[2] * 255, nums[3] if len(nums) > 3 else 1.0)
    if c.startswith("rgb") and len(nums) >= 3:
        return (nums[0], nums[1], nums[2], nums[3] if len(nums) > 3 else 1.0)
    return None


def same_colour(a, b):
    x, y = parse_colour(a), parse_colour(b)
    if x is None or y is None:
        return a.strip() == b.strip()
    if x[3] < 0.02 and y[3] < 0.02:  # both fully transparent, whatever their rgb
        return True
    return all(abs(p - q) <= COLOUR_TOL for p, q in zip(x[:3], y[:3])) and abs(x[3] - y[3]) <= ALPHA_TOL


def shape(v):
    """A value with its colours and numbers taken out, and the two lists."""
    colours = COLOR.findall(v)
    rest = COLOR.sub("C", v)
    nums = [float(n) for n in NUMBER.findall(rest)]
    return re.sub(r"\s+", " ", NUMBER.sub("N", rest)).strip().lower(), colours, nums


def same_number(a, b, tol):
    return abs(a - b) <= max(tol, 0.04 * abs(a))


def same_value(prop, a, b):
    """Whether two computed values of `prop` look the same."""
    a, b = (a or "").strip(), (b or "").strip()
    if a == b:
        return True
    if prop == "letter-spacing":
        a, b = ("0px" if a == "normal" else a), ("0px" if b == "normal" else b)
    if prop.endswith("color"):
        return same_colour(a, b)
    if prop in ("font-weight",):
        try:
            return abs(float(a) - float(b)) < 50
        except ValueError:
            return a == b
    if prop in ("text-transform", "border-top-style"):
        return a == b
    tol = (0.4 if prop.startswith("border") and prop.endswith("-width")
           else 0.5 if prop in ("font-size", "letter-spacing")
           else 2.0 if prop in ("width", "height") else 1.0)
    sa, sb = shape(a), shape(b)
    if sa[0] != sb[0] or len(sa[1]) != len(sb[1]) or len(sa[2]) != len(sb[2]):
        # "none" against a shadow, a gradient against a plain fill: a different value outright
        return False
    return (all(same_colour(x, y) for x, y in zip(sa[1], sb[1]))
            and all(same_number(x, y, tol) for x, y in zip(sa[2], sb[2])))


def short(v, n=110):
    v = re.sub(r"\s+", " ", str(v)).strip()
    return v if len(v) <= n else v[: n - 1] + "…"


def compare(approved, built, parts=V.PARTS, only=None):
    """Differences between two pages' part styles (STYLES_JS results), one dict per difference."""
    out = []
    for pid, label, kit_sel, rt_sel, groups, data in parts:
        if only is not None and pid not in only:
            continue
        a, b = approved.get(pid) or {}, built.get(pid) or {}
        if not a.get("count"):
            continue  # the approved screen has no such part: nothing to match
        base = {"part": pid, "label": label, "kit": kit_sel, "runtime": rt_sel, "data": data}
        if not b.get("count"):
            out.append({**base, "prop": "present", "approved": f"{a['count']} shown", "built": "none shown"})
            continue
        for prop in [p for g in groups for p in V.PROPS[g]]:
            av, bv = (a.get("props") or {}).get(prop), (b.get("props") or {}).get(prop)
            if av is None or bv is None:
                continue
            if prop.startswith("border") and prop.endswith(("-color", "-style")):
                width = prop.replace("-color", "-width").replace("-style", "-width")
                if (a["props"].get(width) or "0px") == "0px":
                    continue  # no approved border there: its width (if the built one has one) says it
            if not same_value(prop, av, bv):
                out.append({**base, "prop": prop, "approved": av, "built": bv})
        for pe in ("::before", "::after"):
            ap, bp = a.get(pe), b.get(pe)
            if ap and not bp:
                out.append({**base, "prop": pe, "pseudo": pe, "approved": ap, "built": "none",
                            "approved_text": ", ".join(f"{k} {short(v, 50)}" for k, v in ap.items()
                                                       if k in PSEUDO_PROPS and v not in ("none", "auto", "rgba(0, 0, 0, 0)", "0px"))})
            elif ap and bp:
                for prop in PSEUDO_PROPS:
                    if not same_value(prop, ap.get(prop, ""), bp.get(prop, "")):
                        out.append({**base, "prop": f"{pe} {prop}", "pseudo": pe, "approved": ap.get(prop),
                                    "built": bp.get(prop)})
    return out


def changed_keys(approved, baseline):
    """(part, property) pairs the creator changed: where the approved page differs from the baseline."""
    return {(d["part"], d["prop"]) for d in compare(approved, baseline)}


def is_blocking(d, touched_ids, changed=None):
    """A difference blocks when the creator changed that part (``changed``: that property, from the
    baseline render; else ``touched_ids``: the part, from the changed CSS rules). A data-dependent
    part the built screen doesn't show (no badge in these rows) never does."""
    if d["prop"] == "present" and d.get("data"):
        return False
    if changed is not None:
        return (d["part"], d["prop"]) in changed
    return d["part"] in touched_ids


def line(d):
    if d["prop"] == "present":
        return f"{d['label']} (`{d['runtime']}`): the approved screen shows it, the built one doesn't"
    if d.get("pseudo") and d["built"] == "none":
        return (f"{d['label']} (`{d['runtime']}{d['pseudo']}`): the approved screen has a decoration "
                f"({short(d.get('approved_text') or '', 120)}), the built one has none")
    return (f"{d['label']} (`{d['runtime']}`) {d['prop']}: approved {short(d['approved'])} · "
            f"built {short(d['built'])}")


def css_colour(c):
    """A computed colour as rgb()/rgba() (Chrome gives a color-mix() result as color(srgb …))."""
    x = parse_colour(c)
    if x is None:
        return c
    r, g, b_ = (round(v) for v in x[:3])
    a = x[3]
    return f"rgb({r}, {g}, {b_})" if a >= 0.999 else f"rgba({r}, {g}, {b_}, {round(a, 3)})"


def css_value(v):
    return COLOR.sub(lambda m: css_colour(m.group(0)), str(v))


# sampled longhands → the shorthand they stand for (design_diff reads one corner, three sides)
SHORTHAND = (
    (("border-top-left-radius", "border-bottom-right-radius"), "border-radius"),
    (("border-top-color", "border-bottom-color", "border-left-color"), "border-color"),
    (("border-top-width", "border-bottom-width", "border-left-width"), "border-width"),
    (("border-top-style",), "border-style"),
    (("padding-top", "padding-right", "padding-bottom", "padding-left"), None),
)


def collapse(decl):
    out = dict(decl)
    for longs, short_name in SHORTHAND:
        have = [k for k in longs if k in out]
        if not have:
            continue
        if short_name is None:  # padding: all four sides, or the ones given
            if len(have) == 4:
                vals = [out.pop(k) for k in longs]
                out["padding"] = " ".join(vals)
            continue
        vals = {out[k] for k in have}
        if len(vals) == 1:
            for k in have:
                out.pop(k)
            out[short_name] = vals.pop()
    if "border-width" in out and "border-style" not in out and out["border-width"] not in ("0px", "0"):
        out["border-style"] = "solid"
    return out


def placement(ap):
    """A decoration's offsets: of each pair (top/bottom, left/right) the authored one, i.e. the
    negative one (a decoration bleeding out of its box), else the nearer edge."""
    out = {}
    for x, y in (("top", "bottom"), ("left", "right")):
        vx, vy = ap.get(x), ap.get(y)
        if vx is None or vy is None or "px" not in f"{vx}{vy}":
            continue
        nx, ny = float(NUMBER.findall(vx)[0]), float(NUMBER.findall(vy)[0])
        if (nx < 0) != (ny < 0):
            out[x if nx < 0 else y] = vx if nx < 0 else vy
        else:
            out[x if abs(nx) <= abs(ny) else y] = vx if abs(nx) <= abs(ny) else vy
    return out


def fix_css(diffs):
    """The approved values on the runtime selectors, grouped per selector: a starting point for
    kit.css (every value is the approved page's own, so the palette lint accepts it)."""
    rules = {}
    for d in diffs:
        if d["prop"] == "present" or d["runtime"] is None:
            continue
        runtime = d["runtime"].split(",")[0].strip()
        if d.get("pseudo") and d["built"] == "none":
            ap = d["approved"] or {}
            decl = rules.setdefault(f"html {runtime}{d['pseudo']}", {})
            decl.update({"content": '""', "position": "absolute", "pointer-events": "none"})
            for k in PSEUDO_PROPS:
                if ap.get(k) not in (None, "none", "auto"):
                    decl[k] = ap[k]
            decl.update(placement(ap))
            rules.setdefault(f"html {runtime}", {}).update({"position": "relative", "overflow": "hidden"})
            continue
        if d.get("pseudo"):
            sel, prop = f"html {runtime}{d['pseudo']}", d["prop"].split(" ", 1)[1]
        else:
            sel, prop = f"html {runtime}", d["prop"]
        rules.setdefault(sel, {})[prop] = d["approved"]
    out = []
    for sel, decl in rules.items():
        decl = collapse(decl)
        out.append(sel + " { " + "; ".join(f"{k}: {css_value(v)}" for k, v in decl.items()) + "; }")
    if any(sel.endswith(("::before", "::after")) for sel in rules):
        # the decorations sit under the content, as in the prototype
        heads = {sel.rsplit("::", 1)[0] for sel in rules if sel.endswith(("::before", "::after"))}
        out += [f"{h} > * {{ position: relative; z-index: 1; }}" for h in sorted(heads)]
    return "\n".join(out)


# ───────────────────────── pages ─────────────────────────

def part_args(side):
    """STYLES_JS parts for one side: (id, selector, property names)."""
    i = 2 if side == "kit" else 3
    return [[p[0], p[i], [x for g in p[4] for x in V.PROPS[g]]] for p in V.PARTS]


def load_touched(proto):
    try:
        with open(os.path.join(proto, "changes.json"), encoding="utf-8") as f:
            changes = json.load(f)
    except (OSError, ValueError):
        return set(), "no change map"
    look = changes.get("look") or {}
    return set(look.get("touched") or []), changes.get("baseline") or ""


def report_md(rows, touched, baseline):
    out = ["# Style differences: built app against the approved prototype", "",
           f"Baseline: {baseline or 'none'}. Touched by the creator's changes: "
           + (", ".join(f"`.{c}`" for c in sorted(touched)) if touched else "nothing") + ".", "",
           "Fix a blocking difference in `frontend/src/custom/kit/kit.css` on the runtime selector shown "
           "(`.zas-…`), with the approved value. `.zas/style_fix.css` has every approved value on its "
           "runtime selector.", ""]
    for r in rows:
        if not (r["blocking"] or r["other"] or r.get("problem")):
            continue
        out.append(f"## {r['screen']} · {r['role']}")
        if r.get("problem"):
            out.append(f"- not compared: {r['problem']}")
        for d in r["blocking"]:
            out.append(f"- **blocking** {line(d)}")
        for d in r["other"]:
            out.append(f"- {line(d)}")
        out.append("")
    return "\n".join(out)


def g_style(Dx, b):
    from . import kit as K
    from .design import is_open_mode, open_built, screen_route
    from . import load_json

    ws = Dx.ws
    prefixes = scope()
    if prefixes and not any(p == "style" or p.startswith("style.") for p in prefixes):
        return
    if not is_open_mode(ws):
        Dx.add(STYLE_CHECK, "the built app's styles match the approved prototype", "style", "skip",
               "default design: no prototype to compare with")
        return
    proto = os.path.join(ws, ".zas", "bundle", "prototype")
    try:
        with open(os.path.join(proto, "manifest.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        with open(os.path.join(proto, "capture.json"), encoding="utf-8") as f:
            capture = {sc["id"]: sc for sc in json.load(f).get("screens") or []}
        html_text = open(os.path.join(proto, "prototype.html"), encoding="utf-8").read()
        base_path = os.path.join(proto, "baseline.html")
        base_text = open(base_path, encoding="utf-8").read() if os.path.isfile(base_path) else None
    except (OSError, ValueError):
        Dx.add(STYLE_CHECK, "the built app's styles match the approved prototype", "style", "skip",
               "the prototype bundle has no prototype.html / capture.json")
        return
    if not manifest.get("kit"):
        Dx.add(STYLE_CHECK, "the built app's styles match the approved prototype", "style", "skip",
               "the prototype is not the kit page: its parts have no runtime counterparts to pair")
        return
    rows = ((Dx.M.get("prototype") or {}).get("screens")) or []
    touched, baseline = load_touched(proto)
    touched_ids = V.touched_parts(touched)
    spec_roles = {r.lower(): r for r in (Dx.M.get("roles") or {})}
    persona_role = {k: spec_roles.get(str(v).lower()) or spec_roles.get(str(k).lower())
                    for k, v in (manifest.get("roles") or {}).items()}
    try:
        records = load_json(ws, "test_records.json")
    except (OSError, ValueError):
        records = {}
    target = auth.load_users(ws)["target"]
    sessions, failed, proto_pages, shell_done = {}, {}, {}, set()
    results = []

    def login(role):
        if role in failed:
            raise auth.AuthError(f"login failed earlier in this run, not retried: {failed[role]}")
        if role not in sessions:
            try:
                sessions[role] = auth.login(ws, role)
            except auth.AuthError as e:
                failed[role] = str(e)[:200]
                raise
        return sessions[role]

    def approved_styles(screen, persona, text=None, key="approved"):
        if (key, persona) not in proto_pages:
            proto_pages[(key, persona)] = K.proto_page(b, text or html_text)
        page = proto_pages[(key, persona)][1]
        if not page.evaluate("typeof window.ZAS === 'object' && typeof ZAS.go === 'function'"):
            raise RuntimeError(f"the {key} prototype did not load (no ZAS runtime)")
        page.evaluate(K.GO_JS, [screen, persona])
        return page.evaluate(STYLES_JS, [part_args("kit"), list(PSEUDO_PROPS + PSEUDO_PLACE)])

    def baseline_changes(screen, persona, want):
        """What the creator changed on this screen, or None (no baseline: fall back to the classes)."""
        if base_text is None:
            return None
        try:
            return changed_keys(want, approved_styles(screen, persona, base_text, "baseline"))
        except Exception:  # noqa: BLE001 - a screen the template didn't have: every part is the creator's
            return {(p[0], prop) for p in V.PARTS for prop in
                    ["present", *[x for g in p[4] for x in V.PROPS[g]], "::before", "::after"]}

    try:
        for r in rows:
            if r.get("cls") == "prototype-only" or r["id"] not in capture:
                continue
            where = f"pages.{r['page']}" if r.get("kind") == "page" else f"detail_views.{r['code']}"
            path_id = f"style.{r['id']}"
            if prefixes and not in_scope(path_id, prefixes) and "style" not in prefixes:
                continue
            for pr in capture[r["id"]].get("roles") or []:
                persona = pr.get("same_as") or pr["role"]
                role = persona_role.get(pr["role"])
                slug = re.sub(r"[^a-z0-9]+", "_", (role or pr["role"]).lower())
                rid = f"{STYLE_CHECK}.{r['id']}.{slug}"
                title = f"prototype screen {r['id']} has the approved styles"
                row = {"screen": r["id"], "role": role or pr["role"], "where": where, "blocking": [], "other": []}
                results.append(row)
                if not role:
                    row["problem"] = f"persona {pr['role']!r} is no spec role"
                    Dx.add(rid, title, path_id, "skip", row["problem"], role)
                    continue
                only = None if role not in shell_done else {p[0] for p in V.PARTS} - SHELL
                try:
                    want = approved_styles(r["id"], persona)
                    changed = baseline_changes(r["id"], persona, want)
                    sess = login(role)
                    path, why = screen_route(Dx, r, sess, records)
                    if why:
                        row["problem"] = why
                        Dx.add(rid, title, path_id, "skip", why, role)
                        continue
                    rp = browser.RolePage(b, target, sess, viewport={"width": WIDTH, "height": HEIGHT})
                    try:
                        open_built(rp, path)
                        rp.page.add_style_tag(content="*,*::before,*::after{transition:none!important;"
                                              "animation:none!important}")
                        got = rp.page.evaluate(STYLES_JS, [part_args("runtime"), list(PSEUDO_PROPS + PSEUDO_PLACE)])
                    finally:
                        rp.close()
                except Exception as e:  # noqa: BLE001 - one screen's trouble is that screen's result
                    row["problem"] = repr(e)[:300]
                    Dx.add(rid, title, path_id, "fail", f"could not compare: {row['problem']}", role)
                    continue
                shell_done.add(role)
                diffs = compare(want, got, only=only)
                row["blocking"] = [d for d in diffs if is_blocking(d, touched_ids, changed)]
                row["other"] = [d for d in diffs if not is_blocking(d, touched_ids, changed)]
                if row["blocking"]:
                    head = (f"{len(row['blocking'])} difference(s) on parts the approved design changed "
                            f"(fix in kit.css on the runtime selector, approved values in .zas/style_fix.css): ")
                    Dx.add(rid, title, path_id, "fail",
                           head + "; ".join(line(d) for d in row["blocking"][:6])
                           + (f"; … {len(row['blocking']) - 6} more in .zas/style_diff.md" if len(row["blocking"]) > 6 else ""),
                           role)
                else:
                    Dx.add(rid, title, path_id, "pass",
                           f"{len(row['other'])} difference(s) on parts the creator didn't change (see .zas/style_diff.md)"
                           if row["other"] else "", role)
    finally:
        for ctx, _ in proto_pages.values():
            try:
                ctx.close()
            except Exception:  # noqa: BLE001
                pass
    zas = os.path.join(ws, ".zas")
    with open(os.path.join(zas, "style_diff.json"), "w", encoding="utf-8") as f:
        json.dump({"baseline": baseline, "touched": sorted(touched), "screens": results}, f, indent=1)
    with open(os.path.join(zas, "style_diff.md"), "w", encoding="utf-8") as f:
        f.write(report_md(results, touched, baseline))
    with open(os.path.join(zas, "style_fix.css"), "w", encoding="utf-8") as f:
        f.write("/* The approved prototype's values on the runtime's selectors, for every blocking difference\n"
                "   (zas_test/style.py). A starting point for frontend/src/custom/kit/kit.css. */\n"
                + fix_css([d for r in results for d in r["blocking"]]) + "\n")
