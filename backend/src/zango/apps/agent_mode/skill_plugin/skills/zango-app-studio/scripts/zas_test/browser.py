"""Headless Chromium for the UI and design layers (Python Playwright, sync API).

    pip install playwright && python3 -m playwright install chromium

One browser per run; one context per role, logged in by copying the cookies of an
auth.login() session (no UI login per test). Console errors and failed API calls are
collected per page so a check can fail on them.
"""

import contextlib
import os
import re
import sys

from . import auth

VIEWPORT = {"width": 1440, "height": 900}
IGNORED_CONSOLE = ("favicon", "Download the React DevTools", "[vite]", "ResizeObserver loop",
                   "Cross-Origin-Opener-Policy header has been ignored")  # http on a non-localhost dev domain


def require():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        sys.stderr.write("the UI/design layers need Playwright: pip install playwright && python3 -m playwright install chromium\n")
        raise SystemExit(2)


@contextlib.contextmanager
def browser():
    require()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        try:
            yield b
        finally:
            b.close()


class RolePage:
    """A page for one role with console/network error capture."""

    def __init__(self, b, target, session=None, viewport=None, pinned=False):
        self.target = target.rstrip("/")
        extra = {"timezone_id": "UTC", "locale": "en-US", "device_scale_factor": 1} if pinned else {}
        self.ctx = b.new_context(viewport=viewport or VIEWPORT, base_url=self.target,
                                 storage_state=auth.storage_state(session) if session else None, **extra)
        self.page = self.ctx.new_page()
        self.errors = []
        self.page.on("console", self._console)
        self.page.on("pageerror", lambda e: self.errors.append(f"page error: {e}"))
        self.page.on("response", self._response)

    def _console(self, m):
        if m.type == "error" and not any(x in m.text for x in IGNORED_CONSOLE):
            self.errors.append(f"console: {m.text[:300]}")

    def _response(self, r):
        if r.status >= 500:
            self.errors.append(f"HTTP {r.status} {r.url.split('?')[0]}")

    def open(self, path, wait='[data-zas="page"], [data-zas="login"]', timeout=20000):
        self.errors.clear()
        self.page.goto(path if path.startswith("http") else self.target + path, wait_until="domcontentloaded")
        if wait:
            self.page.wait_for_selector(wait, timeout=timeout)
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        self.page.evaluate("() => document.fonts.ready.then(() => true)")
        return self.page

    def shot(self, ws, *parts):
        d = os.path.join(ws, ".zas", "screens", *parts[:-1])
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, parts[-1] + ".png")
        self.page.screenshot(path=p, full_page=True)
        return p

    def tree(self):
        """Every [data-zas] node: kind, key, tone, order, layout, visible text (first 80 chars)."""
        return self.page.eval_on_selector_all("[data-zas]", """els => els.map(e => ({
            kind: e.dataset.zas, key: e.dataset.zasKey || null, tone: e.dataset.zasTone || null,
            order: e.dataset.zasOrder !== undefined ? Number(e.dataset.zasOrder) : null,
            layout: e.dataset.zasLayout || null, text: (e.innerText || '').trim().slice(0, 80),
            visible: !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)}))""")

    def close(self):
        self.ctx.close()


def visible_uid(M, entity, session, uids):
    """The newest record in `uids` the session's role can see (row scoping), else the first it can see."""
    uid = uids[-1] if uids else None
    try:
        ep = M["entities"][entity]["names"]["endpoint"]
        j = session.get(ep, params={"view": "table", "action": "get_table_data", "start": 0, "length": 200}).json()
        rows = j.get("data") or ((j.get("response") or {}).get("data") if isinstance(j.get("response"), dict) else None) or []
        seen = [str(x.get("object_uuid")) for x in rows]
        if seen and uid not in seen:
            uid = next((u for u in reversed(uids) if u in seen), seen[0])
    except Exception:
        pass
    return uid


def rebuilt(M, kind, code):
    """A page ("page") or 360 ("view") the build rebuilt from the prototype (`rebuild: true`): the
    mockup is its truth, so the kit-layout checks skip it and the look round compares it."""
    return any(sc.get("cls") == "rebuild" and sc.get("kind") == kind and sc.get("code") == code
               for sc in (M.get("prototype") or {}).get("screens") or [])


RAW_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?")


def raw_dates(text):
    """A problem line when the page prints a machine timestamp (2026-10-28T03:45:48.33+00:00) where a
    person reads a date, else None."""
    hits = sorted(set(RAW_DATE.findall(text or "")))
    return f"shows raw timestamps ({', '.join(hits[:2])}): format them as dates" if hits else None


def route_entity(M, route, param):
    """The entity a route's `:param` names a record of: the crud page whose route is the part before
    it (`/app/cases/:id/review` → the page at `/app/cases` → its entity), else None."""
    head = route.split("/:" + param, 1)[0].rstrip("/")
    for p in M["pages"].values():
        if p.get("type") == "crud" and p.get("entity") and (p.get("route") or "").rstrip("/") == head:
            return p["entity"]
    return None


def fill_route(M, route, records, session):
    """(path, None) with each `:param` set to a record the session can see, or (None, why) when a
    param names no entity (a link token) or there is no record for it."""
    import re

    path = route
    for param in re.findall(r":(\w+)", route):
        ent = route_entity(M, route, param)
        if not ent:
            return None, f"the route {route} takes :{param}, which names no record (a token or code): not opened"
        uids = (records or {}).get(ent) or []
        uid = visible_uid(M, ent, session, uids) if uids else None
        if not uid:
            return None, f"no {ent} record to open {route} with: run zas_test.api first"
        path = path.replace(":" + param, str(uid), 1)
    return path, None


def detail_path(M, entity, uuid):
    """<hero list route>/detail-view/<uuid> (contracts §9)."""
    for p in M["pages"].values():
        if p.get("type") == "crud" and p.get("entity") == entity:
            return f"{p['route'].rstrip('/')}/detail-view/{uuid}"
    for p in M["pages"].values():
        if p.get("type") == "detail" and (M["detail_views"].get(p.get("detail_view")) or {}).get("hero") == entity:
            return f"{p['route'].rsplit('/:', 1)[0]}/{uuid}"
    return None
