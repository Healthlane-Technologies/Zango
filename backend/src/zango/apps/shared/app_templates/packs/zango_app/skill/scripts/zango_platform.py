#!/usr/bin/env python3
"""
Platform-side steps for an App Studio build, driven by <ws>/.zas/spec.resolved.json.
Every command is idempotent, reads its result back, and exits non-zero on any mismatch.

    zango_platform.py app        --project <dir> --name <app code> [--domain <host>]
                                                    create the app if missing, set its domain, install
                                                    appbuilder → crud → workflow; prints the workspace path
    zango_platform.py packages   --workspace <ws>   install appbuilder → crud → workflow if missing
    zango_platform.py roles      --workspace <ws>   create the spec's roles that are missing, add every role
                                                    to AllowFromAnywhere (needed to load the app shell)
    zango_platform.py schedule   --workspace <ws>   set task schedules from `# zas:schedule <cron>` lines in tasks.py
    zango_platform.py sync       --workspace <ws>   sync policies + tasks (App Panel API)
    zango_platform.py users      --workspace <ws>   one test user per role → .zas/test_users.json (chmod 600)
    zango_platform.py appbuilder --workspace <ws>   routes + per-role menus (SVG icons), merged, read back
    zango_platform.py check      --workspace <ws>   roles ↔ policies ↔ menus read back against the spec
    zango_platform.py all        --workspace <ws>   roles, sync, schedule, users, appbuilder, check

Platform credentials: PLATFORM_USERNAME / PLATFORM_USER_PASSWORD from the nearest
deploy/.env above the workspace (or env vars of the same name, or --user/--password).
Platform URL: --platform (default http://localhost:8000). Passwords and tokens are never printed.
References: references/zango/app-panel-api.md, references/zango/packages/appbuilder/api-configuration.md,
references/map/access.md, references/map/pages-menus.md.
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

try:
    import requests
except ImportError:  # pragma: no cover
    sys.stderr.write("zango_platform needs requests: pip install requests\n")
    raise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zas_test import auth as zauth  # noqa: E402  (password generator + users file helpers)

RESERVED_ROLES = {"AnonymousUsers", "SystemUsers"}
FALLBACK_ICON = "circle"


class PlatformError(RuntimeError):
    pass


# ───────────────────────── setup ─────────────────────────

def find_env(ws):
    d = os.path.abspath(ws)
    for _ in range(6):
        p = os.path.join(d, "deploy", ".env")
        if os.path.exists(p):
            return p
        d = os.path.dirname(d)
    return None


def read_env(path):
    out = {}
    if not path:
        return out
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out


def load(ws, name):
    with open(os.path.join(ws, ".zas", name), encoding="utf-8") as f:
        return json.load(f)


def app_name(ws):
    with open(os.path.join(ws, "settings.json"), encoding="utf-8") as f:
        return json.load(f)["app_name"]


def ok(r):
    try:
        j = r.json()
    except ValueError:
        raise PlatformError(f"{r.request.method} {r.url.split('?')[0]} → HTTP {r.status_code}, not JSON (logged out? token expired?)")
    if r.status_code >= 400 or not j.get("success", True):
        raise PlatformError(f"{r.request.method} {r.url.split('?')[0]} → HTTP {r.status_code}: {json.dumps(j)[:400]}")
    return j.get("response", j)


def records(res, key):
    """List payloads come as {key: {records: [...]}}, {key: [...]}, {results: [...]} or a bare list."""
    if isinstance(res, list):
        return res
    if not isinstance(res, dict):
        return []
    v = res.get(key, res)
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return v.get("records") or v.get("results") or []
    return res.get("results") or []


class Platform:
    def __init__(self, ws, url, user, password, app=True):
        self.ws, self.url = ws, url.rstrip("/")
        self.s = requests.Session()
        self.s.headers["Accept"] = "application/json"
        self._login(user, password)
        if app:
            self.use_app(self._app())

    def use_app(self, a):
        self.app = a
        self.uuid = a.get("uuid") or a.get("app_uuid") or a.get("id")

    def find_app(self, name):
        return next((a for a in records(self.get("/api/v1/apps/"), "apps") if a.get("name") == name), None)

    def _hdr(self):
        return {"X-CSRFToken": self.s.cookies.get("csrftoken", ""), "Referer": self.url + "/platform/"}

    def _login(self, user, password):
        if not user or not password:
            raise PlatformError("platform credentials missing: set PLATFORM_USERNAME / PLATFORM_USER_PASSWORD in deploy/.env")
        r = self.s.get(self.url + "/auth/login/", timeout=30)
        if r.status_code >= 400:
            raise PlatformError(f"platform not reachable at {self.url} (HTTP {r.status_code})")
        r = self.s.post(self.url + "/auth/login/", timeout=30, allow_redirects=True,
                        data={"csrfmiddlewaretoken": self.s.cookies.get("csrftoken", ""), "username": user, "password": password},
                        headers={"Referer": self.url + "/auth/login/", "Origin": self.url})
        # session cookie name is configurable (SESSION_COOKIE_NAME, e.g. "zangocookie")
        if not any(c.name != "csrftoken" for c in self.s.cookies) or "/auth/login" in r.url:
            raise PlatformError("platform login failed (check PLATFORM_USERNAME / PLATFORM_USER_PASSWORD)")

    def get(self, path, **params):
        return ok(self.s.get(self.url + path, params=params, timeout=60))

    def post(self, path, data=None, params=None, files=None):
        return ok(self.s.post(self.url + path, data=data or {}, params=params, files=files, headers=self._hdr(), timeout=60))

    def put(self, path, data=None, files=None):
        return ok(self.s.put(self.url + path, data=data or {}, files=files, headers=self._hdr(), timeout=60))

    def _app(self):
        name = app_name(self.ws)
        a = self.find_app(name)
        if a:
            return a
        raise PlatformError(f"app {name!r} (settings.json app_name) not found on {self.url}")

    def app_url(self):
        """http://<primary domain>:<platform port> - where the app is served."""
        doms = self.app.get("domains") or []
        dom = next((d.get("domain") or d.get("domain_url") for d in doms if isinstance(d, dict) and d.get("is_primary")), None) \
            or next((d.get("domain") or d.get("domain_url") for d in doms if isinstance(d, dict)), None) \
            or next((d for d in doms if isinstance(d, str)), None)
        if not dom:
            raise PlatformError("the app has no domain configured (App Panel → app settings → domains)")
        p = urlparse(self.url)
        dom = re.sub(r"^https?://", "", dom).split("/")[0]
        host = dom if ":" in dom or not p.port else f"{dom}:{p.port}"
        return f"{p.scheme}://{host}"

    # roles
    def roles(self):
        res = self.get(f"/api/v1/apps/{self.uuid}/roles/", page_size=500)
        return {r["name"]: r for r in records(res, "roles")}


# ───────────────────────── commands ─────────────────────────

def cmd_roles(P, M, log):
    have = P.roles()
    for name in M["roles"]:
        if name in RESERVED_ROLES:
            continue
        if name in have:
            log(f"role {name!r} exists (id {have[name]['id']})")
            continue
        P.post(f"/api/v1/apps/{P.uuid}/roles/", data={"name": name})  # an empty "policies" string is rejected by zango 1.2 ("expected pk value")
        log(f"role {name!r} created")
    have = P.roles()
    missing = [n for n in M["roles"] if n not in have]
    if missing:
        raise PlatformError(f"roles still missing after create: {missing}")
    # every role must be in AllowFromAnywhere, or its users cannot load the app shell / login flow.
    # The PUT replaces the policy's roles, so send ALL role ids (references/zango/app-panel-api.md).
    pols = records(P.get(f"/api/v1/apps/{P.uuid}/policies/", search="AllowFromAnywhere"), "policies")
    afa = next((p for p in pols if p.get("name") == "AllowFromAnywhere"), None)
    if not afa:
        raise PlatformError("AllowFromAnywhere policy not found")
    ids = sorted({int(r["id"]) for r in have.values()})
    cur = {int(x["id"]) if isinstance(x, dict) else int(x) for x in (afa.get("roles") or [])
           if (isinstance(x, dict) and str(x.get("id", "")).isdigit()) or str(x).isdigit()}
    if not set(ids) <= cur:
        files = [("id", (None, str(afa["id"])))] + [("roles", (None, str(i))) for i in sorted(cur | set(ids))]
        P.put(f"/api/v1/apps/{P.uuid}/policies/{afa['id']}/", files=files)
        log(f"AllowFromAnywhere: roles set to {sorted(cur | set(ids))}")
    else:
        log("AllowFromAnywhere already covers every role")
    return have


def cmd_sync(P, M, log):
    P.post(f"/api/v1/apps/{P.uuid}/policies/", params={"action": "sync_policies"}, files={"_": ("", "")})
    log("policies synced")
    try:
        P.post(f"/api/v1/apps/{P.uuid}/tasks/")
        log("tasks synced")
    except PlatformError as e:
        log(f"tasks sync: {e} (no tasks.py yet is fine)")


def cmd_users(P, M, log):
    roles = P.roles()
    data = zauth.load_users(P.ws)
    data["target"] = data.get("target") or P.app_url()
    users = data.setdefault("users", [])
    existing = {u["email"].lower(): u for u in users if u.get("email")}
    res = P.get(f"/api/v1/apps/{P.uuid}/users/", page_size=1000)
    plat = {(u.get("email") or "").lower(): u for u in records(res, "users")}
    on_platform = set(plat)
    code = M["app"].get("code") or "app"
    for name, r in M["roles"].items():
        if name in RESERVED_ROLES:
            continue
        email = f"test.{r['slug']}@{code.replace('_', '-')}.test"
        u = existing.get(email)
        if email in on_platform and u and u.get("password"):
            pu = plat[email]
            if pu.get("is_active") is False:
                # a workflow hook may have disabled it (e.g. an app_user login on close-out): re-enable
                # with only the test role, so the next run starts from a clean account
                P.put(f"/api/v1/apps/{P.uuid}/users/{pu['id']}/",
                      files=[("name", (None, u.get("name") or pu.get("name") or "")), ("email", (None, email)),
                             ("mobile", (None, "")), ("is_active", (None, "true")),
                             ("roles", (None, str(roles[name]["id"])))])
                log(f"test user {email} was inactive: re-enabled")
            else:
                log(f"test user {email} exists")
            continue
        if email in on_platform and not (u and u.get("password")):
            log(f"test user {email} exists on the platform but its password is not in the users file: "
                f"reset it in App Panel, or delete the user and re-run")
            continue
        pwd = zauth.generate_password()
        u = u or {"name": f"Test {name}", "email": email, "roles": [name]}
        u["password"] = pwd
        if u not in users:
            users.append(u)
        zauth.save_users(P.ws, data)  # saved before sending: the only copy of the password
        P.post(f"/api/v1/apps/{P.uuid}/users/", data={"name": u["name"], "email": email, "mobile": "",
                                                       "password": pwd, "roles": roles[name]["id"]})
        log(f"test user {email} created ({name})")
    zauth.save_users(P.ws, data)
    log(f"users file: {zauth.users_path(P.ws)} (target {data['target']})")


def _config_api(P):
    res = P.get(f"/api/v1/apps/{P.uuid}/packages/", action="config_url", package_name="appbuilder")
    url = res.get("url") if isinstance(res, dict) else res
    u = urlparse(url)
    token = parse_qs(u.query).get("token", [None])[0]
    if not token:
        raise PlatformError("appbuilder config_url has no token")
    base = P.app_url() + u.path.rstrip("/")
    return base, token


def _svg(icons, name):
    svg = icons.get(name or "") or icons.get(FALLBACK_ICON)
    if not svg or "<svg" not in svg:
        raise PlatformError(f"no SVG for icon {name!r}: run lucide_icons.py first")
    return svg


def page_routes(M):
    """(page code, route dict) for every page that needs an AppBuilder route (map/pages-menus.md §1)."""
    out = []
    list_heroes = {p.get("entity") for p in M["pages"].values() if p.get("type") == "crud"}
    for code, p in M["pages"].items():
        t = p.get("type")
        if t == "detail":
            hero = (M["detail_views"].get(p.get("detail_view")) or {}).get("hero")
            if hero in list_heroes:
                continue
            path = re.sub(r"/:[^/]+$", "", p["route"])
        else:
            path = p["route"]
        out.append((code, {"name": p.get("title") or code, "path": path, "page_type": "custom",
                           "component": p["export"], "icon_name": p.get("icon")}))
    out.append(("__zas", {"name": "Style guide", "path": "/app/__zas", "page_type": "custom",
                          "component": "ZasStyleGuide", "icon_name": "layers"}))
    return out


def menu_icon_for(M, page_code):
    for r in M["roles"].values():
        for it in r.get("menu", []):
            for i in (it.get("items") or [it]):
                if i.get("page") == page_code and i.get("icon"):
                    return i["icon"]
    return None


def cmd_appbuilder(P, M, log):
    icons = load(P.ws, "menu_icons.json")
    base, token = _config_api(P)
    S = requests.Session()

    def call(path, action, method="GET", body=None, **extra):
        r = S.request(method, f"{base}{path}", params={"token": token, "action": action, **extra},
                      json=body, timeout=60, allow_redirects=False)
        if r.status_code in (301, 302):
            raise PlatformError("appbuilder token rejected (redirect to login): re-run this command for a fresh token")
        return ok(r)

    # routes: merge by path, keep unknown routes
    cur = call("/routes/api/", "get_routes")
    current = (cur or {}).get("routes") or []
    by_path = {r["path"]: r for r in current}
    wanted = page_routes(M)
    for code, rt in wanted:
        icon = _svg(icons, rt.pop("icon_name") or menu_icon_for(M, code) or FALLBACK_ICON)
        r = by_path.get(rt["path"], {})
        by_path[rt["path"]] = {**r, **rt, "icon": icon, "extra_params": r.get("extra_params") or {}}
    call("/routes/api/", "save_routes", "POST", {"routes": list(by_path.values())})
    saved = {r["path"]: r for r in (call("/routes/api/", "get_routes") or {}).get("routes", [])}
    bad = [rt["path"] for _, rt in wanted if rt["path"] not in saved or saved[rt["path"]].get("component") != rt["component"]]
    if bad:
        raise PlatformError(f"routes not saved as sent: {bad}")
    log(f"routes saved: {len(wanted)} spec routes ({len(saved)} total)")
    route_of = {code: saved[rt["path"]] for code, rt in wanted}

    # menus: one config per role
    roles = P.roles()
    configs = call("/api/", "get_configs") or []
    cfg_by_role = {c.get("user_role") or c.get("role"): c for c in configs}
    for name, r in M["roles"].items():
        if name in RESERVED_ROLES:
            continue
        items = []

        def item(i, inherited_icon=None):
            p = i["page"]
            rt = route_of.get(p)
            if not rt:
                log(f"  {name}: menu page {p!r} has no route (detail page?) - skipped")
                return None
            return {"route_id": rt["route_id"], "name": i.get("label") or M["pages"][p].get("title") or p,
                    "uri": rt["path"], "icon": _svg(icons, i.get("icon") or menu_icon_for(M, p) or inherited_icon or FALLBACK_ICON),
                    "children": []}
        for it in r.get("menu", []):
            if it.get("group"):
                kids = [x for x in (item(c, it.get("icon")) for c in it.get("items") or []) if x]
                if kids:
                    items.append({"route_id": "", "name": it["group"], "uri": "#", "icon": _svg(icons, it.get("icon") or FALLBACK_ICON),
                                  "children": kids})
            else:
                x = item(it)
                if x:
                    items.append(x)
        land = r.get("landing")
        if land and land in route_of:
            uri = route_of[land]["path"]
            hit = next((x for x in items if x["uri"] == uri), None)
            if hit is None:
                for g in items:
                    k = next((c for c in g["children"] if c["uri"] == uri), None)
                    if k:
                        g["children"].remove(k)
                        hit = k
                        log(f"  {name}: landing {land!r} moved out of group {g['name']!r} to the top")
                        break
                items = [x for x in items if x["uri"] != "#" or x["children"]]
            if hit is None:
                hit = item({"page": land})
                log(f"  {name}: landing {land!r} was not in the menu - added first")
            items = [hit] + [x for x in items if x is not hit]
        body = {"user_role": roles[name]["id"], "menu": items, "config": {}}
        if name in cfg_by_role:
            call("/api/", "update_config", "PUT", body, pk=cfg_by_role[name]["pk"])
        else:
            call("/api/", "create_config", "POST", body)
        log(f"menu for {name}: {len(items)} items")

    # read back
    configs = {c.get("user_role") or c.get("role"): c for c in (call("/api/", "get_configs") or [])}
    ids = {r["route_id"] for r in saved.values()}
    problems = []
    for name in M["roles"]:
        if name in RESERVED_ROLES:
            continue
        c = configs.get(name)
        if not c:
            problems.append(f"no menu config for {name}")
            continue
        for x in c.get("menu", []):
            for y in [x] + (x.get("children") or []):
                if "<svg" not in (y.get("icon") or ""):
                    problems.append(f"{name}: menu item {y.get('name')!r} lost its SVG icon")
                if y.get("uri") != "#" and y.get("route_id") not in ids:
                    problems.append(f"{name}: menu item {y.get('name')!r} points at a missing route")
    if problems:
        raise PlatformError("menus read back wrong:\n  " + "\n  ".join(problems))
    log("menus read back OK")


PACKAGES = ["appbuilder", "crud", "workflow"]  # this order: workflow's version list changes after crud


def _vkey(v):
    return [int(x) if x.isdigit() else -1 for x in re.split(r"[.\-+]", str(v))]


def cmd_packages(P, M, log):
    for name in PACKAGES:
        recs = {r.get("name"): r for r in records(P.get(f"/api/v1/apps/{P.uuid}/packages/"), "packages")}  # re-read each time
        r = recs.get(name)
        if not r:
            raise PlatformError(f"package {name!r} is not offered by this platform")
        if str(r.get("status", "")).lower() in ("installed", "true") or r.get("installed_version"):
            log(f"package {name} installed")
            continue
        vers = r.get("versions") or []
        stable = [v for v in vers if re.fullmatch(r"[\d.]+", str(v))] or vers
        if not stable:
            raise PlatformError(f"package {name!r} has no versions")
        ver = max(stable, key=_vkey)
        P.post(f"/api/v1/apps/{P.uuid}/packages/", data={"name": name, "version": ver})
        log(f"package {name} {ver} installed")
    if P.ws:
        man = os.path.join(P.ws, "manifest.json")
        if os.path.exists(man):
            have = json.dumps(json.load(open(man)))
            gone = [n for n in PACKAGES if n not in have]
            if gone:
                raise PlatformError(f"manifest.json does not list {gone} after install")


def cmd_app(P, a, log):
    import socket
    import time
    app = P.find_app(a.name)
    if not app:
        res = P.post("/api/v1/apps/", data={"name": a.name, "description": a.description or a.name})
        task = res.get("task_id")
        log(f"app {a.name} creating (task {task})")
        for _ in range(120):
            st = P.get("/api/v1/apps/", action="get_app_creation_status", task_id=task)
            if st.get("deployed"):
                break
            time.sleep(5)
        else:
            raise PlatformError("app creation did not finish in 10 minutes")
        app = P.find_app(a.name)
        if not app:
            raise PlatformError("app created but not listed")
    P.use_app(app)
    log(f"app {a.name} uuid {P.uuid}")
    dom = a.domain or f"{a.name.replace('_', '')}.local"
    doms = [d.get("domain") if isinstance(d, dict) else d for d in (app.get("domains") or [])]
    if dom not in doms:
        P.put(f"/api/v1/apps/{P.uuid}/", data={"domains": json.dumps([{"domain": dom, "is_primary": True}])})
        log(f"domain {dom} set")
        P.use_app(P.find_app(a.name))
    try:
        socket.gethostbyname(dom)
    except OSError:
        log(f"ACTION NEEDED: {dom} does not resolve. Add this line to /etc/hosts (needs sudo): 127.0.0.1 {dom}")
    P.ws = os.path.join(os.path.abspath(a.project), "workspaces", a.name)
    cmd_packages(P, None, log)
    log(f"workspace: {P.ws}")


def cmd_schedule(P, M, log):
    """`# zas:schedule <min> <hour> <day-of-month> <month> <day-of-week>` on a line above a task's def."""
    want = {}
    for mod in M["modules"]:
        p = os.path.join(P.ws, "backend", mod["code"], "tasks.py")
        if not os.path.exists(p):
            continue
        cron = None
        for line in open(p, encoding="utf-8"):
            m = re.match(r"\s*#\s*zas:schedule\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", line)
            if m:
                cron = m.groups()
                continue
            d = re.match(r"\s*def\s+(\w+)\s*\(", line)
            if d and cron:
                want[d.group(1)] = cron
                cron = None
    if not want:
        log("no `# zas:schedule` lines in tasks.py: nothing to schedule")
        return
    tasks = records(P.get(f"/api/v1/apps/{P.uuid}/tasks/", page_size=500), "tasks")
    missing = []
    for fn, (mi, h, dom, mon, dow) in want.items():
        t = next((x for x in tasks if str(x.get("name", "")).split(".")[-1] == fn), None)
        if not t:
            missing.append(fn)
            continue
        exp = {"minute": mi, "hour": h, "day_of_month": dom, "month_of_year": mon, "day_of_week": dow}
        P.post(f"/api/v1/apps/{P.uuid}/tasks/{t['id']}/",
               files=[("crontab_exp", (None, json.dumps(exp))), ("is_enabled", (None, "true")), ("kwargs", (None, "{}"))])
        log(f"task {fn}: {' '.join([mi, h, dom, mon, dow])}")
    if missing:
        raise PlatformError(f"tasks not registered on the platform (run `sync` first): {missing}")
    log("restart Celery beat/worker to pick up schedules: zango_env.py celery --workspace <ws>")


def cmd_check(P, M, log):
    problems = []
    have = P.roles()
    for name in M["roles"]:
        if name not in have:
            problems.append(f"role missing: {name}")
    want = {}
    for E in M["entities"].values():
        for pol in E.get("policies", []):
            want[pol["name"]] = set(pol["roles"])
    res = P.get(f"/api/v1/apps/{P.uuid}/policies/", page_size=1000)
    recs = records(res, "policies")
    got = {p.get("name"): p for p in recs}
    for name, roles in want.items():
        p = got.get(name)
        if not p:
            problems.append(f"policy not synced: {name}")
            continue
        pr = p.get("roles") or []
        names = {x.get("name") if isinstance(x, dict) else x for x in pr}
        if pr and names != roles and not roles <= names:
            problems.append(f"policy {name}: roles {sorted(names)} != spec {sorted(roles)}")
    if problems:
        raise PlatformError("check failed:\n  " + "\n  ".join(problems))
    log(f"check OK: {len(M['roles'])} roles, {len(want)} policies")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["app", "packages", "roles", "sync", "schedule", "users", "appbuilder", "check", "all"])
    ap.add_argument("--workspace")
    ap.add_argument("--project", help="app: the Zango project dir (has manage.py)")
    ap.add_argument("--name", help="app: app name = the spec's app.code")
    ap.add_argument("--description")
    ap.add_argument("--domain", help="app: domain (default <name without _>.local)")
    ap.add_argument("--platform", default=os.environ.get("ZANGO_PLATFORM_URL", "http://localhost:8000"))
    ap.add_argument("--user")
    ap.add_argument("--password")
    a = ap.parse_args(argv)
    if a.command == "app" and not (a.project and a.name):
        ap.error("app needs --project and --name")
    if a.command != "app" and not a.workspace:
        ap.error("--workspace is required")
    env = read_env(find_env(a.workspace or a.project))
    user = a.user or os.environ.get("PLATFORM_USERNAME") or env.get("PLATFORM_USERNAME")
    pwd = a.password or os.environ.get("PLATFORM_USER_PASSWORD") or env.get("PLATFORM_USER_PASSWORD")

    def log(msg):
        print(f"zango_platform: {msg}")
    try:
        if a.command == "app":
            cmd_app(Platform(None, a.platform, user, pwd, app=False), a, log)
            return 0
        M = load(a.workspace, "spec.resolved.json")
        P = Platform(a.workspace, a.platform, user, pwd)
        steps = ["roles", "sync", "schedule", "users", "appbuilder", "check"] if a.command == "all" else [a.command]
        for s in steps:
            globals()[f"cmd_{s}"](P, M, log)
    except (PlatformError, requests.RequestException, OSError, KeyError) as e:
        print(f"zango_platform: FAILED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
