"""Render an uploaded HTML reference and measure its look (SpecWorkbench.ref_look's browser half).

Run as a script, so a stuck Chromium can be killed and the ORM is never touched::

    stdin   {"html": <page>, "steps": [{"go": "#/app/referrals"} | {"click": "Send code"} |
             {"fill": "Work email", "value": "a@b.c"} | {"wait": 500}], "width": 1440, "height": 900,
             "full": false}
    stdout  one JSON line: {"ok": true, "png": <base64>, "url": ..., "title": ..., "styles": {...},
             "tables": [...], "clickable": [...], "routes": [...], "step_errors": [...]}
             or {"ok": false, "error": ...}

Generic: it reads computed styles of whatever the page draws (body, sidebar, headings, tables,
buttons, cards, pills, tabs, inputs), never a particular mockup's classes.
"""

from __future__ import annotations

import base64
import json
import re
import sys


# Hosts a reference may load its look from; everything else stays offline.
FONT_HOSTS = ("https://fonts.googleapis.com/", "https://fonts.gstatic.com/")

MEASURE_JS = r"""() => {
  const H = innerHeight;
  const vis = el => {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'
      && +cs.opacity > 0.05 && r.bottom > 0 && r.top < H * 1.5;
  };
  const hex = c => {
    const m = String(c).match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/);
    if (!m) return c;
    const a = m[4] === undefined ? 1 : +m[4];
    if (a === 0) return 'transparent';
    const h = '#' + [m[1], m[2], m[3]].map(x => (+x).toString(16).padStart(2, '0')).join('').toUpperCase();
    return a < 1 ? h + Math.round(a * 255).toString(16).padStart(2, '0').toUpperCase() : h;
  };
  const SKIP = new Set(['none', 'normal', 'auto', '0px', 'transparent', 'rgba(0, 0, 0, 0)', 'start', 'static']);
  const PROPS = ['background-color', 'background-image', 'color', 'font-family', 'font-size', 'font-weight',
    'letter-spacing', 'text-transform', 'line-height', 'border-radius', 'box-shadow', 'padding',
    'border-top', 'border-right', 'border-bottom', 'border-left', 'height', 'width', 'gap'];
  const fix = v => String(v).replace(/rgba?\([^)]*\)/g, hex);
  const style = (el, props) => {
    const cs = getComputedStyle(el), o = {};
    for (const p of props || PROPS) {
      let v = cs.getPropertyValue(p);
      if (!v || SKIP.has(v)) continue;
      if (/^border-(top|right|bottom|left)$/.test(p) && /^0px/.test(v)) continue;
      if (p === 'background-image' && v === 'none') continue;
      if ((p === 'width' || p === 'height') && !(props || []).includes(p)) continue;
      if (p === 'font-family') v = v.split(',')[0].replace(/["']/g, '').trim();
      o[p] = fix(v);
    }
    return o;
  };
  const first = (sels, test) => {
    for (const s of sels) {
      let els = []; try { els = [...document.querySelectorAll(s)]; } catch (e) {}
      const el = els.find(e => vis(e) && (!test || test(e)));
      if (el) return el;
    }
    return null;
  };
  const text = el => (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40);
  const out = {};
  const put = (name, el, props) => { if (el) out[name] = Object.assign(style(el, props), text(el) ? { _text: text(el) } : {}); };

  put('page', document.body, ['background-color', 'color', 'font-family', 'font-size', 'line-height']);
  const side = first(['aside', '[data-sidebar="sidebar"]', '[class*="sidebar" i]', 'nav'], e => e.getBoundingClientRect().height > H * 0.5 && e.getBoundingClientRect().width < 400);
  if (side) {
    out.sidebar = style(side, ['background-color', 'background-image', 'color', 'width', 'border-right', 'box-shadow', 'padding']);
    const items = [...side.querySelectorAll('a,button,[role=menuitem],li')].filter(e => vis(e) && text(e) && e.getBoundingClientRect().height < 56);
    const active = items.find(e => e.matches('[aria-current],[data-active="true"],[aria-selected="true"],.active,.is-active,[data-state="active"]'));
    const plain = items.find(e => e !== active && !e.contains(active || null));
    put('sidebar_item', plain, ['background-color', 'color', 'font-size', 'font-weight', 'border-radius', 'padding', 'height']);
    put('sidebar_item_active', active, ['background-color', 'color', 'font-size', 'font-weight', 'border-radius', 'box-shadow', 'border-left']);
  }
  put('topbar', first(['header', '[role=banner]'], e => e.getBoundingClientRect().width > 500), ['background-color', 'border-bottom', 'box-shadow', 'height', 'padding']);
  put('h1', first(['main h1', 'h1']), ['color', 'font-family', 'font-size', 'font-weight', 'letter-spacing', 'line-height']);
  put('h2', first(['main h2', 'h2', 'main h3', 'h3']), ['color', 'font-size', 'font-weight', 'letter-spacing', 'text-transform']);
  put('table', first(['table']), ['background-color', 'border-radius', 'box-shadow', 'border-top', 'border-bottom']);
  put('table_header', first(['thead th', 'th']), ['background-color', 'color', 'font-size', 'font-weight', 'letter-spacing', 'text-transform', 'padding', 'border-bottom', 'height']);
  put('table_cell', first(['tbody td', 'td']), ['color', 'font-size', 'font-weight', 'padding', 'border-bottom', 'height']);
  const row = first(['tbody tr']); if (row) out.table_row = style(row, ['height', 'background-color', 'border-bottom']);
  put('input', first(['input[type=search]', 'input[type=text]', 'input:not([type])', 'select']), ['background-color', 'color', 'font-size', 'border-top', 'border-radius', 'height', 'padding', 'box-shadow']);
  const tab = first(['[role=tab]']);
  put('tab', tab, ['color', 'font-size', 'font-weight', 'padding', 'border-bottom', 'background-color', 'border-radius']);
  put('tab_active', first(['[role=tab][aria-selected="true"]', '[role=tab][data-state="active"]']), ['color', 'font-weight', 'border-bottom', 'background-color', 'border-radius', 'box-shadow']);

  // Buttons: the filled ones (primary) and the outlined ones (secondary).
  const buttons = [...document.querySelectorAll('button,a[role=button],[class*="btn" i]')].filter(e => vis(e) && text(e) && e.getBoundingClientRect().height < 60);
  const filled = b => { const c = getComputedStyle(b).backgroundColor; const m = c.match(/[\d.]+/g) || []; return m.length >= 3 && (m[3] === undefined || +m[3] > 0.5) && Math.max(+m[0], +m[1], +m[2]) - Math.min(+m[0], +m[1], +m[2]) > 40; };
  const btnProps = ['background-color', 'background-image', 'color', 'font-size', 'font-weight', 'border-radius', 'border-top', 'box-shadow', 'height', 'padding'];
  put('button_primary', buttons.find(filled), btnProps);
  put('button_secondary', buttons.find(b => !filled(b) && /^\d/.test(getComputedStyle(b).borderTopWidth) && getComputedStyle(b).borderTopWidth !== '0px'), btnProps);

  // Cards and pills: the most common distinct looks, by area.
  const groups = (test, props, n) => {
    const seen = new Map();
    for (const el of document.querySelectorAll('body *')) {
      if (!vis(el) || !test(el)) continue;
      const s = style(el, props), key = JSON.stringify(s);
      const r = el.getBoundingClientRect();
      const g = seen.get(key) || { style: s, count: 0, size: Math.round(r.width) + 'x' + Math.round(r.height), example: text(el) };
      g.count++; seen.set(key, g);
    }
    return [...seen.values()].sort((a, b) => b.count - a.count).slice(0, n)
      .map(g => Object.assign(g.style, { _count: g.count, _size: g.size }, g.example ? { _text: g.example } : {}));
  };
  out.cards = groups(el => {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    return r.width > 160 && r.height > 56 && parseFloat(cs.borderTopLeftRadius) >= 6
      && (cs.boxShadow !== 'none' || parseFloat(cs.borderTopWidth) > 0) && el.tagName !== 'BUTTON' && el.tagName !== 'INPUT';
  }, ['background-color', 'background-image', 'border-radius', 'box-shadow', 'border-top', 'padding'], 4);
  out.pills = groups(el => {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    const bg = cs.backgroundColor, t = text(el);
    return r.height >= 14 && r.height <= 30 && r.width < 220 && t && t.length < 28 && !/^[A-Z]{1,3}$/.test(t)
      && parseFloat(cs.borderTopLeftRadius) >= 4 && bg !== 'rgba(0, 0, 0, 0)' && el.tagName !== 'BUTTON'
      && ![...el.children].some(k => getComputedStyle(k).backgroundColor !== 'rgba(0, 0, 0, 0)' && text(k) === t);
  }, ['background-color', 'color', 'font-size', 'font-weight', 'border-top', 'padding', 'text-transform', 'letter-spacing'], 6);
  out.avatars = groups(el => {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    return r.width >= 20 && r.width <= 96 && Math.abs(r.width - r.height) < 2 && parseFloat(cs.borderTopLeftRadius) >= 4
      && cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && /^[A-Z]{1,3}$/.test(text(el));
  }, ['background-color', 'color', 'font-size', 'font-weight', 'border-radius', 'width'], 3);

  // Palette: colours by painted area (backgrounds) and by text length (text).
  const bg = new Map(), fg = new Map();
  for (const el of document.querySelectorAll('body *')) {
    if (!vis(el)) continue;
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    const b = hex(cs.backgroundColor);
    if (b !== 'transparent') bg.set(b, (bg.get(b) || 0) + r.width * r.height);
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('');
    if (own) { const c = hex(cs.color); fg.set(c, (fg.get(c) || 0) + own.length); }
  }
  const top = (m, n) => [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n).map(e => e[0]);
  out.palette = { backgrounds: top(bg, 10), text: top(fg, 8) };
  out.fonts = [...new Set([...document.querySelectorAll('body *')].slice(0, 3000).map(e => getComputedStyle(e).fontFamily.split(',')[0].replace(/["']/g, '').trim()))].slice(0, 5);

  // Tables: the header, and how the first row's cells are built (lines, avatar, pill).
  const tables = [...document.querySelectorAll('table')].filter(vis).slice(0, 2).map(t => {
    const heads = [...t.querySelectorAll('thead th')].map(text);
    const tr = t.querySelector('tbody tr');
    const cells = tr ? [...tr.children].map((td, i) => {
      const lines = [];
      const walk = n => {
        for (const c of n.children) {
          const d = getComputedStyle(c).display;
          if ((d === 'block' || d === 'flex' || d === 'grid') && c.children.length && !c.querySelector('img,svg') && c.innerText.trim() && [...c.children].some(k => ['block','flex','grid'].includes(getComputedStyle(k).display))) walk(c);
          else if ((d === 'block' || d === 'flex' || d === 'grid') && text(c)) lines.push(text(c));
        }
      };
      walk(td);
      const av = [...td.querySelectorAll('*')].find(e => { const r = e.getBoundingClientRect(); return r.width >= 18 && r.width <= 48 && Math.abs(r.width - r.height) < 2 && /^[A-Z]{1,3}$/.test(text(e)); });
      const pills = [...td.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return r.height <= 28 && r.height >= 14 && parseFloat(cs.borderTopLeftRadius) >= 4 && cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && text(e) && !/^[A-Z]{1,3}$/.test(text(e)); }).map(text);
      const progress = [...td.querySelectorAll('*')].some(e => { const r = e.getBoundingClientRect(); return r.height > 0 && r.height <= 6 && r.width >= 8 && getComputedStyle(e).backgroundColor !== 'rgba(0, 0, 0, 0)'; });
      return { column: heads[i] || '', lines: (lines.length ? lines : [text(td)]).filter(l => !av || l !== text(av)), avatar: av ? text(av) : '', pills: [...new Set(pills)].slice(0, 3), progress_bar: progress, chevron: !text(td) && !!td.querySelector('svg') };
    }) : [];
    return { columns: heads, rows: t.querySelectorAll('tbody tr').length, first_row: cells };
  });

  const clickable = [...new Set([...document.querySelectorAll('a,button,[role=tab],[role=menuitem],[onclick],[data-href]')]
    .filter(vis).map(text).filter(t => t && t.length < 32))].slice(0, 60);
  return { styles: out, tables, clickable };
}"""

CLICK_JS = r"""(t) => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const want = norm(t);
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const els = [...document.querySelectorAll('a,button,[role=button],[role=tab],[role=menuitem],[onclick],tr,li,summary,label')].filter(vis);
  const el = els.find(e => norm(e.innerText) === want) || els.find(e => norm(e.innerText).startsWith(want))
    || els.find(e => norm(e.innerText).includes(want));
  if (!el) return false;
  el.click();
  return true;
}"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    req = json.loads(sys.stdin.read())
    html = req["html"]
    routes = sorted(set(re.findall(r"""["'](#/[A-Za-z0-9_/\-]{2,60})["']""", html)))[
        :40
    ]
    step_errors: list = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={
                "width": int(req.get("width") or 1440),
                "height": int(req.get("height") or 900),
            }
        )

        def route(r):
            url = r.request.url
            if not url.startswith("http") or url.startswith(FONT_HOSTS):
                r.continue_()
            else:
                r.abort()

        page.route("**/*", route)
        errors: list = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        # A real origin, so the page's own router and storage work as in a browser.
        page.route(
            "http://reference.local/",
            lambda r: r.fulfill(status=200, content_type="text/html", body=html),
        )
        page.goto("http://reference.local/", wait_until="load", timeout=60000)
        page.wait_for_timeout(600)
        for step in req.get("steps") or []:
            try:
                if "go" in step:
                    target = str(step["go"])
                    if target.startswith("#"):
                        page.evaluate("h => { location.hash = h }", target)
                    else:
                        page.goto(
                            "http://reference.local/" + target.lstrip("/"),
                            wait_until="load",
                        )
                elif "click" in step:
                    if not page.evaluate(CLICK_JS, str(step["click"])):
                        step_errors.append(f"nothing to click named {step['click']!r}")
                elif "fill" in step:
                    loc = page.get_by_label(str(step["fill"]))
                    if not loc.count():
                        loc = page.get_by_placeholder(str(step["fill"]))
                    loc.first.fill(str(step.get("value", "")))
                elif "wait" in step:
                    page.wait_for_timeout(min(int(step["wait"]), 3000))
                page.wait_for_timeout(350)
            except Exception as exc:  # noqa: BLE001 - reported, the look still goes back
                step_errors.append(f"{json.dumps(step)}: {str(exc)[:160]}")
        try:
            page.evaluate("document.fonts && document.fonts.ready")
        except Exception:  # noqa: BLE001 - fonts are cosmetic here
            pass
        measured = page.evaluate(MEASURE_JS)
        png = page.screenshot(full_page=bool(req.get("full")), type="png")
        result = {
            "ok": True,
            "png": base64.b64encode(png).decode("ascii"),
            "url": page.url.replace("http://reference.local/", "/"),
            "title": page.title(),
            "routes": routes,
            "step_errors": step_errors,
            "page_errors": errors[:5],
            **measured,
        }
        browser.close()
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
