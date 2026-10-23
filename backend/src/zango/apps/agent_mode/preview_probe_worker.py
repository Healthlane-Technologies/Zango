"""Headless runner for the App Studio preview (see preview_probe.py).

Run as a plain script, never imported by Django: ``python preview_probe_worker.py <page.html>``.
It loads the template's preview page (the same page the console shows, adapter included) in
Chromium, then answers JSON requests, one per stdin line, with one JSON line on stdout:

    {"id": 1, "op": "check", "yaml": "...", "paths": [...] | null}
        → {"id": 1, "ok": true, "result": {"parse_error": null, "results": [...]}}
    {"id": 2, "op": "look", "yaml": "...", "path": "...", "role": null, "record": null, "width": 1280}
        → {"id": 2, "ok": true, "result": {"show": {...}, "run": {...}, "png": "<base64>"}}
    {"id": 3, "op": "sketches", "yaml": "..."}
        → {"id": 3, "ok": true, "result": {"parse_error": null, "sketches": [...]}}
    {"id": 4, "op": "capture", "yaml": "...", "path": "...", "kit_tree": "<js>", "max_variants": 3}
        → {"id": 4, "ok": true, "result": {"variants": [{roles, record, tree, run, png}], "in_page": "<base64>"}}
      (the approval bundle: one screen for every role that opens it; roles whose screen has the same
      kit tree share one screenshot; a tab or panel is also shot once in its 360 page)
    {"id": 5, "op": "capture_layout", "yaml": "...", "kind": "view" | "shell", "page": "<code>", "view": 1}
        → {"id": 5, "ok": true, "result": {"role", "page", "layout": {...}, "png": "<base64>"}}
      (the approval bundle's standard screens: a list page in one of its declared views, or the app
      shell on a role's landing page, shot with the shell around it at 1440px)

Open mode (Free design), one batch instead of requests:
``python preview_probe_worker.py --open <prototype.html> <out_dir>`` opens the assembled prototype,
visits every manifest screen for every role through ``ZAS.go`` and writes, per screen,
``dom.<role>.html`` (the rendered markup, scripts removed), ``shot.<role>.png`` and
``css.used.css`` (the stylesheet rules that match), then prints one JSON summary line. Roles whose
screen renders the same markup are written once (``same_as``). Allowed hosts: web fonts and the
script CDNs a prototype may use (PROTO_HOSTS).

The page is sealed: every request is refused except the web fonts it styles text with. Sketch
code written by the agent runs only against the page's seeded demo data. The parent kills this
process (and its browser) when a request runs too long.
"""

from __future__ import annotations

import base64
import json
import sys

from urllib.parse import urlparse


FONT_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com"}
# A prototype may also load pinned scripts from these (prototype.LIBRARY_HOSTS).
PROTO_HOSTS = FONT_HOSTS | {"cdnjs.cloudflare.com", "cdn.jsdelivr.net", "unpkg.com"}
OPEN_WIDTH = 1280
OPEN_MAX_HEIGHT = 2400
MAX_SHOT_HEIGHT = 2000
APP_WIDTH = 1440  # the app frame's width in a layout shot (the preview's "1440" frame)

# Puts a list page (in one declared view) or a role's landing page on screen, in the preview's own
# state, and says how the page is laid out. Uses the page's globals (S, canPage, landingRoute,
# render): a preview without them answers {ok: false}.
LAYOUT_JS = """([kind, pageCode, viewIndex]) => {
  if (typeof S !== 'object' || !S.M || typeof render !== 'function' || typeof canPage !== 'function')
    return { ok: false, error: 'This preview page cannot be driven to a page (no S/render/canPage).' };
  const M = S.M; const roles = M.roles.map(r => r.name);
  let role = null, page = null;
  if (kind === 'view') {
    page = M.pages[pageCode];
    if (!page) return { ok: false, error: `No page ${pageCode} in the spec` };
    role = roles.find(r => canPage(page, r));
    if (!role) return { ok: false, error: `No role can open ${pageCode}` };
  } else {
    for (const r of roles) { S.role = r; const lr = landingRoute(); if (lr && lr.page) { role = r; page = M.pages[lr.page]; break; } }
    if (!role) return { ok: false, error: 'No role has a landing page' };
  }
  S.role = role; S.frame = '1440'; S.ui = { tables: {}, drawer: null };
  try { MODAL = null; } catch (e) { /* older page */ }
  if (kind === 'view') S.views[page.code] = viewIndex || 0;
  S.route = { page: page.code };
  render();
  const q = s => document.querySelector('#zapp ' + s);
  const sw = q('.z-vsw');
  const text = el => el ? el.textContent.replace(/\\s+/g, ' ').trim() : null;
  return { ok: true, role, page: page.code, layout: {
    switcher: sw ? (sw.closest('.z-tb') ? 'toolbar' : 'header') : null,
    shell: {
      sidebar: !!q('.z-side'),
      brand: text(q('.z-side .z-brand b')),
      brand_role: text(q('.z-side .z-brand span')),
      user_in_sidebar: !!q('.z-side .z-user'),
      topbar: !!q('.z-top'),
      topbar_title: text(q('.z-top .z-crumbs')),
      topbar_actions: [...document.querySelectorAll('#zapp .z-top .z-ib')].length,
    },
  } };
}"""


def _send(message: dict) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def main(html_path: str) -> int:
    from playwright.sync_api import sync_playwright

    with open(html_path, encoding="utf-8") as fh:
        html = fh.read()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=1,
            service_workers="block",
        )
        page = context.new_page()

        def route(r):
            if (urlparse(r.request.url).hostname or "") in FONT_HOSTS:
                r.continue_()
            else:
                r.abort()

        page.route("**/*", route)
        page.set_content(html, wait_until="domcontentloaded")
        supported = page.evaluate(
            "typeof window.ZAS_PROBE === 'object' && typeof window.zangoLoad === 'function'"
        )
        if not supported:
            _send(
                {
                    "id": 0,
                    "ok": False,
                    "error": "This preview page has no probe (ZAS_PROBE).",
                }
            )
            return 2
        _send(
            {
                "id": 0,
                "ok": True,
                "result": {"probe": page.evaluate("ZAS_PROBE.version")},
            }
        )

        loaded = None

        def shoot(width: int, show: dict, whole_page: bool = False):
            """PNG (base64) of the element show() marked, or of the page content when whole_page."""
            if whole_page:
                page.evaluate("""() => { document.querySelectorAll('[data-zas-shot]').forEach(x => x.removeAttribute('data-zas-shot'));
                    const c = document.querySelector('.z-content'); if (c) { c.setAttribute('data-zas-shot', '1'); c.scrollTop = 0; } }""")
            height = min(max(900, int(show.get("height") or 0) + 160), MAX_SHOT_HEIGHT)
            if whole_page:
                height = MAX_SHOT_HEIGHT
            page.set_viewport_size({"width": width, "height": height})
            try:
                page.evaluate("document.fonts.ready.then(() => true)")
            except Exception:  # noqa: BLE001 - fonts are a nicety
                pass
            box = page.evaluate("ZAS_PROBE.box()")
            if not box:
                return None
            box["height"] = max(1, min(box["height"], MAX_SHOT_HEIGHT - box["y"]))
            shot = page.screenshot(type="png", clip=box, timeout=15000)
            page.set_viewport_size({"width": width, "height": 900})
            return base64.b64encode(shot).decode("ascii")

        def _untexted(tree):
            return [
                {
                    **{k: v for k, v in n.items() if k != "text"},
                    "children": _untexted(n.get("children") or []),
                }
                for n in tree or []
            ]

        def capture(req: dict) -> dict:
            path = req.get("path")
            sk = next(
                (x for x in page.evaluate("ZAS_PROBE.sketches()") if x["path"] == path),
                None,
            )
            if sk is None:
                return {"error": f"No custom screen at {path}"}
            tree_js = req.get("kit_tree") or "() => []"
            groups: dict = {}
            for role in sk.get("roles") or []:
                run = page.evaluate("([p, r]) => ZAS_PROBE.run(p, r)", [path, role])
                show = page.evaluate("([p, r]) => ZAS_PROBE.show(p, r)", [path, role])
                if not show.get("ok"):
                    continue
                tree = page.evaluate(
                    f"p => ({tree_js})(document.querySelector('[data-zas-sketch=\"' + CSS.escape(p) + '\"]'))",
                    path,
                )
                # Hand-written markup has no tree: each role counts as its own variant (capped below).
                # A hand-drawn block's text holds data, so roles group by structure and look only.
                key = (
                    json.dumps(_untexted(tree), sort_keys=True)
                    if tree
                    else f"raw:{role}"
                )
                if key not in groups:
                    groups[key] = {
                        "roles": [],
                        "record": show.get("record"),
                        "tree": tree,
                        "run": run,
                        "png": None,
                    }
                groups[key]["roles"].append(role)
            variants = list(groups.values())[: int(req.get("max_variants") or 3)]
            in_page = None
            for i, v in enumerate(variants):
                show = page.evaluate(
                    "([p, r]) => ZAS_PROBE.show(p, r)", [path, v["roles"][0]]
                )
                if show.get("ok"):
                    v["png"] = shoot(1280, show)
                    if i == 0 and sk.get("kind") != "page":
                        in_page = shoot(1280, show, whole_page=True)
            return {
                "variants": variants,
                "in_page": in_page,
                "kind": sk.get("kind"),
                "title": sk.get("title"),
            }

        def capture_layout(req: dict) -> dict:
            info = page.evaluate(
                LAYOUT_JS, [req.get("kind"), req.get("page"), int(req.get("view") or 0)]
            )
            if not info.get("ok"):
                return {"error": info.get("error")}
            # The editor takes about a third of the page: make the stage wide enough for the frame.
            page.set_viewport_size({"width": int(APP_WIDTH * 1.6), "height": 1000})
            page.evaluate("render()")
            try:
                page.evaluate("document.fonts.ready.then(() => true)")
            except Exception:  # noqa: BLE001 - fonts are a nicety
                pass
            png = None
            frame = page.query_selector("#zapp")
            if frame is not None:
                png = base64.b64encode(
                    frame.screenshot(type="png", timeout=15000)
                ).decode("ascii")
            page.set_viewport_size({"width": 1280, "height": 900})
            page.evaluate("S.frame = 'full'; render()")
            return {
                "role": info["role"],
                "page": info["page"],
                "layout": info["layout"],
                "png": png,
            }

        def load(yaml_text: str):
            nonlocal loaded
            if yaml_text == loaded:
                return page.evaluate(
                    "S.parseErr ? String(S.parseErr.message || S.parseErr) : null"
                )
            err = page.evaluate(
                "y => { window.zangoLoad(y); return S.parseErr ? String(S.parseErr.message || S.parseErr) : null; }",
                yaml_text,
            )
            loaded = yaml_text
            return err

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            req = {}
            try:
                req = json.loads(line)
                op = req.get("op")
                parse_error = load(req.get("yaml") or "")
                if op == "check":
                    results = (
                        []
                        if parse_error
                        else page.evaluate("p => ZAS_PROBE.runAll(p)", req.get("paths"))
                    )
                    _send(
                        {
                            "id": req.get("id"),
                            "ok": True,
                            "result": {"parse_error": parse_error, "results": results},
                        }
                    )
                elif op == "look":
                    if parse_error:
                        _send(
                            {
                                "id": req.get("id"),
                                "ok": True,
                                "result": {"parse_error": parse_error},
                            }
                        )
                        continue
                    width = int(req.get("width") or 1280)
                    page.set_viewport_size({"width": width, "height": 900})
                    args = [req.get("path"), req.get("role"), req.get("record")]
                    run = page.evaluate("([p, r, i]) => ZAS_PROBE.run(p, r, i)", args)
                    show = page.evaluate("([p, r, i]) => ZAS_PROBE.show(p, r, i)", args)
                    png = None
                    if show.get("ok"):
                        height = min(
                            max(900, int(show.get("height") or 0) + 160),
                            MAX_SHOT_HEIGHT,
                        )
                        page.set_viewport_size({"width": width, "height": height})
                        try:
                            page.evaluate("document.fonts.ready.then(() => true)")
                        except Exception:  # noqa: BLE001 - fonts are a nicety
                            pass
                        box = page.evaluate("ZAS_PROBE.box()")
                        box["height"] = min(box["height"], MAX_SHOT_HEIGHT - box["y"])
                        shot = page.screenshot(type="png", clip=box, timeout=15000)
                        png = base64.b64encode(shot).decode("ascii")
                    _send(
                        {
                            "id": req.get("id"),
                            "ok": True,
                            "result": {"show": show, "run": run, "png": png},
                        }
                    )
                elif op == "sketches":
                    sketches = (
                        [] if parse_error else page.evaluate("ZAS_PROBE.sketches()")
                    )
                    _send(
                        {
                            "id": req.get("id"),
                            "ok": True,
                            "result": {
                                "parse_error": parse_error,
                                "sketches": sketches,
                            },
                        }
                    )
                elif op == "capture_layout":
                    result = (
                        {"parse_error": parse_error}
                        if parse_error
                        else capture_layout(req)
                    )
                    _send({"id": req.get("id"), "ok": True, "result": result})
                elif op == "capture":
                    result = (
                        {"parse_error": parse_error} if parse_error else capture(req)
                    )
                    _send({"id": req.get("id"), "ok": True, "result": result})
                else:
                    _send(
                        {
                            "id": req.get("id"),
                            "ok": False,
                            "error": f"Unknown op {op!r}",
                        }
                    )
            except Exception as exc:  # noqa: BLE001 - reported to the parent, which decides
                _send(
                    {
                        "id": req.get("id"),
                        "ok": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        browser.close()
    return 0


# The rendered markup of the page, without scripts, the persona bar or toasts: what the build ports.
OPEN_DOM_JS = """() => {
  const body = document.body.cloneNode(true);
  body.querySelectorAll('script, noscript, .z-persona, .z-toast, template').forEach(n => n.remove());
  return body.innerHTML.replace(/\\n\\s*\\n+/g, '\\n');
}"""

# Indexes of the stylesheet rules that match the current DOM (any role so far is unioned in Python).
OPEN_CSS_JS = """() => {
  const hits = [];
  const strip = s => s.replace(/::?(before|after|placeholder|selection|marker|-webkit-[a-z-]+|-moz-[a-z-]+)\\b(\\([^)]*\\))?/g, '')
                      .replace(/:(hover|focus|focus-visible|focus-within|active|visited|checked|disabled|empty)\\b/g, '');
  const matches = sel => sel.split(',').some(part => {
    const s = strip(part).trim() || '*';
    try { return !!document.querySelector(s); } catch (e) { return false; }
  });
  const walk = (rules, path) => {
    for (let i = 0; i < rules.length; i++) {
      const r = rules[i], key = path.concat(i).join('.');
      if (r.type === 1) { if (matches(r.selectorText)) hits.push(key); }
      else if (r.cssRules && r.type !== 7) walk(r.cssRules, path.concat(i));   // @media, @supports
      else hits.push(key);                                                     // @font-face, @keyframes, @import
    }
  };
  Array.from(document.styleSheets).forEach((sh, si) => { if (sh.ownerNode && sh.ownerNode.hasAttribute('data-zas-probe')) return; try { walk(sh.cssRules, [si]); } catch (e) {} });
  return hits;
}"""

# The rules picked above, in stylesheet order, as text (group rules keep only their matching children).
OPEN_CSS_TEXT_JS = """(keys) => {
  const want = new Set(keys), out = [];
  const emit = (rules, path) => {
    const parts = [];
    for (let i = 0; i < rules.length; i++) {
      const r = rules[i], key = path.concat(i).join('.');
      if (r.type === 1 || !r.cssRules || r.type === 7) { if (want.has(key)) parts.push(r.cssText); }
      else {
        const inner = emit(r.cssRules, path.concat(i));
        if (inner.length) parts.push(r.cssText.slice(0, r.cssText.indexOf('{') + 1) + '\\n' + inner.join('\\n') + '\\n}');
      }
    }
    return parts;
  };
  Array.from(document.styleSheets).forEach((sh, si) => { if (sh.ownerNode && sh.ownerNode.hasAttribute('data-zas-probe')) return; try { out.push(...emit(sh.cssRules, [si])); } catch (e) {} });
  return out.join('\\n');
}"""

OPEN_GO_JS = """async ([screen, role]) => {
  const M = ZAS.M || {};
  const meta = (M.screens || []).find(s => s.id === screen) || {};
  let record = meta.sample == null ? null : meta.sample;
  if (record == null && meta.record && ZAS.store && ZAS.store.list) {
    const rows = ZAS.store.list(meta.record) || [];
    if (rows.length) record = rows[0].id;
  }
  const before = (ZAS.errors || []).length;
  ZAS.go(screen, { role, record, replace: true });
  await new Promise(r => setTimeout(r, 250));
  try { await document.fonts.ready; } catch (e) {}
  window.scrollTo(0, 0);
  document.querySelectorAll('.z-persona, .z-toast').forEach(n => n.remove());
  const text = (document.body.innerText || '').trim();
  return {
    record,
    errors: (ZAS.errors || []).slice(before).map(e => (e.part ? e.part + ': ' : '') + e.message),
    blank: text.length < 20,
    height: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight),
  };
}"""


def open_capture(html_path: str, out_dir: str) -> int:
    """Every manifest screen x role of an open-mode prototype, written under out_dir/screens/."""
    import hashlib
    import os

    from playwright.sync_api import sync_playwright

    with open(html_path, encoding="utf-8") as fh:
        html = fh.read()
    summary: dict = {"ok": True, "screens": [], "load_errors": [], "blocked": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport={"width": OPEN_WIDTH, "height": 900},
            device_scale_factor=1,
            service_workers="block",
        )
        page = context.new_page()

        def route(r):
            host = urlparse(r.request.url).hostname or ""
            if host in PROTO_HOSTS:
                r.continue_()
            else:
                if len(summary["blocked"]) < 20:
                    summary["blocked"].append(r.request.url[:200])
                r.abort()

        page.route("**/*", route)
        page.on(
            "pageerror",
            lambda e: summary["load_errors"].append(str(e)[:300])
            if len(summary["load_errors"]) < 20
            else None,
        )
        try:
            page.set_content(html, wait_until="load", timeout=30000)
        except Exception:  # noqa: BLE001 - a slow CDN still leaves the inline parts running
            pass
        if not page.evaluate(
            "typeof window.ZAS === 'object' && typeof ZAS.go === 'function'"
        ):
            _send({"ok": False, "error": "The prototype has no ZAS runtime."})
            return 2
        # The persona switcher and toasts are the prototype's own tooling, not the app.
        page.add_style_tag(
            content=".z-persona,.z-toast{display:none!important}"
        ).evaluate("n => n.setAttribute('data-zas-probe', '')")
        manifest = page.evaluate("ZAS.M")
        roles = list((manifest.get("roles") or {}).keys())
        for screen in manifest.get("screens") or []:
            sid = screen.get("id")
            if not sid:
                continue
            folder = os.path.join(out_dir, "screens", sid)
            os.makedirs(folder, exist_ok=True)
            entry = {"id": sid, "title": screen.get("title") or sid, "roles": []}
            for key in ("record", "only", "parent", "group"):
                if screen.get(key):
                    entry[key] = screen[key]
            seen: dict = {}
            css_keys: list = []
            for role in screen.get("roles") or roles:
                try:
                    state = page.evaluate(OPEN_GO_JS, [sid, role])
                    dom = page.evaluate(OPEN_DOM_JS)
                except Exception as exc:  # noqa: BLE001 - one screen must not stop the rest
                    entry["roles"].append(
                        {"role": role, "error": f"{type(exc).__name__}: {exc}"[:300]}
                    )
                    continue
                item = {
                    "role": role,
                    **{k: v for k, v in state.items() if k != "height" and v},
                }
                digest = hashlib.sha1(dom.encode("utf-8")).hexdigest()
                if digest in seen:
                    item["same_as"] = seen[digest]
                    entry["roles"].append(item)
                    continue
                seen[digest] = role
                with open(
                    os.path.join(folder, f"dom.{role}.html"), "w", encoding="utf-8"
                ) as fh:
                    fh.write(dom)
                height = max(900, min(int(state.get("height") or 900), OPEN_MAX_HEIGHT))
                page.set_viewport_size({"width": OPEN_WIDTH, "height": height})
                page.screenshot(
                    path=os.path.join(folder, f"shot.{role}.png"),
                    type="png",
                    timeout=20000,
                )
                page.set_viewport_size({"width": OPEN_WIDTH, "height": 900})
                for k in page.evaluate(OPEN_CSS_JS):
                    if k not in css_keys:
                        css_keys.append(k)
                item["files"] = [f"dom.{role}.html", f"shot.{role}.png"]
                entry["roles"].append(item)
            if css_keys:
                with open(
                    os.path.join(folder, "css.used.css"), "w", encoding="utf-8"
                ) as fh:
                    fh.write(page.evaluate(OPEN_CSS_TEXT_JS, css_keys))
            summary["screens"].append(entry)
        browser.close()
    _send(summary)
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["--open"]:
        sys.exit(open_capture(sys.argv[2], sys.argv[3]))
    sys.exit(main(sys.argv[1]))
