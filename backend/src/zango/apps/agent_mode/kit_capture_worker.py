"""Render a spec in the kit preview and capture every screen as markup (open_from_kit's browser half).

Run as a script (``prototype_kit.open_from_kit`` starts it), so a stuck Chromium can be killed and
the ORM is never touched while the browser's loop runs::

    stdin   {"html": <kit page>, "adapter": <kit adapter js>, "yaml": <spec>, "width": 1440}
    stdout  one JSON line: {"ok": true, "css": ..., "vars": {...}, "fonts": [...], "app": {...},
             "roles": [...], "pages": [...], "views": [...], "sides": {...}} or {"ok": false, "error"}

The kit draws the spec with its own renderer; every action on a screen is a closure (``data-a``),
so each one is clicked once, on a fresh copy of the screen, and what it did is recorded: it went to
another page (``g``: page, record, tab), opened a drawer, dialog or menu (``o``: its markup, explored
the same way), closed one (``c``), or nothing the preview can show. Generic: it reads only the kit's
own model (``S.M``) and its location hooks (``ZAS_LOCATION`` / ``ZAS_GOTO``), never a template.
"""

from __future__ import annotations

import json
import sys


# One function in the page: everything is synchronous there (the kit renders on click).
CAPTURE_JS = r"""(opts) => {
  const MAX_CLICKS = opts.maxClicks || 30000, MAX_DEPTH = 2;
  const $ = s => document.querySelector(s);
  const M = S.M;
  if (!M) return { ok: false, error: 'The kit did not read the spec.' };
  const clone = x => { try { return structuredClone(x); } catch (e) { return JSON.parse(JSON.stringify(x)); } };
  const SNAP = clone({ db: S.db, audit: S.audit, seq: S.seq, users: S.users, me: S.me, views: S.views });
  const norm = h => String(h || '').replace(/ data-a="\d+"/g, '').replace(/\s+/g, ' ');
  const kinds = {
    drawer: () => [...document.querySelectorAll('#zapp > .z-dw-bg, #zapp > .z-dw')],
    modal: () => [...$('#modalRoot').children],
    pop: () => [...$('#popRoot').children],
  };
  const ovHtml = k => kinds[k]().map(n => n.outerHTML).join('');
  const scopeEls = scope => {
    const sel = '[data-a],[data-go]';
    if (scope === 'main') return [...document.querySelectorAll('#zapp .z-main ' + sel.replace(',', ',#zapp .z-main '))];
    if (scope === 'side') return [...document.querySelectorAll('#zapp .z-side ' + sel.replace(',', ',#zapp .z-side '))];
    const out = [];
    kinds[scope]().forEach(n => { if (n.matches(sel)) out.push(n); out.push(...n.querySelectorAll(sel)); });
    return out;
  };
  // A table's rows after the first do what the first row does (the 360 a row opens is drawn for one
  // sample record): such an element takes the key of its counterpart in the first row.
  const pathIn = (root, el) => { const out = []; for (let n = el; n && n !== root; n = n.parentElement) out.unshift([...n.parentElement.children].indexOf(n)); return out.join('/'); };
  function canon(els) {
    const at = new Map(els.map((el, i) => [el, i]));
    return els.map((el, i) => {
      const tr = el.closest('tbody > tr'); if (!tr) return i;
      const first = tr.parentElement.firstElementChild; if (!first || first === tr) return i;
      let twin = first; for (const k of pathIn(tr, el).split('/').filter(Boolean)) { twin = twin && twin.children[+k]; }
      return twin && at.has(twin) ? at.get(twin) : i;
    });
  }
  const state = () => ({ loc: ZAS_LOCATION() || {}, drawer: norm(ovHtml('drawer')), modal: norm(ovHtml('modal')), pop: norm(ovHtml('pop')) });
  let clicks = 0;
  const seen = {};   // normalised main markup → index in views (a view several roles share is explored once)
  function reset(loc) {
    Object.assign(S, clone(SNAP));
    try { closeModal(); } catch (e) {}
    try { closePop(); } catch (e) {}
    const t = $('#toasts'); if (t) t.innerHTML = '';
    S.ui = { tables: {}, drawer: null };
    ZAS_GOTO(loc);
  }
  // Put the page where `path` leads: the view, then each click in turn.
  function replay(loc, path) {
    reset(loc);
    for (const step of path) {
      const el = scopeEls(step.scope)[step.i];
      if (!el) return false;
      el.click(); clicks++;
    }
    return true;
  }
  const sameLoc = (a, b) => (a.page || null) === (b.page || null) && String((a.record || {}).id ?? '') === String((b.record || {}).id ?? '') && ((a.tab || {}).code || '') === ((b.tab || {}).code || '');
  // Mark every element of `scope` with its key, and return the scope's markup.
  function annotate(scope, prefix) {
    const els = scopeEls(scope), c = canon(els);
    els.forEach((el, i) => el.setAttribute('data-kk', prefix + c[i]));
  }
  function explore(loc, path, scope, prefix, depth, overlays) {
    if (!replay(loc, path)) return {};
    const first = scopeEls(scope), n = first.length, c = canon(first), acts = {};
    for (let i = 0; i < n && clicks < MAX_CLICKS; i++) {
      if (c[i] !== i) continue;
      if (!replay(loc, path)) break;
      const el = scopeEls(scope)[i]; if (!el || el.disabled) continue;
      const before = state();
      el.click(); clicks++;
      const after = state(), act = {};
      if (!sameLoc(before.loc, after.loc) && after.loc.page) {
        act.g = [after.loc.page, after.loc.record ? String(after.loc.record.id) : null, after.loc.tab ? after.loc.tab.code : null];
      }
      for (const k of ['pop', 'modal', 'drawer']) {
        if (before[k] && !after[k]) (act.c = act.c || []).push(k);
        else if (after[k] && !before[k] && !act.g) {   // a re-render of one already open (a form's own state) is not an action
          let html = '';
          if (depth < MAX_DEPTH) {
            const sub = explore(loc, path.concat([{ scope, i }]), k, prefix + i + '.', depth + 1, overlays);
            if (replay(loc, path.concat([{ scope, i }]))) { annotate(k, prefix + i + '.'); html = ovHtml(k); }
            Object.assign(acts, sub);
          } else {
            html = ovHtml(k);
          }
          overlays.push({ kind: k, html });
          (act.o = act.o || []).push([k, overlays.length - 1]);
        }
      }
      if (act.g || act.c || act.o) acts[prefix + i] = act;
    }
    return acts;
  }
  function capture(loc, scope, prefix) {
    const overlays = [];
    const acts = explore(loc, [], scope, prefix, 0, overlays);
    reset(loc); annotate(scope, prefix);
    const host = scope === 'side' ? $('#zapp .z-side') : $('#zapp .z-main');
    return { html: scope === 'side' ? host.outerHTML : host.innerHTML, acts, overlays };
  }

  const roles = M.roles.map(r => r.name);
  const pages = Object.values(M.pages).map(p => ({ code: p.code, title: p.title || p.code, type: p.type, detail_view: p.detail_view || null }));
  const out = { ok: true, roles: [], pages, views: [], sides: {} };
  for (const role of roles) {
    reset({ role });
    const landing = (ZAS_LOCATION() || {}).page || null;
    out.sides[role] = opts.outline ? { html: '', acts: {}, overlays: [] } : capture({ role, page: landing }, 'side', 's');
    // The landing page's own menu item goes nowhere from there: read the menu once more from
    // another page, so every item knows where it goes.
    const other = pages.find(p => p.code !== landing && p.type !== 'detail' && canPage(M.pages[p.code], role));
    if (other && !opts.outline) {
      const again = explore({ role, page: other.code }, [], 'side', 's', 0, out.sides[role].overlays);
      for (const k of Object.keys(again)) if (!out.sides[role].acts[k]) out.sides[role].acts[k] = again[k];
    }
    const open = [];
    for (const p of pages) {
      if (!canPage(M.pages[p.code], role)) continue;
      const loc = { role, page: p.code };
      let tabs = [null];
      if (p.type === 'detail') {
        const dv = M.dvs[p.detail_view]; const E = dv && M.ents[dv.hero];
        const row = E && visibleRows(E, role)[0];
        if (!row) { open.push({ page: p.code, error: 'no record this role can open' }); continue; }
        loc.record = { id: row.id };
        tabs = [null];
        for (const t of (dv.tabs || [])) {
          if (!t || !t.code) continue;
          reset({ ...loc, tab: { code: t.code } });
          const at = (ZAS_LOCATION() || {}).tab;
          if (at && at.code === t.code) tabs.push(t.code);
        }
      }
      reset(loc);
      if ((ZAS_LOCATION() || {}).page !== p.code) { open.push({ page: p.code, error: 'did not open' }); continue; }
      const entry = { page: p.code, record: loc.record ? String(loc.record.id) : null, views: {} };
      for (const tab of tabs) {
        const at = tab ? { ...loc, tab: { code: tab } } : loc;
        reset(at);
        const key = norm($('#zapp .z-main').innerHTML);
        if (!(key in seen)) {
          seen[key] = out.views.length;
          out.views.push(opts.outline ? { html: '', acts: {}, overlays: [] } : capture(at, 'main', ''));
        }
        entry.views[tab || ''] = seen[key];
      }
      open.push(entry);
    }
    const r = M.role[role] || {};
    out.roles.push({ name: role, landing, pages: open, description: r.description || '' });
  }
  out.clicks = clicks;
  out.app = { name: (M.app && M.app.name) || '', radius: document.documentElement.dataset.zasRadius || '', density: document.documentElement.dataset.zasDensity || '' };
  // Every custom property the kit declares, as the page resolved it (the spec's theme included).
  const cs = getComputedStyle(document.documentElement);
  out.vars = {};
  (opts.varNames || []).forEach(n => { const v = cs.getPropertyValue(n).trim(); if (v) out.vars[n] = v; });
  return out;
}"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    req = json.loads(sys.stdin.read())
    html = req["html"].replace("</body>", f"<script>{req['adapter']}</script></body>")
    blocked: list = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={"width": int(req.get("width") or 1440), "height": 900}
        )

        def route(r):
            url = r.request.url
            if not url.startswith("http") or url.startswith(
                tuple(req.get("hosts") or ())
            ):
                r.continue_()
            else:
                blocked.append(url[:200])
                r.abort()

        page.route("**/*", route)
        errors: list = []
        page.on("pageerror", lambda e: errors.append(str(e)[:300]))
        page.set_content(html, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_function("typeof window.zangoLoad === 'function'", timeout=30000)
        err = page.evaluate(
            "y => { window.zangoLoad(y); return S.parseErr ? String(S.parseErr.message || S.parseErr) : null }",
            req["yaml"],
        )
        if err:
            browser.close()
            print(
                json.dumps(
                    {"ok": False, "error": f"The kit could not read the spec: {err}"}
                )
            )
            return 1
        try:
            page.evaluate("document.fonts && document.fonts.ready")
        except Exception:  # noqa: BLE001 - fonts are cosmetic here
            pass
        result = page.evaluate(
            CAPTURE_JS,
            {
                "maxClicks": req.get("max_clicks") or 30000,
                "outline": bool(req.get("outline")),
                "varNames": req.get("var_names") or [],
            },
        )
        browser.close()
    result["page_errors"] = errors[:20]
    print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
