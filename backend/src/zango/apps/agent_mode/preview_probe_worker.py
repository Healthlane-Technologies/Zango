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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
