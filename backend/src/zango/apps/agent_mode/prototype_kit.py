"""A template's starting prototype, drawn from its spec by the kit preview (template mode, T0).

Template requirements open in Free design (``preview_mode == "open"``) on the template's own
preview, before anyone has written a prototype. ``open_from_kit`` makes that first prototype when a
pack is published: the kit (the generic template's preview page) renders the starter, and every
screen it draws becomes a real part the analyst can edit like any other:

    manifest.json        one screen per page, with the roles that open it and ``maps`` to its page
    tokens.css           the kit's custom properties as resolved for this spec, plus canonical names
    app.css              the kit's stylesheet
    shell.js             the sidebar per role, and the small helper (``KIT``) the screens run on
    screens/<page>.js    the page as each role sees it (per 360 tab), with its drawers and dialogs

Every action on a kit screen is a closure, so the browser half (``kit_capture_worker.py``) clicks
each one and records what it did: go to a page, open or close a drawer, dialog or menu. The
prototype replays those; anything else (typing, sorting, saving) does nothing in it.

Generic: nothing here, nor in the worker, knows any one template. ``open_spec`` adds what the YAML
needs to go with it (``app.design`` and ``prototype.screens``), so Commit's coverage gate holds.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

from pathlib import Path

from .prototype import FONT_HOST, LIBRARY_HOSTS, runtime_css


WORKER = Path(__file__).resolve().parent / "kit_capture_worker.py"
CAPTURE_TIMEOUT = 600
WIDTH = 1440
KIT_SOURCE = "kit"

# The kit's custom properties under the canonical design-token names the build maps
# (prototype.DESIGN_TOKENS). They point at the kit's own, so editing either moves the look.
# What the kit page draws the app area with (app-studio.html's .z-* / .d-* rules use these greys
# directly). The page's :root variables of the same names belong to the Studio around it, not to the
# app, so a kit prototype's tokens.css (and so app.design) carries these instead. They are also the zas
# runtime's defaults: a stock template builds with the greys its preview shows.
KIT_APP_LOOK = {
    "page": "#F7F8FA",
    "card": "#FFFFFF",
    "sunk": "#F2F4F7",
    "text-strong": "#101828",
    "text": "#101828",
    "text-2": "#475467",
    "text-3": "#667085",
    "text-faint": "#98A2B3",
    "border-faint": "#F2F4F7",
    "border": "#EAECF0",
    "border-strong": "#D0D5DD",
}

CANONICAL = {
    "page": "page",
    "card": "card",
    "sunk": "sunken",
    "text-strong": "strong",
    "text": "text",
    "text-2": "sub",
    "text-3": "muted",
    "text-faint": "faint",
    "border-faint": "bdf",
    "border": "bd",
    "border-strong": "bds",
}

# The page scrolls instead of the kit's content pane, so a screen captures at its full height;
# the sidebar stays put. A wrapper the runtime adds must not break the kit's flex layout.
HOST_CSS = """
/* ---- prototype host (open_from_kit): the page scrolls, the sidebar stays put ---- */
#zas-app{min-height:100vh}
.zapp{height:auto;min-height:100vh;overflow:visible}
.z-shell{height:auto;min-height:100vh;align-items:flex-start}
.z-side{position:sticky;top:0;height:100vh;align-self:flex-start}
.z-content{overflow:visible}
.z-main>[data-zas-screen],#kit-dw{display:contents}
"""

SHELL_JS = r"""/* The shell: each role's sidebar, as the kit drew it, and the helper the screens run on.
   KIT.screen(id, {pick, views}) registers a screen: pick[role][tab] is the view a role sees on a
   tab ('' when none); each view is {html, acts, ovs}. An element with data-act="kit" data-k="<key>"
   runs acts[<key>]: c = close (pop | modal | drawer), o = open [[kind, index into ovs]],
   g = go [screen, record, tab]. Keys starting with "s" are the sidebar's. */
(function () {
  var de = document.documentElement;
  de.dataset.zasRadius = __RADIUS__;
  de.dataset.zasDensity = __DENSITY__;
  var SIDES = __SIDES__;
  var KIT = window.KIT = { cur: null, side: null, sides: SIDES };
  var roots = {};
  function host(kind) {
    if (kind === 'drawer') return document.getElementById('kit-dw');
    if (!roots[kind] || !roots[kind].isConnected) {
      roots[kind] = document.createElement('div');
      roots[kind].id = kind === 'modal' ? 'modalRoot' : 'popRoot';
      document.body.appendChild(roots[kind]);
    }
    return roots[kind];
  }
  function close(kind) { var el = host(kind); if (el) el.innerHTML = ''; }
  function open(kind, html) {
    var el = host(kind); if (!el) return;
    el.innerHTML = html;
    if (window.lucide && lucide.createIcons) { try { lucide.createIcons(); } catch (e) {} }
  }
  KIT.screen = function (id, data) {
    ZAS.screen(id, {
      render: function (c) {
        var pick = data.pick[c.role] || data.pick[Object.keys(data.pick)[0]] || {};
        var tab = (c.params && c.params.tab) || '';
        var i = Object.prototype.hasOwnProperty.call(pick, tab) ? pick[tab] : pick[''];
        KIT.cur = data.views[i == null ? 0 : i];
        return KIT.cur ? KIT.cur.html : '';
      }
    });
  };
  ZAS.on('kit', function (d, el, ev) {
    if (el && el.closest && el.closest('.z-main')) KIT.lastOpener = el;
    var k = String(d.k || ''), t = k.charAt(0) === 's' ? KIT.side : KIT.cur, a = t && t.acts[k];
    if (!a) return;
    if (ev && ev.preventDefault) ev.preventDefault();
    (a.c || []).forEach(close);
    (a.o || []).forEach(function (o) { open(o[0], t.ovs[o[1]] || ''); });
    if (a.g) ZAS.go(a.g[0], { record: a.g[1], params: a.g[2] ? { tab: a.g[2] } : {} });
  });
  /* Forms in a dialog or drawer work on what the kit drew: choice pills toggle, Autofill fills the
     empty fields, Create closes the form and adds the record to the table behind it. */
  function toast(msg) {
    var t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = 'position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:#101828;color:#fff;padding:10px 16px;border-radius:8px;font-size:13px;z-index:99999';
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 2200);
  }
  function value(f) {
    var inp = f.querySelector('input,textarea,select');
    if (inp && inp.tagName === 'SELECT') return inp.selectedIndex > 0 ? inp.options[inp.selectedIndex].text : '';
    if (inp && inp.type !== 'checkbox') return inp.value.trim();
    return Array.prototype.map.call(f.querySelectorAll('.z-pill.on'), function (b) { return b.textContent.trim(); }).join(', ');
  }
  function formOf(el) { return el.closest('.mo, [role=dialog]'); }
  document.addEventListener('click', function (ev) {
    var el = ev.target.closest && ev.target.closest('button');
    if (!el || el.hasAttribute('data-act') || el.hasAttribute('data-a')) return;
    var form = formOf(el);
    if (!form) return;
    if (el.classList.contains('z-pill')) {
      var group = el.parentNode, was = el.classList.contains('on');
      Array.prototype.forEach.call(group.children, function (b) { b.classList.remove('on'); });
      el.classList.toggle('on', !was);
      return;
    }
    var label = el.textContent.trim();
    if (/^autofill$/i.test(label)) {
      form.querySelectorAll('.fld').forEach(function (f) {
        if (value(f)) return;
        var inp = f.querySelector('input,textarea,select'), pills = f.querySelectorAll('.z-pill');
        if (inp && inp.tagName === 'SELECT') { if (inp.options.length > 1) inp.selectedIndex = 1; }
        else if (inp && inp.type === 'number') inp.value = '100';
        else if (inp && inp.type === 'date') inp.value = '2027-01-15';
        else if (inp && inp.type !== 'checkbox' && inp.type !== 'file') inp.value = 'Sample ' + ((f.querySelector('label') || {}).textContent || 'text').replace('*', '').trim().toLowerCase();
        else if (pills.length) pills[0].classList.add('on');
      });
      return;
    }
    if (el.classList.contains('pri') && form.querySelector('.mo-f')) {
      var vals = {};
      form.querySelectorAll('.fld').forEach(function (f) {
        var l = ((f.querySelector('label') || {}).textContent || '').replace('*', '').trim().toLowerCase();
        if (l) vals[l] = value(f);
      });
      var missing = Array.prototype.filter.call(form.querySelectorAll('.fld'), function (f) { return f.querySelector('.rq') && !value(f); });
      if (missing.length) { missing[0].scrollIntoView({ block: 'center' }); toast('Fill the required fields first'); return; }
      var flow = form.querySelectorAll('.flow .z-badge');
      if (flow.length === 2) {   // a status change: the page's badge moves from the first status to the second
        var from = flow[0].textContent.trim();
        document.querySelectorAll('.z-main .z-badge').forEach(function (b) {
          if (b.textContent.trim() === from) { b.setAttribute('style', flow[1].getAttribute('style') || ''); b.innerHTML = flow[1].innerHTML; }
        });
        var opener = KIT.lastOpener;
        if (opener && opener.isConnected) opener.style.display = 'none';
        close('modal'); close('drawer');
        toast('Status changed to ' + flow[1].textContent.trim() + '. This is the prototype, nothing is stored.');
        return;
      }
      var table = document.querySelector('.z-main table tbody');
      var first = table && table.querySelector('tr');
      if (first) {
        var heads = Array.prototype.map.call(document.querySelectorAll('.z-main table thead th'), function (h) { return h.textContent.trim().toLowerCase(); });
        var row = first.cloneNode(true);
        Array.prototype.forEach.call(row.children, function (td, i) {
          var v = vals[heads[i]];
          if (v === undefined) { var k = Object.keys(vals).filter(function (n) { return heads[i] && (n.indexOf(heads[i]) >= 0 || heads[i].indexOf(n) >= 0); })[0]; v = k ? vals[k] : undefined; }
          if (v) { var w = document.createTreeWalker(td, NodeFilter.SHOW_TEXT), n, done = false; while (!done && (n = w.nextNode())) { if (n.nodeValue.trim()) { n.nodeValue = v; done = true; } } }
        });
        table.insertBefore(row, first);
      }
      close('modal'); close('drawer');
      toast('Saved. This is the prototype, nothing is stored.');
    }
  });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { close('pop'); close('modal'); close('drawer'); } });
  document.addEventListener('click', function (ev) {
    if (ev.target.closest && !ev.target.closest('#popRoot, [data-act]')) close('pop');
  });
  ZAS.shell({
    render: function (c, body) {
      var s = SIDES[c.role] || SIDES[Object.keys(SIDES)[0]] || { html: '', acts: {}, ovs: [] };
      KIT.side = s;
      return '<div class="zapp"><div class="z-shell">' + s.html + '<div class="z-main">' + body +
        '</div></div><div id="kit-dw"></div></div>';
    },
    mount: function (root, c) {
      close('pop'); close('modal');
      var here = [c.screen, (c.meta && c.meta.parent) || ''];
      root.querySelectorAll('.z-side [data-nav]').forEach(function (el) {
        el.classList.toggle('on', here.indexOf(el.getAttribute('data-nav')) >= 0);
      });
    }
  });
})();
"""


class KitCaptureError(Exception):
    """The kit could not draw the spec (no browser, a spec it can't read, a timeout)."""


# ---------------------------------------------------------------------------
# The kit page
# ---------------------------------------------------------------------------


def kit_styles(html: str) -> str:
    """Every ``<style>`` in the kit page, in order."""
    return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))


def kit_fonts(html: str) -> list[str]:
    return [
        m
        for m in re.findall(r'<link[^>]+href="([^"]+)"', html)
        if m.startswith(FONT_HOST) and "css" in m
    ]


def kit_icons_url(html: str) -> str:
    """The icon library the kit inlines, when it says where from (so icon names match)."""
    m = re.search(r"inlined from (https://unpkg\.com/lucide@[\d.]+/\S+?\.js)", html)
    return m.group(1) if m and m.group(1).startswith(LIBRARY_HOSTS) else ""


def _root_blocks(css: str) -> list[tuple[int, int]]:
    """(start, end) of each top-level ``:root{…}`` rule."""
    out, depth, start = [], 0, 0
    sel_start = 0
    for i, ch in enumerate(css):
        if ch == "{":
            if depth == 0:
                start = i
                selector = re.sub(
                    r"/\*.*?\*/", "", css[sel_start:i], flags=re.S
                ).strip()
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                if selector == ":root":
                    out.append((sel_start, i + 1))
                sel_start = i + 1
            depth = max(depth, 0)
    return out


def split_root(css: str) -> tuple[list[str], str]:
    """(custom property names on ``:root``, the stylesheet without those rules)."""
    names, kept, last = [], [], 0
    for start, end in _root_blocks(css):
        block = css[start:end]
        names += re.findall(r"(--[a-zA-Z0-9_-]+)\s*:", block)
        kept.append(css[last:start])
        last = end
    kept.append(css[last:])
    return list(dict.fromkeys(names)), "".join(kept)


def runtime_resets(kit_css: str) -> str:
    """Undo what the runtime's base styles set on classes the kit styles itself (``.z-pill``…).

    The runtime's rules load first, so the kit's win wherever both set a property; the rest of the
    runtime's would leak into the kit's look. Those are put back to the browser's defaults."""
    out = []
    for selector, decls in re.findall(r"([^{}]+)\{([^{}]*)\}", runtime_css()):
        selector = selector.strip()
        if not re.fullmatch(r"\.[a-z][a-z0-9-]*", selector):
            continue
        if not re.search(re.escape(selector) + r"(?![a-z0-9-])", kit_css):
            continue
        props = [d.split(":", 1)[0].strip() for d in decls.split(";") if ":" in d]
        if props:
            out.append(selector + "{" + ";".join(f"{p}:revert" for p in props) + "}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Markup clean-up
# ---------------------------------------------------------------------------

_SVG_RE = re.compile(r"<svg\b([^>]*\bdata-lucide=\"([^\"]+)\"[^>]*)>.*?</svg>", re.S)
_KK_RE = re.compile(r' data-kk="([^"]*)"')


def _icon(m: re.Match) -> str:
    cls = re.search(r'\bclass="([^"]*)"', m.group(1))
    keep = [
        c
        for c in (cls.group(1).split() if cls else [])
        if c != "lucide" and not c.startswith("lucide-")
    ]
    attr = f' class="{" ".join(keep)}"' if keep else ""
    return f'<i data-lucide="{m.group(2)}"{attr}></i>'


def clean(html: str, acts: dict, nav: dict | None = None) -> str:
    """Kit markup as prototype markup: icons back to ``<i data-lucide>``, the kit's closures
    dropped, and each element with a recorded action wired to it (``data-act="kit"``)."""
    html = _SVG_RE.sub(_icon, html)
    html = re.sub(r' data-(?:a|in|go)="[^"]*"', "", html)

    def wire(m):
        key = m.group(1)
        if key not in acts:
            return ""
        extra = ""
        if nav is not None and acts[key].get("g"):
            extra = f' data-nav="{nav.get(acts[key]["g"][0], acts[key]["g"][0])}"'
        return f' data-act="kit" data-k="{key}"{extra}'

    return _KK_RE.sub(wire, html)


def screen_id(code: str) -> str:
    sid = re.sub(r"[^a-z0-9_.-]+", "_", str(code).lower()).strip("_.-")
    return sid or "screen"


def role_code(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_") or "role"


def _acts(raw: dict, ids: dict) -> dict:
    """The worker's actions with page codes as screen ids; actions to a page no screen is dropped."""
    out = {}
    for key, act in (raw or {}).items():
        a = {k: v for k, v in act.items() if k in ("c", "o")}
        if act.get("g") and act["g"][0] in ids:
            page, record, tab = act["g"]
            a["g"] = [ids[page], record, tab]
        if a:
            out[key] = a
    return out


def _view(raw: dict, ids: dict, nav: bool = False) -> dict:
    acts = _acts(raw.get("acts"), ids)
    mapping = {v: v for v in ids.values()} if nav else None
    return {
        "html": clean(raw.get("html") or "", acts, mapping),
        "acts": acts,
        "ovs": [clean(o.get("html") or "", acts) for o in raw.get("overlays") or []],
    }


def _js_template(text: str) -> str:
    return (
        "`" + text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${") + "`"
    )


def _view_js(view: dict, indent: str) -> str:
    ovs = (",\n" + indent + "    ").join(_js_template(o) for o in view["ovs"])
    return (
        indent
        + "{\n"
        + indent
        + "  acts: "
        + json.dumps(view["acts"], ensure_ascii=False, separators=(",", ":"))
        + ",\n"
        + indent
        + "  ovs: ["
        + (("\n" + indent + "    " + ovs + "\n" + indent + "  ") if view["ovs"] else "")
        + "],\n"
        + indent
        + "  html: "
        + _js_template(view["html"])
        + "\n"
        + indent
        + "}"
    )


# ---------------------------------------------------------------------------
# Capture → parts
# ---------------------------------------------------------------------------


def capture(
    spec_text: str, kit_html: str, adapter: str, var_names: list, outline: bool = False
) -> dict:
    """Run the browser half; the worker's JSON, or KitCaptureError."""
    import os
    import signal

    req = {
        "html": kit_html,
        "adapter": adapter,
        "yaml": spec_text,
        "width": WIDTH,
        "var_names": var_names,
        "outline": outline,
        "hosts": [*LIBRARY_HOSTS, FONT_HOST, "https://fonts.gstatic.com/"],
    }
    try:
        proc = subprocess.Popen(
            [sys.executable, str(WORKER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            start_new_session=True,  # killing its group takes Chromium too
        )
    except OSError as exc:
        raise KitCaptureError(f"Could not start the kit capture: {exc}") from exc
    try:
        stdout, stderr = proc.communicate(json.dumps(req), timeout=CAPTURE_TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise KitCaptureError(
            f"The kit capture took longer than {CAPTURE_TIMEOUT} s."
        ) from exc
    lines = [ln for ln in (stdout or "").splitlines() if ln.strip()]
    try:
        result = json.loads(lines[-1]) if lines else {}
    except ValueError:
        result = {}
    if not result.get("ok"):
        why = (
            result.get("error")
            or (stderr or "").strip().splitlines()[-1:]
            or ["no result"]
        )
        raise KitCaptureError(why if isinstance(why, str) else why[0])
    return result


def parts_from_capture(cap: dict, kit_html: str) -> dict:
    """The prototype parts for one capture (``kit_capture_worker`` output)."""
    css = kit_styles(kit_html)
    _, rest = split_root(css)
    pages = {p["code"]: p for p in cap.get("pages") or []}
    roles = cap.get("roles") or []
    codes = {r["name"]: role_code(r["name"]) for r in roles}
    opened: dict = {}  # page code → [(role, entry)]
    for r in roles:
        for entry in r.get("pages") or []:
            if not entry.get("error"):
                opened.setdefault(entry["page"], []).append((r["name"], entry))
    ids = {code: screen_id(code) for code in pages if code in opened}
    views = [_view(v, ids) for v in cap.get("views") or []]

    # A record screen's parent: the first screen whose actions go to it (the nav highlights it).
    parent: dict = {}
    for code in pages:
        for _, entry in opened.get(code, []):
            for vi in entry["views"].values():
                for act in views[vi]["acts"].values():
                    target = (act.get("g") or [None])[0]
                    if target and target != ids[code]:
                        parent.setdefault(target, ids[code])

    manifest_screens = []
    parts: dict = {}
    for code, page in pages.items():
        if code not in ids:
            continue
        sid = ids[code]
        entries = opened[code]
        screen = {
            "id": sid,
            "title": page.get("title") or code,
            "roles": [codes[name] for name, _ in entries],
            "maps": f"/pages/@{code}",
        }
        if page.get("type") == "detail":
            sample = next(
                (e.get("record") for _, e in entries if e.get("record")), None
            )
            screen["record"] = page.get("detail_view") or code
            if sample is not None:
                screen["sample"] = sample
            if sid in parent:
                screen["parent"] = parent[sid]
        manifest_screens.append(screen)

        used = sorted({vi for _, e in entries for vi in e["views"].values()})
        local = {vi: i for i, vi in enumerate(used)}
        pick = {
            codes[name]: {tab: local[vi] for tab, vi in e["views"].items()}
            for name, e in entries
        }
        body = ",\n".join(_view_js(views[vi], "    ") for vi in used)
        parts[f"screens/{sid}.js"] = (
            f"/* {page.get('title') or code}: drawn from the template's preview. "
            "pick: the view each role sees (per 360 tab). */\n"
            f"KIT.screen({json.dumps(sid)}, {{\n"
            f"  pick: {json.dumps(pick, ensure_ascii=False)},\n"
            f"  views: [\n{body}\n  ]\n}});\n"
        )

    sides = {}
    for r in roles:
        raw = (cap.get("sides") or {}).get(r["name"]) or {}
        sides[codes[r["name"]]] = _view(raw, ids, nav=True)
    app = cap.get("app") or {}
    parts["shell.js"] = (
        SHELL_JS.replace("__RADIUS__", json.dumps(app.get("radius") or "rounded"))
        .replace("__DENSITY__", json.dumps(app.get("density") or "comfortable"))
        .replace("__SIDES__", json.dumps(sides, ensure_ascii=False, indent=1))
    )

    resolved = cap.get("vars") or {}
    token_lines = [f"  {name}: {value};" for name, value in resolved.items()]
    canon = [
        f"  --{canon}: var(--{kit});"
        for canon, kit in CANONICAL.items()
        if f"--{kit}" in resolved and f"--{canon}" not in resolved
    ]
    if "--brand" in resolved:
        canon.append("  --brand-soft: var(--b50);")
    body_font = re.search(r"body\s*\{[^}]*font-family:\s*'?([A-Za-z0-9 ]+)'?", css)
    if body_font and "--font" not in resolved:
        canon.append(f"  --font: '{body_font.group(1).strip()}', sans-serif;")
    parts["tokens.css"] = (
        "/* The look: the kit's tokens for this app (theme included), then the canonical names the\n"
        "   build maps (app.design). Change a value here to change it everywhere. */\n:root {\n"
        + "\n".join(token_lines + canon)
        + "\n}\n"
    )
    parts["app.css"] = (
        "/* The kit's stylesheet (the template preview), and what the prototype host needs. */\n"
        + runtime_resets(css)
        + "\n"
        + rest.strip()
        + "\n"
        + HOST_CSS
    )

    first = roles[0]["name"] if roles else ""
    manifest = {
        "title": app.get("name") or "Prototype",
        "source": KIT_SOURCE,
        "roles": {codes[r["name"]]: r["name"] for r in roles},
        "default_role": codes.get(first, ""),
        "home": {
            codes[r["name"]]: ids[r["landing"]]
            for r in roles
            if r.get("landing") in ids
        },
        "fonts": kit_fonts(kit_html),
        "libraries": [u for u in [kit_icons_url(kit_html)] if u],
        "screens": manifest_screens,
    }
    parts["manifest.json"] = json.dumps(manifest, indent=2, ensure_ascii=False)
    return parts


# ---------------------------------------------------------------------------
# The kit page itself, as the prototype (an imported page)
# ---------------------------------------------------------------------------

SPEC_PART = "imported/script-zy-spec.js"
BRIDGE_PART = "imported/script-zz-bridge.js"
BRIDGE_CSS = """/* The kit page is a preview here: its YAML pane and studio header are not shown. */
.hd,.ed{display:none!important}
.body{grid-template-columns:1fr!important}
"""
BRIDGE_JS = r"""/* Starts the kit page on this app's spec and tells the preview where the user is.
   The kit draws everything from the YAML (imported/script-zy-spec.js): change the YAML and the
   pages, forms, filters and status changes change with it. The look goes in look.css (loaded after
   every other stylesheet), as rules on the kit's own classes (.d-head, .d-fact, .z-card, .z-t th…). */
(function () {
  var ROLES = __ROLES__;   // role code -> the spec's role name
  var CODES = {};
  Object.keys(ROLES).forEach(function (c) { CODES[ROLES[c]] = c; });
  function start() {
    S.M = null; S.route = null; S.role = null; S.builtFor = null;
    var src = document.getElementById('src'); if (src) src.value = window.ZAS_KIT_SPEC;
    parse(window.ZAS_KIT_SPEC);
    document.documentElement.classList.add('zango-loaded');
  }
  function where() { try { return window.ZAS_LOCATION ? window.ZAS_LOCATION() : null; } catch (e) { return null; } }
  var last = '';
  function report() {
    var l = where(); if (!l || !l.page) return;
    var k = JSON.stringify([l.role, l.page, l.record && l.record.id]);
    if (k === last) return; last = k;
    ZAS.at(l.page, { role: CODES[l.role] || l.role, record: l.record ? l.record.id : null });
  }
  ZAS.ready({
    go: function (screen, o) {
      o = o || {};
      var target = { role: ROLES[o.role] || ROLES[ZAS.state.role], page: screen };
      if (o.record != null && o.record !== '') target.record = { id: /^\d+$/.test(String(o.record)) ? Number(o.record) : o.record };
      if (o.params && o.params.tab) target.tab = { code: o.params.tab };
      if (window.ZAS_GOTO) window.ZAS_GOTO(target);
      last = ''; report();
    }
  });
  start();
  setInterval(report, 300);
  document.addEventListener('click', function () { setTimeout(report, 60); }, true);
})();
"""


def _spec_part(spec_text: str) -> str:
    return (
        "window.ZAS_KIT_SPEC = "
        + json.dumps(spec_text or "", ensure_ascii=False).replace("</", "<\\/")
        + ";\n"
    )


def _menu_pages(items) -> list[str]:
    out: list[str] = []
    for item in items or []:
        if not hasattr(item, "get"):
            continue
        if item.get("page"):
            out.append(str(item["page"]))
        out.extend(_menu_pages(item.get("items")))
    return out


def spec_screens(parts: dict, spec_text: str) -> dict:
    """``parts`` with a manifest screen for every page the spec has and the manifest lacks.

    The manifest is drawn when the template is published; a page the spec gains afterwards (a change
    request adds a 360, a list, a role) would have no screen: nothing to snapshot, compare or cover,
    while the lists that open it point at it. Only adds: a screen already there is as it was drawn.
    """
    from zango.apps.shared.app_templates.services.spec import yamlio

    from .prototype import manifest_of

    manifest, _ = manifest_of(parts)
    if not manifest.get("screens"):
        return parts
    try:
        doc = yamlio.load_rt(spec_text or "")
    except Exception:
        return parts
    if not hasattr(doc, "get"):
        return parts
    pages = [p for p in doc.get("pages") or [] if hasattr(p, "get") and p.get("code")]
    views = {
        str(v.get("code")): v
        for v in doc.get("detail_views") or []
        if hasattr(v, "get")
    }
    screens = list(manifest["screens"])
    have = {s["id"] for s in screens}
    role_names = {
        role_code(r.get("name")): str(r.get("name"))
        for r in doc.get("roles") or []
        if hasattr(r, "get") and r.get("name")
    }
    menus = {
        code: _menu_pages(r.get("menu"))
        for code, r in (
            (role_code(r.get("name")), r)
            for r in doc.get("roles") or []
            if hasattr(r, "get") and r.get("name")
        )
    }
    added = []
    for page in pages:
        code = str(page["code"])
        sid = screen_id(code)
        if sid in have:
            continue
        screen = {
            "id": sid,
            "title": str(page.get("title") or code.replace("_", " ").title()),
            "maps": f"/pages/@{code}",
        }
        if page.get("type") == "detail":
            view = views.get(str(page.get("detail_view") or code), {})
            wanted = {role_code(n) for n in view.get("roles") or []}
            screen["roles"] = [c for c in role_names if not wanted or c in wanted]
            screen["record"] = str(page.get("detail_view") or code)
            screen["sample"] = "1"
            hero = view.get("hero")
            parent = next(
                (
                    screen_id(str(p["code"]))
                    for p in pages
                    if p.get("type") == "crud"
                    and hero
                    and str(p.get("entity")) == str(hero)
                ),
                None,
            )
            if parent:
                screen["parent"] = parent
        else:
            screen["roles"] = [
                c for c in role_names if code in menus.get(c, [])
            ] or list(role_names)
        added.append(screen)
        have.add(sid)
    if not added:
        return parts
    return {
        **parts,
        "manifest.json": json.dumps(
            {**manifest, "screens": screens + added}, indent=2, ensure_ascii=False
        ),
    }


def with_spec(parts: dict, spec_text: str) -> dict:
    """``parts`` of a kit page with ``spec_text`` as the YAML it draws (anything else: as it is)."""
    if not is_kit_page(parts):
        return parts
    return spec_screens({**parts, SPEC_PART: _spec_part(spec_text)}, spec_text)


def is_kit_page(parts: dict) -> bool:
    """Whether ``parts`` are the kit page itself (draws whatever YAML it is given)."""
    return SPEC_PART in (parts or {})


def imported_parts(cap: dict, kit_html: str, spec_text: str) -> dict:
    """The kit page as an imported prototype: its own markup, styles and scripts, the spec, a bridge,
    and a manifest of the pages and roles from the outline ``cap`` (kit_capture_worker, outline)."""
    from .prototype import import_html

    parts, _ = import_html(kit_html)
    pages = {p["code"]: p for p in cap.get("pages") or []}
    roles = cap.get("roles") or []
    codes = {r["name"]: role_code(r["name"]) for r in roles}
    opened: dict = {}
    for r in roles:
        for entry in r.get("pages") or []:
            if not entry.get("error"):
                opened.setdefault(entry["page"], []).append((r["name"], entry))
    ids = {code: screen_id(code) for code in pages if code in opened}
    screens = []
    for code, page in pages.items():
        if code not in ids:
            continue
        entries = opened[code]
        screen = {
            "id": ids[code],
            "title": page.get("title") or code,
            "roles": [codes[name] for name, _ in entries],
            "maps": f"/pages/@{code}",
        }
        if page.get("type") == "detail":
            screen["record"] = page.get("detail_view") or code
            sample = next(
                (e.get("record") for _, e in entries if e.get("record")), None
            )
            if sample is not None:
                screen["sample"] = sample
        screens.append(screen)
    manifest = json.loads(parts["manifest.json"])
    app = cap.get("app") or {}
    first = roles[0]["name"] if roles else ""
    manifest.update(
        {
            "title": app.get("name") or manifest.get("title") or "Prototype",
            "kit": True,
            "roles": {codes[r["name"]]: r["name"] for r in roles},
            "default_role": codes.get(first, ""),
            "home": {
                codes[r["name"]]: ids[r["landing"]]
                for r in roles
                if r.get("landing") in ids
            },
            "screens": screens,
        }
    )
    parts["manifest.json"] = json.dumps(manifest, indent=2, ensure_ascii=False)
    parts[SPEC_PART] = _spec_part(spec_text)
    parts[BRIDGE_PART] = BRIDGE_JS.replace(
        "__ROLES__", json.dumps(manifest["roles"], ensure_ascii=False)
    )
    parts["imported/bridge.css"] = BRIDGE_CSS
    studio = set(CANONICAL) | set(CANONICAL.values())
    resolved = {n: v for n, v in (cap.get("vars") or {}).items() if n[2:] not in studio}
    canon = [f"  --{c}: {v};" for c, v in KIT_APP_LOOK.items()]
    if "--brand" in resolved:
        canon.append("  --brand-soft: var(--b50);")
    parts["tokens.css"] = (
        "/* The look this app resolves to (the spec's theme included), and the canonical names the build\n"
        "   maps (app.design): the greys the kit draws the app with, not the Studio page's. The kit page\n"
        "   draws with its own stylesheet (imported/styles.css). */\n:root {\n"
        + "\n".join([f"  {n}: {v};" for n, v in resolved.items()] + canon)
        + "\n}\n"
    )
    return parts


def _cache_path(spec_text: str, kit_html: str, adapter: str) -> Path:
    import hashlib
    import tempfile

    h = hashlib.sha256()
    for text in (
        spec_text,
        kit_html,
        adapter,
        WORKER.read_text(encoding="utf-8"),
        Path(__file__).read_text(encoding="utf-8"),
    ):
        h.update((text or "").encode("utf-8"))
        h.update(b"\0")
    return Path(tempfile.gettempdir()) / "zas-kit-proto" / f"{h.hexdigest()[:32]}.json"


def open_from_kit(spec_text: str, kit_html: str, adapter: str) -> dict:
    """The starting prototype for ``spec_text``: the kit page itself, as an imported page
    (``{path: text}`` parts). It draws the YAML with the kit's own pages, forms, filters and status
    changes, exactly as the template's preview does.

    Raises KitCaptureError when it can't be made here (no Playwright, a spec the kit can't read).
    Cached on disk by everything that goes into it, so re-importing a pack gives the same parts.
    """
    cache = _cache_path(spec_text, kit_html, adapter)
    try:
        return json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    names, _ = split_root(kit_styles(kit_html))
    cap = capture(spec_text, kit_html, adapter, [*names, "--brand"], outline=True)
    parts = imported_parts(cap, kit_html, spec_text)
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(parts), encoding="utf-8")
    except OSError:
        pass
    return parts


def starting_prototype_issues(spec_text: str, parts: dict) -> list[str]:
    """What Commit would refuse if a requirement started on ``spec_text`` + ``parts`` were
    committed as it is: screens that don't draw, and what they show that the spec doesn't say
    (the same capture and coverage check, prototype_coverage). One line per problem."""
    import yaml

    from .prototype_coverage import coverage, ensure_capture, format_gaps, render_gaps

    try:
        doc = yaml.safe_load(open_spec(spec_text, parts))
    except Exception as exc:  # noqa: BLE001 - a starter that doesn't parse is lint's to report
        return [f"The starter can't be read with its prototype: {exc}"]
    design = (doc.get("app") or {}).get("design")
    try:
        bundle, why = ensure_capture(
            parts, design=design if isinstance(design, dict) else None
        )
    except Exception as exc:  # noqa: BLE001
        bundle, why = None, str(exc)
    if bundle is None:
        return [f"The prototype could not be rendered here to check it: {why}"]
    out = [f"screen {line[2:]}" for line in render_gaps(bundle, doc)]
    gaps = format_gaps(coverage(doc, bundle))
    out += [line[2:] for line in gaps.splitlines() if line.startswith("- ")]
    return out


def _kit_owned(path: str) -> bool:
    """A part that is the kit page itself (its markup, stylesheet and scripts), not this app's."""
    from .prototype import BODY_PART

    return (path == BODY_PART or path.startswith("imported/")) and path not in (
        SPEC_PART,
        BRIDGE_PART,
        "imported/bridge.css",
    )


def refresh_kit(parts: dict, pristine: dict | None, kit_html: str) -> dict | None:
    """``parts`` of a kit page on the current kit (``kit_html``, the generic template's preview page),
    so the preview draws what the kit draws now. Only the kit's own parts change; the spec, the
    bridge, look.css, tokens.css and the manifest stay. None when there is nothing to do, or when
    those kit parts were edited for this app (they differ from the template's own, ``pristine``)."""
    from .prototype import import_html

    if not kit_html or not is_kit_page(parts):
        return None
    from .prototype import parts_hash

    own = {p: t for p, t in parts.items() if _kit_owned(p)}
    try:
        manifest = json.loads(parts.get("manifest.json") or "{}")
    except ValueError:
        return None
    # Untouched: as the template drew it, or as the last refresh left it.
    pristine_own = {p: t for p, t in (pristine or {}).items() if _kit_owned(p)}
    if own != pristine_own and manifest.get("kit_hash") != parts_hash(own):
        return None
    fresh, _ = import_html(kit_html)
    fresh = {p: t for p, t in fresh.items() if _kit_owned(p)}
    if fresh == own:
        return None
    new = {p: t for p, t in parts.items() if not _kit_owned(p)}
    new.update(fresh)
    manifest["kit_hash"] = parts_hash(fresh)
    new["manifest.json"] = json.dumps(manifest, indent=2, ensure_ascii=False)
    return new


def refreshed_kit_parts(requirement) -> dict | None:
    """A template-mode requirement's prototype on the current kit, or None (see refresh_kit)."""
    from zango.apps.shared.app_templates.services.generic import generic_version

    template = requirement.template if requirement.template_slug else None
    generic = generic_version()
    if template is None or generic is None:
        return None
    return refresh_kit(
        requirement.prototype_parts or {},
        getattr(template, "prototype_parts", None) or {},
        generic.builder_html,
    )


def is_from_kit(parts: dict) -> bool:
    """Whether ``parts`` were generated by open_from_kit (not shipped or written by hand)."""
    try:
        manifest = json.loads((parts or {}).get("manifest.json") or "{}")
        return manifest.get("source") == KIT_SOURCE or bool(manifest.get("kit"))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# The YAML that goes with it
# ---------------------------------------------------------------------------


def open_spec(spec_text: str, parts: dict, *, with_design: bool = True) -> str:
    """``spec_text`` with what Free design needs next to these parts: ``app.design`` (from
    tokens.css) and a ``prototype.screens`` entry per screen. What the spec already says wins."""
    from zango.apps.shared.app_templates.services.spec import yamlio

    from .prototype import design_tokens, manifest_of

    doc = yamlio.load_rt(spec_text)
    if not hasattr(doc, "get"):
        return spec_text
    manifest, _ = manifest_of(parts)
    app = doc.get("app")
    if with_design and hasattr(app, "get") and not app.get("design"):
        design = design_tokens(parts)
        if design:
            app["design"] = design
    proto = doc.get("prototype")
    if not hasattr(proto, "get"):
        proto = {}
        doc["prototype"] = proto
    screens = proto.get("screens")
    if not isinstance(screens, list):
        screens = []
        proto["screens"] = screens
    have = {str(s.get("id")) for s in screens if hasattr(s, "get")}
    for s in manifest.get("screens") or []:
        if s["id"] not in have and s.get("maps"):
            screens.append({"id": s["id"], "maps": s["maps"]})
    return yamlio.dump_rt(doc)
