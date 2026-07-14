# App- & Role-level Session Timeout — Implementation Progress

**Branches**
- zelthy3: `feat/session-timeout-app-role-config`
- pkg-zango-appbuilder: `feat/session-timeout-app-role-config`

**Design:** backend-only, three levers off one resolver `get_app_session_timeout(request)`, no workspace template edits. Mirrors token-TTL (#601). Config lives in `session_policy` (keys `session_warn_after`, `session_expire_after`; seconds; absent = inherit; precedence user_role > tenant > platform default).

Full plan: `session-timeout-config-plan.html`.

---

## Checklist

| # | Task | Repo | Status |
|---|------|------|--------|
| 1 | Schema: `session_warn_after`/`session_expire_after` in `SessionPolicy` | zelthy3 | ✅ done |
| 2 | Resolver: `get_app_session_timeout()` in `core/utils.py` | zelthy3 | ✅ done |
| 3 | Middleware: subclass for per-app/role logout | zelthy3 | ✅ done |
| 4 | Serializer: validate keys + platform hints (tenant + role) | zelthy3 | ✅ done |
| 5 | Legacy: override `session_security_tags` filters | zelthy3 | ✅ done |
| 6 | Appbuilder: serve per-app/role config | appbuilder | ✅ done |
| 7 | Frontend UI: `SessionTimeoutField` + wiring | zelthy3 | ✅ done |
| 8 | Verify: resolver/serializer/both frontends | both | ✅ done |

Legend: ⬜ todo · 🟡 in progress · ✅ done · ⚠️ blocked

---

## Notes / decisions

- **INSTALLED_APPS ordering (verified):** Django's templatetag registry lets a *later*
  app override an earlier one for the same library name. `zango.apps.shared.tenancy`
  (line 47) is after `session_security` (line 41) in `SHARED_APPS`, so the override in
  `tenancy/templatetags/session_security_tags.py` wins. No reordering needed. (Same
  pattern as the existing `zstatic` override.)
- **Middleware role-timing concern resolved:** `get_auth_priority` auto-resolves role
  from `session["role_id"]`, so the middleware (which runs before the user-role
  middleware) still gets the right role. No tenant-floor fallback needed.
- Resolver lives at `core/utils.py::get_app_session_timeout` — accepts `request` OR
  explicit user/role/tenant; returns `(warn_after, expire_after)` with platform
  fallback + `warn < expire` guard.

---

## Verification results (all ✅)

Run with `zango_venv` (py3.10, editable zango → this checkout):

- **Unit tests:** `src/zango/tests/test_session_timeout.py` — **16 passed**
  (resolver precedence/guard, serializer validation incl. bool/int/range/warn<expire,
  platform-hint inject/strip round-trip).
  `PYTHONPATH=. DJANGO_SETTINGS_MODULE=test_project.settings python -m pytest src/zango/tests/test_session_timeout.py`
- **Middleware:** `get_expire_seconds` → 300 (custom) / platform default (inherit). ✅
- **Legacy templatetag:** rendering `{% load session_security_tags %}{{ request|warn_after }}|{{ request|expire_after }}`
  → `250|300` (override) / platform default (inherit). Confirmed Django resolves OUR
  module: `get_installed_libraries()['session_security_tags']` →
  `zango.apps.shared.tenancy.templatetags.session_security_tags`. ✅
- **`manage.py check`:** clean (E003 duplicate-library warning silenced via
  `SILENCED_SYSTEM_CHECKS`).
- **Frontend lint:** edited JSX/JS files → 0 errors (2 pre-existing unrelated warnings).

### E003 note (resolved)
Django's system check warns (templates.E003 / W003) when a templatetag library name is
defined by two apps. It's a WARNING, not fatal — and Django's registry resolves the
later-installed app (tenancy), i.e. our override. Silenced explicitly in `settings/base.py`.

## Remaining (not code — deployment)
- Appbuilder: rebuild the frontend bundle if a new min.js needs committing (backend change
  only touches Python; React hook already consumes served config).
- Manual smoke: set a short expiry on an app, idle in a legacy app + an appbuilder app,
  confirm warning + auto-logout fire per-role.

## Log

_(newest first — one line per change)_
- Verified end-to-end: 16 unit tests pass; middleware + legacy templatetag render per-role
  values; manage.py check clean (E003 silenced); frontend lint clean.
- Frontend (task 7): sessionTimeout.js util + SessionTimeoutField.jsx; wired into
  ModernAuthConfig (form, 2 save sites, Yup, 2 read-only rows) and RoleOverrideModal
  (field + save normalize + import).
- Appbuilder (task 6): get_session_security_config(user,role,tenant) → get_app_session_timeout;
  views.py passes context. Separate branch.
- zelthy3 backend done (tasks 1–5): schema keys, resolver, middleware swap, serializer
  validation+hints (tenant+role), legacy templatetag override. Syntax-checked OK.
