"""
Design checks. No human approves anything: every check compares against a fixed reference
(rules, shipped goldens, tokens.css, or the spec). See references/design-system.md.

    python3 -m zas_test.design --workspace <ws> [--only lint,gallery,tokens,tree,layout]
    python3 -m zas_test.design --make-goldens --gallery-url http://localhost:4173/ --out <skill>/assets/goldens
        (skill author only: re-shoot the goldens after changing the runtime)

  lint     src/custom/**: no colour literals, no colour/font inline styles, no new .css/<style>,
           UI imported only from zas (static, no browser)
  gallery  /app/__zas sections vs <skill>/assets/goldens/<section>.png (pixel diff, small tolerance;
           skipped with a reason when no goldens are shipped or Pillow is missing)
  tokens   computed styles on /app/__zas: primary button = app brand, tone badges = tokens.css,
           Inter font, card radius/border, ground colour
  tree     per 360 × viewer role: data-zas facts and stats in spec order, status badge tone = spec
           colour, sidebar rail present iff the layout has one
  layout   menu pages and 360s at 1440 and 1280 px: no horizontal page overflow, no clipped text
           in titles/facts/stats/tabs (unless it ends in an ellipsis)
  parity   each custom screen the user approved (.zas/bundle/): its kit blocks, titles, KPI labels
           and table columns as the approved role saw them, in order (kit_tree.js on both sides;
           values are never compared). Saves the built screen to .zas/screens/parity/ and lists
           approved/built pairs in .zas/parity_looks.json. Reported, not blocking.
Results: <ws>/.zas/test_results.json (layer "design"). Exit 1 when a blocking check fails.
"""

import argparse
import glob
import json
import os
import re
import sys

from . import auth, browser, load_json, print_summary, save_results

GROUPS = ["lint", "gallery", "tokens", "tree", "layout", "parity"]
HERE = os.path.dirname(os.path.abspath(__file__))
GOLDENS = os.path.join(HERE, "..", "..", "assets", "goldens")
SECTIONS = ["badges", "buttons", "stats", "banners", "tabs", "panels", "states", "kit"]
TONE_BG = {"gray": "#f2f4f7", "blue": "#eff8ff", "green": "#ecfdf3", "amber": "#fffaeb", "red": "#fef3f2",
           "purple": "#f4f3ff", "teal": "#f0fdf9", "indigo": "#eef4ff", "pink": "#fdf2fa"}

COLOR_LIT = re.compile(r"(?<![\w-])(#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\()")
STYLE_COLOR = re.compile(r"style=\{\{[^}]*\b(color|background|backgroundColor|border\w*|font\w*|boxShadow)\s*:", re.S)
BAD_IMPORT = re.compile(r"""from\s+["'](@zango-core/components|@mui/|antd|@chakra-ui|react-bootstrap|styled-components|@emotion)""")


def rgb(hexs):
    h = hexs.lstrip("#")
    return f"rgb({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)})"


class D:
    def __init__(self, ws):
        self.ws, self.results = ws, []
        self.M = load_json(ws, "spec.resolved.json") if ws else None

    def add(self, id, title, path, status, detail="", role=None):
        self.results.append({"layer": "design", "id": id, "title": title, "role": role, "spec_path": path,
                             "status": status, "detail": str(detail)[:700]})

    def check(self, id, title, path, fn, role=None):
        try:
            good, detail = fn()
            if good is None:
                self.add(id, title, path, "skip", detail, role)
            else:
                self.add(id, title, path, "pass" if good else "fail", "" if good else detail, role)
        except Exception as e:
            self.add(id, title, path, "fail", repr(e)[:500], role)


# ───────────────────────── lint ─────────────────────────

def g_lint(Dx, b=None):
    root = os.path.join(Dx.ws, "frontend", "src", "custom")
    files = [f for f in glob.glob(os.path.join(root, "**", "*"), recursive=True) if os.path.isfile(f)]
    probs = []
    for f in files:
        rel = os.path.relpath(f, Dx.ws)
        if f.endswith((".css", ".scss", ".less")):
            probs.append(f"{rel}: stylesheet in src/custom (use zas classes)")
            continue
        if not f.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        src = open(f, encoding="utf-8").read()
        code = re.sub(r"//[^\n]*|/\*.*?\*/", "", src, flags=re.S)
        for i, line in enumerate(code.splitlines(), 1):
            if COLOR_LIT.search(line):
                probs.append(f"{rel}:{i}: colour literal `{COLOR_LIT.search(line).group(0)}`")
            if BAD_IMPORT.search(line):
                probs.append(f"{rel}:{i}: UI import outside zas: {line.strip()[:80]}")
        for m in STYLE_COLOR.finditer(code):
            probs.append(f"{rel}:{code[:m.start()].count(chr(10)) + 1}: inline `{m.group(1)}` style")
        if "<style" in code:
            probs.append(f"{rel}: <style> tag")
        for word in ("Lorem", "Coming soon", "TODO"):
            if re.search(rf">[^<]*{word}", code):
                probs.append(f"{rel}: placeholder copy '{word}' rendered")
    Dx.check("design.lint", "custom code uses the design system only", "frontend/src/custom",
             lambda: (not probs, "\n".join(probs[:40])))


# ───────────────────────── browser helpers ─────────────────────────

def first_session(Dx):
    roles = [r for r in Dx.M["roles"] if r not in ("AnonymousUsers", "SystemUsers")]
    for r in roles:
        try:
            return r, auth.login(Dx.ws, r)
        except auth.AuthError:
            continue
    raise RuntimeError("no test user could log in (zango_platform.py users)")


def gallery_page(b, url=None, session=None, target=None):
    rp = browser.RolePage(b, url or target, session, pinned=True)
    rp.open(url or "/app/__zas", wait='[data-zas="page"][data-zas-key="__zas"]')
    rp.page.add_style_tag(content="*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}")
    rp.page.wait_for_timeout(300)
    return rp


def shoot_sections(rp, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for s in SECTIONS:
        loc = rp.page.locator(f'[data-gallery="{s}"]')
        if loc.count():
            p = os.path.join(out_dir, f"{s}.png")
            loc.first.screenshot(path=p)
            paths[s] = p
    return paths


def diff(a, b_):
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return None
    A, B = Image.open(a).convert("RGB"), Image.open(b_).convert("RGB")
    if A.size != B.size:
        return 1.0, f"size {A.size} vs golden {B.size}"
    d = ImageChops.difference(A, B).convert("L")
    hist = d.histogram()
    changed = sum(hist[16:])  # ignore anti-aliasing noise below 16/255
    return changed / (A.size[0] * A.size[1]), ""


# ───────────────────────── gallery, tokens ─────────────────────────

def g_gallery(Dx, b):
    goldens = {s: os.path.join(GOLDENS, f"{s}.png") for s in SECTIONS if os.path.exists(os.path.join(GOLDENS, f"{s}.png"))}
    if not goldens:
        Dx.add("design.gallery", "gallery matches goldens", "assets/goldens", "skip", "no goldens shipped with the skill yet")
        return
    try:
        meta = json.load(open(os.path.join(GOLDENS, "meta.json")))
    except (OSError, ValueError):
        meta = {}
    here = {"platform": sys.platform, "chromium": b.version}
    if meta and meta != here:
        Dx.add("design.gallery", "gallery matches goldens", "assets/goldens", "skip",
               f"goldens were shot on {meta}, this run is {here}: font rendering differs across platforms. "
               f"Re-shoot with `zas_test.design --make-goldens` on this platform to compare")
        return
    role, s = first_session(Dx)
    rp = gallery_page(b, session=s, target=auth.load_users(Dx.ws)["target"])
    try:
        shots = shoot_sections(rp, os.path.join(Dx.ws, ".zas", "screens", "gallery"))
        for sec, g in goldens.items():
            def t(sec=sec, g=g):
                if sec not in shots:
                    return False, f"section {sec} missing from /app/__zas"
                r = diff(shots[sec], g)
                if r is None:
                    return None, "Pillow not installed (pip install pillow)"
                frac, why = r
                return frac <= 0.01, why or f"{frac:.2%} of pixels differ from the golden (limit 1%): {shots[sec]}"
            Dx.check(f"design.gallery.{sec}", f"gallery {sec} matches golden", "assets/goldens", t)
    finally:
        rp.close()


def g_tokens(Dx, b):
    role, s = first_session(Dx)
    brand = Dx.M["app"]["theme"]["primary"]
    rp = gallery_page(b, session=s, target=auth.load_users(Dx.ws)["target"])
    try:
        css = rp.page.evaluate("""() => {
          const g = (sel, prop) => { const e = document.querySelector(sel); return e ? getComputedStyle(e)[prop] : null; };
          const out = {pri: g('.zas-btn.pri', 'backgroundColor'), font: g('.zas', 'fontFamily'),
                       panelRadius: g('.zas-panel', 'borderTopLeftRadius'), panelBorder: g('.zas-panel', 'borderTopColor'),
                       brandVar: getComputedStyle(document.documentElement).getPropertyValue('--brand').trim(), badges: {}};
          document.querySelectorAll('[data-zas="badge"][data-zas-key^="badge-"]').forEach(e => out.badges[e.dataset.zasTone] = getComputedStyle(e).backgroundColor);
          return out; }""")
        # the gallery pins the default brand; the app brand is checked on --brand
        Dx.check("design.tokens.primary", "primary button uses the brand", "app.theme.primary",
                 lambda: (css["pri"] == rgb("#4F46E5"), f"primary button {css['pri']} != {rgb('#4F46E5')} (gallery brand)"))
        Dx.check("design.tokens.brand", "app brand applied", "app.theme.primary",
                 lambda: (css["brandVar"].lower() == brand.lower(), f"--brand on :root is {css['brandVar']!r}, spec {brand}"))
        Dx.check("design.tokens.font", "Inter type", "design-system", lambda: ("Inter" in (css["font"] or ""), css["font"]))
        Dx.check("design.tokens.card", "card radius 12px, hairline border", "design-system",
                 lambda: (css["panelRadius"] == "12px" and css["panelBorder"] == rgb("#eaecf0"), f"{css['panelRadius']} {css['panelBorder']}"))
        bad = {t: v for t, v in css["badges"].items() if v != rgb(TONE_BG.get(t, "#000000"))}
        Dx.check("design.tokens.tones", "nine tones match tokens.css", "design-system",
                 lambda: (len(css["badges"]) == 9 and not bad, f"{len(css['badges'])} tones rendered; wrong: {bad}"))
    finally:
        rp.close()


# ───────────────────────── tree, layout ─────────────────────────

def viewers(Dx, V):
    hero = Dx.M["entities"][V["hero"]]
    out = []
    for r in Dx.M["roles"]:
        a = (hero.get("access_resolved") or {}).get(r)
        if r in ("AnonymousUsers", "SystemUsers") or (V.get("roles") and r not in V["roles"]):
            continue
        if not hero.get("access") or (a and not a.get("none") and "detail" in a["actions"]):
            out.append(r)
    return out


def g_tree(Dx, b):
    try:
        records = load_json(Dx.ws, "test_records.json")
    except (OSError, ValueError):
        records = {}
    target = auth.load_users(Dx.ws)["target"]
    for vcode, V in (Dx.M.get("detail_views") or {}).items():
        uids = records.get(V["hero"]) or []
        for role in viewers(Dx, V):
            def t(role=role, V=V, uids=uids):
                if not uids:
                    return None, "no record to open: run zas_test.api first"
                sess = auth.login(Dx.ws, role)
                rp = browser.RolePage(b, target, sess)
                try:
                    uid = browser.visible_uid(Dx.M, V["hero"], sess, uids)  # row-scoped roles open their own record
                    rp.open(browser.detail_path(Dx.M, V["hero"], uid), wait='[data-zas="header"], [data-zas="empty"]')
                    tree = rp.tree()
                    probs = []
                    spec_facts = [f.get("field") or f.get("path") or f"fact{i + 1}" for i, f in enumerate((V.get("header") or {}).get("facts", []))]
                    got_facts = [n["key"] for n in tree if n["kind"] == "fact"]
                    if [k for k in spec_facts if k in got_facts] != got_facts:
                        probs.append(f"facts order {got_facts} vs spec {spec_facts}")
                    got_stats = sorted((n for n in tree if n["kind"] == "stat"), key=lambda n: n["order"] or 0)
                    if [n["order"] for n in got_stats] != sorted(n["order"] for n in got_stats):
                        probs.append("stats out of order")
                    statuses = {s["label"]: s["color"] for s in (Dx.M["entities"][V["hero"]].get("workflow") or {}).get("statuses", [])}
                    for n in tree:
                        if n["kind"] == "badge" and n["text"] in statuses and n["tone"] != statuses[n["text"]]:
                            probs.append(f"status badge {n['text']!r} tone {n['tone']} != spec {statuses[n['text']]}")
                    rail = any(n["kind"] == "rail" for n in tree)
                    want_rail = V.get("layout", "header_tabs") != "header_tabs" and bool(V.get("sidebar"))
                    if rail != want_rail:
                        probs.append(f"sidebar rail {'present' if rail else 'missing'} for layout {V.get('layout')}")
                    return not probs, "; ".join(probs)
                finally:
                    rp.close()
            Dx.check(f"design.tree.{vcode}.{re.sub(r'[^a-z0-9]+', '_', role.lower())}", f"{vcode} layout follows the spec",
                     f"detail_views.{vcode}", t, role)


LAYOUT_JS = """() => {
  const probs = [];
  const se = document.scrollingElement;
  if (se.scrollWidth > se.clientWidth + 1) probs.push(`page scrolls sideways (${se.scrollWidth} > ${se.clientWidth})`);
  document.querySelectorAll('[data-zas="title"], [data-zas="fact"], [data-zas="stat"], [data-zas="tab"], .zas-ph h1').forEach(e => {
    const cs = getComputedStyle(e);
    if (e.scrollWidth > e.clientWidth + 1 && cs.textOverflow !== 'ellipsis' && cs.overflowX !== 'auto')
      probs.push(`clipped: ${(e.dataset.zas || e.tagName)}:${(e.innerText || '').slice(0, 40)}`);
  });
  return probs; }"""


def g_layout(Dx, b):
    try:
        records = load_json(Dx.ws, "test_records.json")
    except (OSError, ValueError):
        records = {}
    target = auth.load_users(Dx.ws)["target"]
    roles = [r for r in Dx.M["roles"] if r not in ("AnonymousUsers", "SystemUsers")]
    for role in roles:
        paths = []
        for it in Dx.M["roles"][role].get("menu", []):
            for i in (it.get("items") or [it]):
                p = Dx.M["pages"].get(i.get("page"))
                if p:
                    paths.append((i["page"], p["route"]))
        for vcode, V in (Dx.M.get("detail_views") or {}).items():
            if role in viewers(Dx, V) and records.get(V["hero"]):
                paths.append((vcode, browser.detail_path(Dx.M, V["hero"], records[V["hero"]][-1])))
        for width in (1440, 1280):
            def t(role=role, paths=paths, width=width):
                try:
                    s = auth.login(Dx.ws, role)
                except auth.AuthError as e:
                    return None, f"cannot log in: {e}"
                rp = browser.RolePage(b, target, s, viewport={"width": width, "height": 900})
                probs = []
                try:
                    for code, path in paths:
                        rp.open(path, wait='[data-zas="page"], [data-zas="empty"]')
                        rp.page.wait_for_timeout(250)
                        probs += [f"{code}: {x}" for x in rp.page.evaluate(LAYOUT_JS)]
                finally:
                    rp.close()
                return not probs, "; ".join(probs[:20])
            Dx.check(f"design.layout.{re.sub(r'[^a-z0-9]+', '_', role.lower())}.{width}", f"no overflow or clipping at {width}px",
                     f"roles.{role}.menu", t, role)


# ───────────────────────── parity ─────────────────────────

KIT_TREE_JS = os.path.join(HERE, "kit_tree.js")


def flat_tree(tree, depth=0):
    """[(depth, kit, title, items)] in document order."""
    out = []
    for n in tree or []:
        out.append((depth, n.get("kit"), n.get("title") or "", tuple(n.get("items") or ())))
        out += flat_tree(n.get("children"), depth + 1)
    return out


def parity_diff(want, got):
    """What the built screen lacks or adds against the approved kit tree, as short lines."""
    import difflib

    def name(b):
        return f'{b[1]} "{b[2]}"' if b[2] else b[1]

    W, G = flat_tree(want), flat_tree(got)
    sm = difflib.SequenceMatcher(a=[(b[1], b[2]) for b in W], b=[(b[1], b[2]) for b in G], autojunk=False)
    probs = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for a, b_ in zip(W[i1:i2], G[j1:j2]):
                if a[3] != b_[3]:
                    miss = [x for x in a[3] if x not in b_[3]]
                    extra = [x for x in b_[3] if x not in a[3]]
                    what = "labels" if a[1] == "kpis" else "columns" if a[1] == "table" else "items"
                    if miss or extra:
                        probs.append(f"{name(a)}: {what} " + "; ".join(
                            x for x in (f"missing {miss}" if miss else "", f"extra {extra}" if extra else "") if x))
                    else:
                        probs.append(f"{name(a)}: {what} out of order {list(b_[3])} (approved {list(a[3])})")
            continue
        probs += [f"missing {name(b)}" for b in W[i1:i2]]
        probs += [f"not in the approved screen: {name(b)}" for b in G[j1:j2]]
    return probs


def parity_target(Dx, hole):
    """(path to open, tab to click or None, root selector, entity or None) for a custom screen's hole."""
    where = hole["where"]
    if hole["kind"] == "custom_page":
        page = Dx.M["pages"].get(where.split(".", 1)[1]) or {}
        return page.get("route"), None, '[data-zas="page"]', None
    vcode = where.split(".")[1]
    V = Dx.M["detail_views"].get(vcode) or {}
    key = hole["function"].split("__custom__", 1)[-1]
    m = re.search(r"\.tabs\.([^.\[]+)", where)
    return None, (m.group(1) if m else None), f'[data-zas="panel"][data-zas-key="{key}"]', V.get("hero")


def g_parity(Dx, b):
    bundle = os.path.join(Dx.ws, ".zas", "bundle")
    try:
        with open(os.path.join(bundle, "manifest.json"), encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        Dx.add("design.parity", "custom screens match the approved preview", "", "skip",
               "no approval bundle (.zas/bundle/): this build had no preview to compare with")
        return
    extractor = open(KIT_TREE_JS, encoding="utf-8").read()
    try:
        records = load_json(Dx.ws, "test_records.json")
    except (OSError, ValueError):
        records = {}
    target = auth.load_users(Dx.ws)["target"]
    holes = {h["bundle"].rstrip("/").rsplit("/", 1)[-1]: h for h in Dx.M.get("holes") or [] if h.get("bundle")}
    looks = []
    for scr in manifest.get("screens") or []:
        folder = scr["folder"].split("/", 1)[-1]
        hole = holes.get(folder)
        if not hole:
            continue
        for v in scr.get("variants") or []:
            role = v["roles"][0]
            rid = f"design.parity.{folder}.{re.sub(r'[^a-z0-9]+', '_', role.lower())}"

            def t(v=v, role=role, hole=hole, scr=scr, folder=folder):
                path, tab, root_sel, hero = parity_target(Dx, hole)
                sess = auth.login(Dx.ws, role)
                if hero:
                    uids = records.get(hero) or []
                    if not uids:
                        return None, "no record to open: run zas_test.api first"
                    path = browser.detail_path(Dx.M, hero, browser.visible_uid(Dx.M, hero, sess, uids))
                if not path:
                    return None, "no route for this screen"
                rp = browser.RolePage(b, target, sess)
                try:
                    rp.open(path, wait='[data-zas="page"], [data-zas="header"], [data-zas="empty"]')
                    if tab:
                        btn = rp.page.query_selector(f'[data-zas="tab"][data-zas-key="{tab}"]')
                        if btn:
                            btn.click()
                            rp.page.wait_for_load_state("networkidle")
                    root = rp.page.query_selector(root_sel)
                    if not root:
                        return None, f"{scr['path']} is not on the page for {role} on this record (roles or show_when)"
                    rp.page.wait_for_timeout(250)
                    got = rp.page.evaluate(f"el => ({extractor})(el)", root)
                    shot_dir = os.path.join(Dx.ws, ".zas", "screens", "parity")
                    os.makedirs(shot_dir, exist_ok=True)
                    built = os.path.join(shot_dir, f"{folder}.{re.sub(r'[^a-z0-9]+', '_', role.lower())}.png")
                    root.screenshot(path=built)
                    approved = f".zas/bundle/{v['shot']}" if v.get("shot") else None
                    looks.append({"screen": scr["path"], "where": hole["where"], "role": role,
                                  "approved": approved, "built": os.path.relpath(built, Dx.ws),
                                  "hand_written": bool(v.get("hand_written"))})
                    if v.get("hand_written"):
                        return None, "hand-written sketch: no kit blocks to compare; the look covers it"
                    probs = parity_diff(v.get("tree") or [], got)
                    pair = f" Compare {os.path.relpath(built, Dx.ws)} with {approved}." if approved else ""
                    return not probs, "; ".join(probs) + "." + pair if probs else ""
                finally:
                    rp.close()
            Dx.check(rid, f"{scr['path']} matches the approved preview", hole["where"], t, role)
    with open(os.path.join(Dx.ws, ".zas", "parity_looks.json"), "w", encoding="utf-8") as f:
        json.dump(looks, f, indent=1)


RUNNERS = {"lint": g_lint, "gallery": g_gallery, "tokens": g_tokens, "tree": g_tree, "layout": g_layout, "parity": g_parity}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace")
    ap.add_argument("--only")
    ap.add_argument("--make-goldens", action="store_true")
    ap.add_argument("--gallery-url")
    ap.add_argument("--out", default=GOLDENS)
    a = ap.parse_args(argv)
    if a.make_goldens:
        if not a.gallery_url:
            ap.error("--make-goldens needs --gallery-url (a page rendering ZasGallery, e.g. the scratch app's vite preview)")
        with browser.browser() as b:
            rp = gallery_page(b, url=a.gallery_url)
            paths = shoot_sections(rp, a.out)
            rp.close()
            with open(os.path.join(a.out, "meta.json"), "w") as f:
                json.dump({"platform": sys.platform, "chromium": b.version}, f)
        print("\n".join(f"golden {k}: {v}" for k, v in paths.items()))
        return 0
    if not a.workspace:
        ap.error("--workspace is required")
    groups = [g for g in (a.only or ",".join(GROUPS)).split(",") if g]
    Dx = D(a.workspace)
    if groups == ["lint"]:
        g_lint(Dx)
    else:
        with browser.browser() as b:
            for g in groups:
                RUNNERS[g](Dx, b)
    save_results(a.workspace, "design", Dx.results, {"groups": groups})
    print_summary("design", Dx.results)
    return 1 if any(r["status"] == "fail" for r in Dx.results) else 0


if __name__ == "__main__":
    sys.exit(main())
