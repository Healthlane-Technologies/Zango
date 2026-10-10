"""
Log in to a running Zango app as each test user / role. Ported from the flow proven in
the PSP template's api-playground/flows/zango_auth.py, on requests.Session.

Credentials live in <ws>/.zas/test_users.json (chmod 600, never committed, never printed):

    {"target": "http://<app host>:<port>",
     "users": [{"name": "Test Finance", "email": "test.finance@vendorhub.test",
                "password": "...", "roles": ["Finance"]}]}

Sequence (Zango app-auth, browser client):
  1. GET  /api/v1/appauth/config/                 -> csrftoken cookie
  2. POST /api/v1/appauth/login/  {email|phone, password} + X-CSRFToken
       200 -> logged in          401 next_step role_selection -> 3
       401 set_password -> 2b    401 other (mfa) -> cannot be scripted
  2b. POST /api/v1/appauth/password/set/  {new_password}   (file users only; new password is
       saved to the file BEFORE it is sent; letter first; specials from @$!#%*?&)
  3. POST /api/v1/appauth/role/set/?role=<id>
  4. POST /api/v1/appauth/role/switch/?role=<id>   (when another role was asked for)
  then GET /api/v1/profile/ for roles {name: id} and the current role.

Repeated failures lock login from this machine for every account (403 ACCOUNT_LOCKED):
never retry with guessed passwords.
"""

import json
import os
import secrets
import string
import sys

try:
    import requests
except ImportError:  # pragma: no cover
    sys.stderr.write("zas_test needs requests: pip install requests\n")
    raise

AUTH = "/api/v1/appauth"
COOKIE = "zangocookie"
SPECIALS = "@$!#%*?&"


class AuthError(RuntimeError):
    pass


def users_path(ws):
    return os.path.join(ws, ".zas", "test_users.json")


def load_users(ws):
    try:
        with open(users_path(ws), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_users(ws, data):
    path = users_path(ws)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def generate_password(policy=None):
    """Meets a Zango password_policy; first character is a letter (Zango rule not in the policy)."""
    policy = policy or {}
    length = max(int(policy.get("min_length") or 8), 14)
    chars = [secrets.choice(string.ascii_uppercase), secrets.choice(string.ascii_lowercase),
             secrets.choice(string.digits), secrets.choice(SPECIALS)]
    pool = string.ascii_letters + string.digits + SPECIALS
    chars += [secrets.choice(pool) for _ in range(length - len(chars) - 1)]
    secrets.SystemRandom().shuffle(chars)
    return secrets.choice(string.ascii_letters) + "".join(chars)


def user_for_role(data, role):
    """The user holding `role`; a dedicated single-role user wins."""
    holders = [u for u in data.get("users", []) if role is None
               or str(role).lower() in [r.lower() for r in u.get("roles", [])]]
    return min(holders, key=lambda u: len(u.get("roles", [])), default=None)


class ZSession(requests.Session):
    """requests.Session that sends X-CSRFToken and Referer on writes. Extra attrs: target, role, role_id, roles."""

    def __init__(self, target):
        super().__init__()
        self.target = target.rstrip("/")
        self.role, self.role_id, self.roles = "", 0, {}
        self.email = None
        self.headers.update({"Accept": "application/json"})

    def url(self, path):
        return path if path.startswith("http") else self.target + path

    def csrf(self):
        return self.cookies.get("csrftoken", "")

    def request(self, method, url, *args, **kwargs):  # noqa: D401
        headers = kwargs.pop("headers", None) or {}
        if method.upper() not in ("GET", "HEAD", "OPTIONS"):
            headers.setdefault("X-CSRFToken", self.csrf())
            headers.setdefault("Referer", self.target + "/")
        kwargs.setdefault("timeout", 60)
        return super().request(method, self.url(url), *args, headers=headers, **kwargs)


def _json(r):
    try:
        return r.json()
    except ValueError:
        return {"_text": r.text[:300]}


def _step(body):
    inner = body.get("response", body) if isinstance(body, dict) else {}
    return ((inner or {}).get("data") or {}).get("next_step") or {}


def _err(body):
    if not isinstance(body, dict):
        return str(body)[:300]
    inner = body.get("response", body)
    errs = (inner or {}).get("errors") or body.get("errors") or []
    if isinstance(errs, list) and errs:
        return "; ".join(e.get("message", str(e)) if isinstance(e, dict) else str(e) for e in errs)
    return json.dumps(body)[:300]


def _load_profile(s):
    r = s.get("/api/v1/profile/")
    body = _json(r)
    if r.status_code != 200:
        raise AuthError(f"profile check failed (HTTP {r.status_code}): {_err(body)}")
    resp = body.get("response", {}) or {}
    s.roles = {x["name"]: x["id"] for x in (resp.get("profile_data") or {}).get("roles", [])}
    cur = resp.get("current_role") or {}
    s.role, s.role_id = cur.get("name", ""), cur.get("id", 0)


def _role_id(s, role):
    if role in (None, ""):
        return None
    if str(role).isdigit():
        return int(role)
    for name, rid in s.roles.items():
        if name.lower() == str(role).lower():
            return int(rid)
    raise AuthError(f"role {role!r} is not one of this user's roles: {sorted(s.roles)}")


def switch_role(s, role):
    rid = _role_id(s, role)
    r = s.post(f"{AUTH}/role/switch/?role={rid}")
    if r.status_code != 200:
        raise AuthError(f"role switch to {role!r} failed (HTTP {r.status_code}): {_err(_json(r))}")
    _load_profile(s)
    return s


def login(ws, role=None, target=None):
    """A logged-in ZSession acting as `role` (user picked from test_users.json)."""
    data = load_users(ws)
    target = target or data.get("target")
    if not target:
        raise AuthError(f"no target: set \"target\" in {users_path(ws)}")
    u = user_for_role(data, role)
    if not u or not u.get("password") or not (u.get("email") or u.get("phone")):
        raise AuthError(f"no test user{' for role ' + repr(role) if role else ''} in {users_path(ws)}")
    s = ZSession(target)
    s.email = u.get("email") or u.get("phone")
    r = s.get(f"{AUTH}/config/")
    if r.status_code != 200 or not s.csrf():
        raise AuthError(f"auth config gave HTTP {r.status_code} and no csrftoken cookie (is the app running at {target}?)")
    creds = {"email": u["email"]} if u.get("email") else {"phone": u["phone"]}
    r = s.post(f"{AUTH}/login/", json={**creds, "password": u["password"]})
    body = _json(r)
    if r.status_code == 403 and "LOCK" in json.dumps(body).upper():
        raise AuthError(f"login locked for this machine: {_err(body)} - wait for the cool-off; do not retry other passwords")
    if r.status_code == 401 and _step(body).get("id") in ("set_password", "first_login", "password_expiry"):
        new = generate_password((_step(body).get("metadata") or {}).get("password_policy"))
        old = u["password"]
        u["password"] = new
        save_users(ws, data)  # saved BEFORE sending: a crash can't lose the only working password
        r = s.post(f"{AUTH}/password/set/", json={"new_password": new})
        body = _json(r)
        if r.status_code not in (200, 401):
            u["password"] = old
            save_users(ws, data)
            raise AuthError(f"first-login password set failed (HTTP {r.status_code}): {_err(body)}")
        sys.stderr.write(f"zas_test.auth: {s.email}: first-login password set and saved to the users file\n")
    if r.status_code == 401:
        st = _step(body)
        if st.get("id") != "role_selection":
            raise AuthError(f"login stopped at pending step {st.get('id')!r}: finish it once in the browser")
        roles = (st.get("metadata") or {}).get("roles") or {}
        if isinstance(roles, list):
            offered = {x.get("name"): int(x.get("id")) for x in roles}
        else:
            offered = {name: int(rid) for rid, name in roles.items()}
        s.roles = offered
        rid = _role_id(s, role) if role else min(offered.values())
        r = s.post(f"{AUTH}/role/set/?role={rid}")
        if r.status_code != 200:
            raise AuthError(f"role selection failed (HTTP {r.status_code}): {_err(_json(r))}")
    elif r.status_code != 200:
        raise AuthError(f"login failed for {s.email} (HTTP {r.status_code}): {_err(body)}")
    _load_profile(s)
    if role and _role_id(s, role) != s.role_id:
        switch_role(s, role)
    if not s.cookies.get(COOKIE):
        raise AuthError(f"logged in but no {COOKIE} cookie was set")
    return s


def sessions(ws, roles):
    """{role: ZSession} for every role that has a test user; errors collected, not raised."""
    out, errors = {}, {}
    for role in roles:
        try:
            out[role] = login(ws, role)
        except AuthError as e:
            errors[role] = str(e)
    return out, errors


def anonymous(ws, target=None):
    data = load_users(ws)
    s = ZSession(target or data.get("target") or "http://localhost:8000")
    try:
        s.get(f"{AUTH}/config/")
    except requests.RequestException:
        pass
    return s


def storage_state(s):
    """Playwright storageState JSON for a logged-in session (cookies only)."""
    from urllib.parse import urlparse
    host = urlparse(s.target).hostname
    cookies = []
    for c in s.cookies:
        cookies.append({
            "name": c.name, "value": c.value, "domain": c.domain or host, "path": c.path or "/",
            "expires": c.expires if c.expires else -1, "httpOnly": bool(c.has_nonstandard_attr("HttpOnly")),
            "secure": bool(c.secure), "sameSite": "Lax",
        })
    return {"cookies": cookies, "origins": []}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Log in as a role and print who you are (never the password).")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--role")
    a = ap.parse_args(argv)
    try:
        s = login(a.workspace, a.role)
    except AuthError as e:
        print(f"zas_test.auth: {e}", file=sys.stderr)
        return 1
    print(f"logged in as {s.email} → role {s.role} (id {s.role_id}); roles {sorted(s.roles)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
