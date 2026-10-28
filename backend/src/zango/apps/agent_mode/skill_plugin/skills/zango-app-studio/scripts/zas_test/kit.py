"""
The app's kit against the approved prototype (open mode; references/open-mode.md, "The kit").

frontend/src/custom/kit/map.json names each kit piece the prototype shows, where one instance of it
sits in the prototype (screen, persona, CSS selector) and the props that draw the same instance with
the app's kit. For each piece this crops the instance from the live prototype (.zas/bundle/prototype/
prototype.html, opened the way the capture opens it), shoots the app's piece on
/app/__zas?kit=mockup&piece=<id>&w=<crop width>, and scores the pair: the share of pixels that
differ, with both scaled to the crop's size. Over KIT_LIMIT fails the piece; the build's kit rounds
send it back to the agent, and what is left goes to the internal report, never to the verdict.

Writes .zas/screens/kit/<id>.{mockup,built}.png, .zas/kit_looks.json and .zas/screens/kit/index.html
(each piece next to its crop: a debugging page, not for the app's users).
"""

import html
import json
import os
import re

from . import auth, browser

KIT_LIMIT = 0.05
# zas/kit.tsx KIT_PIECES. ZasTable and makeShell are kit pieces too, but they need data and a layout:
# the screens' parity compares them, not this gallery.
KIT_PIECES = ("Button", "Badge", "Chip", "Panel", "StatTile", "Tabs", "Timeline", "FieldGrid", "Drawer", "Modal",
              "EmptyState", "Banner", "Kpis", "Bars", "List", "MiniTable", "Board", "Progress", "ZasTable", "makeShell")
GALLERY_PIECES = tuple(p for p in KIT_PIECES if p not in ("ZasTable", "makeShell"))
# a piece drawn into a portal: shoot the panel, not the gallery's (empty) body
BUILT_DEFAULT = {"Drawer": "aside.zas-dw", "Modal": ".zas-mo"}
PROTO_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com", "cdnjs.cloudflare.com", "cdn.jsdelivr.net", "unpkg.com"}
PROTO_WIDTH = 1280
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

GO_JS = """async ([screen, role]) => {
  const meta = ((ZAS.M || {}).screens || []).find(s => s.id === screen) || {};
  let record = meta.sample == null ? null : meta.sample;
  if (record == null && meta.record && ZAS.store && ZAS.store.list) {
    const rows = ZAS.store.list(meta.record) || [];
    if (rows.length) record = rows[0].id;
  }
  ZAS.go(screen, { role, record, params: meta.params || {}, replace: true });
  await new Promise(r => setTimeout(r, 300));
  try { await document.fonts.ready; } catch (e) {}
  window.scrollTo(0, 0);
  document.querySelectorAll('.z-persona, .z-toast').forEach(n => n.remove());
  return true;
}"""


def kit_dir(ws):
    return os.path.join(ws, "frontend", "src", "custom", "kit")


def load_map(ws):
    """(pieces, problem): the kit map's pieces, or a problem with the file."""
    path = os.path.join(kit_dir(ws), "map.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError:
        return [], "no frontend/src/custom/kit/map.json"
    except ValueError as e:
        return [], f"frontend/src/custom/kit/map.json is not JSON: {e}"
    pieces = data.get("pieces") if isinstance(data, dict) else None
    if not isinstance(pieces, list):
        return [], 'frontend/src/custom/kit/map.json: {"pieces": [...]} expected'
    return [p for p in pieces if isinstance(p, dict)], None


def exported_pieces(ws):
    """The kit pieces src/custom/kit/index.ts exports (its own Button, Panel…)."""
    try:
        src = open(os.path.join(kit_dir(ws), "index.ts"), encoding="utf-8").read()
    except OSError:
        return set()
    src = re.sub(r"//[^\n]*|/\*.*?\*/", "", src, flags=re.S)
    names = set(re.findall(r"export\s+(?:const|function|class)\s+(\w+)", src))
    for block in re.findall(r"export\s*\{([^}]*)\}", src):
        for part in block.split(","):
            bits = part.split(" as ")
            name = bits[-1].strip()
            if bits[0].strip() == "default" and len(bits) == 1:
                continue
            names.add(name)
    return {n for n in names if n in KIT_PIECES}


def map_problems(ws, pieces, capture):
    """What is wrong with the map itself: the agent's to fix before anything can be compared."""
    probs, seen = [], set()
    for i, p in enumerate(pieces):
        pid, comp = str(p.get("id") or ""), p.get("component")
        where = f"map.json pieces[{i}]" + (f" ({pid})" if pid else "")
        if not ID.match(pid):
            probs.append(f"{where}: id must be lower-case letters, digits, - or _")
        elif pid in seen:
            probs.append(f"{where}: id {pid!r} is listed twice")
        seen.add(pid)
        if comp not in GALLERY_PIECES:
            probs.append(f"{where}: component {comp!r} is not one of {', '.join(GALLERY_PIECES)} "
                         "(ZasTable and the shell are compared on the screens, not in the map)")
        if "props" in p and not isinstance(p["props"], dict):
            probs.append(f"{where}: props must be an object")
        m = p.get("mockup") if isinstance(p.get("mockup"), dict) else {}
        if not (m.get("screen") and m.get("role") and m.get("selector")):
            probs.append(f"{where}: mockup needs screen, role and selector (one instance of the piece)")
        elif capture is not None and m["screen"] not in capture:
            probs.append(f"{where}: screen {m['screen']!r} is not a prototype screen")
        elif capture is not None and m["role"] not in {r.get("role") for r in capture[m["screen"]].get("roles") or []}:
            probs.append(f"{where}: screen {m['screen']!r} has no persona {m['role']!r}")
    mapped = {p.get("component") for p in pieces}
    for name in sorted(exported_pieces(ws) - mapped - {"ZasTable", "makeShell"}):
        probs.append(f"kit/index.ts exports {name} but map.json has no piece for it: nothing compares it")
    return probs


def kit_score(built, mockup):
    """Share of pixels that differ (0 = the same), and how far the sizes differ; the score is the
    larger. Both in grey, centred on one canvas (never stretched: a 2 px wider button would shift all
    its text) and lightly blurred, so anti-aliasing and sub-pixel text don't count but a different
    fill, border or layout does. None without PIL."""
    try:
        from PIL import Image, ImageChops, ImageFilter
    except ImportError:
        return None
    A, B = Image.open(mockup).convert("L"), Image.open(built).convert("L")
    built_size = [B.width, B.height]
    size_gap = max(abs(A.width - B.width) / max(A.width, 1), abs(A.height - B.height) / max(A.height, 1))
    size = (max(A.width, B.width), max(A.height, B.height))

    def canvas(im):
        c = Image.new("L", size, 255)
        c.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2))
        return c.filter(ImageFilter.GaussianBlur(1.5))
    hist = ImageChops.difference(canvas(A), canvas(B)).histogram()
    frac = sum(hist[40:]) / max(1, size[0] * size[1])
    return {"score": round(max(frac, min(1.0, size_gap)), 3), "pixels": round(frac, 3),
            "size": [A.width, A.height], "built_size": built_size, "size_gap": round(size_gap, 3)}


def proto_page(b, html_text):
    ctx = b.new_context(viewport={"width": PROTO_WIDTH, "height": 900}, device_scale_factor=1, service_workers="block")
    page = ctx.new_page()

    def route(r):
        from urllib.parse import urlparse
        if (urlparse(r.request.url).hostname or "") in PROTO_HOSTS or r.request.url.startswith(("data:", "about:")):
            r.continue_()
        else:
            r.abort()
    page.route("**/*", route)
    try:
        page.set_content(html_text, wait_until="load", timeout=30000)
    except Exception:  # noqa: BLE001 - a slow CDN still leaves the inline parts running
        pass
    page.add_style_tag(content=".z-persona,.z-toast{display:none!important}"
                       "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}")
    return ctx, page


def crop_mockup(b, html_text, piece, out):
    """Shoot the piece's instance in the prototype; (box, problem)."""
    m = piece["mockup"]
    ctx, page = proto_page(b, html_text)
    try:
        if not page.evaluate("typeof window.ZAS === 'object' && typeof ZAS.go === 'function'"):
            return None, "the prototype did not load (no ZAS runtime)"
        page.evaluate(GO_JS, [m["screen"], m["role"]])
        loc = page.locator(m["selector"])
        n = loc.count()
        idx = int(m.get("index") or 0)
        if n <= idx:
            return None, (f"selector `{m['selector']}` matches {n} element(s) on prototype screen {m['screen']} "
                          f"as {m['role']}" + (f" (index {idx})" if n else ""))
        el = loc.nth(idx)
        el.scroll_into_view_if_needed(timeout=3000)
        box = el.bounding_box()
        if not box or box["width"] < 2 or box["height"] < 2:
            return None, f"`{m['selector']}` is not visible on prototype screen {m['screen']}"
        el.screenshot(path=out)
        return box, None
    finally:
        ctx.close()


def shoot_built(b, target, session, piece, width, out):
    rp = browser.RolePage(b, target, session, viewport={"width": max(PROTO_WIDTH, int(width) + 80), "height": 900},
                          pinned=True)
    try:
        rp.open(f"/app/__zas?kit=mockup&piece={piece['id']}&w={int(round(width))}",
                wait=f'[data-kit-piece="{piece["id"]}"]')
        rp.page.add_style_tag(content="*,*::before,*::after{animation:none!important;transition:none!important;"
                              "caret-color:transparent!important}")
        rp.page.wait_for_timeout(200)
        if rp.page.locator("[data-kit-error]").count():
            return f"the gallery has no kit piece {piece.get('component')}"
        sel = piece.get("built") or BUILT_DEFAULT.get(piece.get("component"))
        loc = rp.page.locator(sel) if sel else rp.page.locator(f'[data-kit-body="{piece["id"]}"] > *')
        if not loc.count():
            return f"nothing to shoot on /app/__zas?kit=mockup&piece={piece['id']}" + (f" (`{sel}`)" if sel else "")
        loc.first.screenshot(path=out)
        errs = [e for e in rp.errors if "page error" in e]
        return f"the piece throws: {errs[0]}" if errs else None
    finally:
        rp.close()


def side_by_side(out_dir, looks):
    rows = []
    for x in looks:
        score = "no score" if x.get("score") is None else f"{x['score']:.0%}"
        cells = "".join(
            f'<td>{"<img src=%s>" % html.escape(os.path.basename(x[k]), quote=True) if x.get(k) else "-"}</td>'
            for k in ("mockup", "built"))
        rows.append(f"<tr><th>{html.escape(x['id'])}<br><small>{html.escape(str(x.get('component')))}"
                    f" · {score}</small><br><small>{html.escape(x.get('problem') or '')}</small></th>{cells}</tr>")
    page = ("<!doctype html><meta charset=utf-8><title>App kit vs prototype</title><style>"
            "body{font:13px system-ui;margin:24px}td,th{border:1px solid #ccc;padding:8px;vertical-align:top;text-align:left}"
            "img{max-width:560px}</style><h1>App kit vs prototype</h1><table><tr><th>Piece</th><th>Prototype</th>"
            "<th>App kit</th></tr>" + "".join(rows) + "</table>")
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)


def g_kit(Dx, b):
    from .design import first_session, is_open_mode

    ws = Dx.ws
    if not is_open_mode(ws):
        Dx.add("design.kit", "the app's kit matches the prototype", "kit", "skip",
               "default design: the app uses the default kit")
        return
    proto = os.path.join(ws, ".zas", "bundle", "prototype")
    try:
        with open(os.path.join(proto, "capture.json"), encoding="utf-8") as f:
            capture = {sc["id"]: sc for sc in json.load(f).get("screens") or []}
    except (OSError, ValueError):
        capture = None
    pieces, bad = load_map(ws)
    probs = [bad] if bad else map_problems(ws, pieces, capture)
    if not bad and not pieces:
        # the kit draws the standard pages; a rebuild screen is ported from the prototype and needs none
        kit_pages = [r["id"] for r in ((Dx.M or {}).get("prototype") or {}).get("screens") or []
                     if r.get("cls") in ("kit", "theme")]
        if not kit_pages:
            Dx.add("design.kit", "the app's kit matches the prototype", "kit", "skip",
                   "every mapped screen is ported from the prototype: no kit page to draw")
            return
        probs.append(f"map.json has no pieces: kit pages ({', '.join(kit_pages[:6])}) draw with the app's kit; "
                     "build the kit pieces the prototype shows (open-mode.md, \"The kit\")")
    Dx.check("design.kit.map", "the kit map names the prototype's pieces", "kit",
             lambda: (not probs, "\n".join(probs[:20])))
    if probs:
        return
    html_path = os.path.join(proto, "prototype.html")
    if not os.path.isfile(html_path):
        Dx.add("design.kit", "the app's kit matches the prototype", "kit", "skip",
               "no reference: the bundle has no prototype.html")
        return
    html_text = open(html_path, encoding="utf-8").read()
    out_dir = os.path.join(ws, ".zas", "screens", "kit")
    os.makedirs(out_dir, exist_ok=True)
    target = auth.load_users(ws)["target"]
    session = None
    looks = []
    for p in pieces:
        pid = p["id"]
        look = {"id": pid, "component": p.get("component"), "screen": p["mockup"]["screen"],
                "role": p["mockup"]["role"], "selector": p["mockup"]["selector"], "score": None,
                "mockup": None, "built": None}
        looks.append(look)

        def t(p=p, pid=pid, look=look):
            nonlocal session
            mock = os.path.join(out_dir, f"{pid}.mockup.png")
            box, why = crop_mockup(b, html_text, p, mock)
            if why:
                look["problem"] = why
                return False, f"{why}: fix the piece's mockup selector in map.json"
            look["mockup"] = os.path.relpath(mock, ws)
            if session is None:
                session = first_session(Dx)[1]
            built = os.path.join(out_dir, f"{pid}.built.png")
            why = shoot_built(b, target, session, p, box["width"], built)
            if why:
                look["problem"] = why
                return False, why
            look["built"] = os.path.relpath(built, ws)
            s = kit_score(built, mock)
            if s is None:
                return None, "Pillow not installed (pip install pillow)"
            look.update(s)
            size = (f"; size {s['built_size'][0]}x{s['built_size'][1]} vs the prototype's {s['size'][0]}x{s['size'][1]}"
                    if s["size_gap"] > 0.1 else "")
            return s["score"] <= KIT_LIMIT, (f"{s['score']:.0%} different from the prototype's piece (limit "
                                             f"{KIT_LIMIT:.0%}){size}: compare {look['mockup']} with {look['built']}")
        Dx.check(f"design.kit.{pid}", f"kit piece {pid} looks like the prototype's", f"kit.{pid}", t)
    with open(os.path.join(ws, ".zas", "kit_looks.json"), "w", encoding="utf-8") as f:
        json.dump(looks, f, indent=1)
    side_by_side(out_dir, [{**x, "mockup": x["mockup"] and os.path.join(ws, x["mockup"]),
                            "built": x["built"] and os.path.join(ws, x["built"])} for x in looks])
