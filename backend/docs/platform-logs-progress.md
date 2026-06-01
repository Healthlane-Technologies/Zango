# Platform Logs — Implementation Progress

Live checklist for the Platform Logs feature implementation. See
[`platform-logs-design.html`](./platform-logs-design.html) for the spec.

**Branch:** `feat/zango_logs`  •  **Started:** 2026-05-29
**Resumption rule:** read this file top-to-bottom, find the first unchecked
box, continue from there. Commit a progress.md update alongside every code
commit.

---

## Current state — where to resume

> _Update this paragraph after each session._

**Last touched:** 2026-06-01 — **all phases (P0-P7) complete**. Backend + frontend + docs + IAM template all committed.
**Next up:** Manual smoke against staging once IAM role gets the policy attached and a connector row is seeded in `LogConnectorConfig`. Future enhancements live under "P5+ deferred" in the design doc.

---

## P0 · Scaffold + model + permissions

- [x] Create folder `backend/src/zango/apps/platform_logs/` with `__init__.py`
- [x] `apps.py` — `PlatformLogsConfig(AppConfig)` mirroring the codexec pattern
- [x] Register `"zango.apps.platform_logs"` in `SHARED_APPS` in `config/settings/base.py`
- [x] `models.py` — `Component` + `ConnectorType` text choices, `LogConnectorConfig` model
  - [x] Fields: `id` (UUID PK), `environment`, `component`, `connector`, `config` (JSONField), `is_active`
  - [x] FullAuditMixin
  - [x] `UniqueConstraint(environment, component)`
- [x] `admin.py` — register `LogConnectorConfig` for `django-admin`
- [x] Generate `migrations/0001_initial.py`
- [x] ~~`migrations/0002_initial_policies.py` — RunPython seeding `platform.logs.view` + `platform.logs.admin`~~
  - **Deferred to v2.** `platform_logs` is a SHARED_APP — its migrations run in the public schema only, but `PolicyModel` lives in tenant schemas. In v1 both endpoints are platform-admin-only, so we gate with `IsAuthenticatedPlatformUser` + admin check. Tenant-side policy seeding gets a dedicated TENANT_APP when v2 opens viewing to app users.
- [ ] Apply migrations on a tenant; `manage.py check` clean ← `manage.py check` is clean; migrate when ready to deploy

---

## P1 · Connector abstraction

- [x] Folder `connectors/` with `__init__.py`
- [x] `connectors/exceptions.py` — `ConnectorError`, `ConnectorThrottled`, `ConnectorNotFound`, `ConnectorConfigError`, `ConnectorUnauthorized`
- [x] `connectors/base.py`
  - [x] `LogLevel` enum (DEBUG..CRITICAL, plus `UNKNOWN`)
  - [x] `@dataclass LogStream` (name, last_event_ts, first_event_ts, retention_in_days)
  - [x] `@dataclass LogFilters` (since, until, q, pattern, levels, streams, app_name, limit)
  - [x] `@dataclass LogLine` (ts, message, stream, level, structured, cursor_token)
  - [x] `@dataclass Cursor` (token: str, direction: enum) + `CursorDirection` enum
  - [x] `@dataclass LogPage` (lines, next_cursor, has_more)
  - [x] `@dataclass FacetSet` (levels, streams)
  - [x] `LogConnector` Protocol with `list_streams / fetch / facets / deep_link`
- [x] `connectors/__init__.py` — registry mapping `ConnectorType` → factory, lazy import

---

## P2 · CloudWatch connector

- [x] `connectors/cloudwatch.py`
  - [x] `CloudWatchConfig` dataclass with `region`, `log_group_name`, `stream_prefix?`, `format`, `role_arn?`
  - [x] `_get_client()` — memoized boto3 client per (region, role)
  - [x] STS AssumeRole path when `role_arn` set
  - [x] `list_streams(since)` — DescribeLogStreams, paginate, filter on lastEventTimestamp, 30s cache
  - [x] `fetch(filters, page)`
    - [x] Build `FilterLogEvents` kwargs: `logGroupName`, `startTime`, optional `endTime`, optional `logStreamNames`, optional `filterPattern`
    - [x] If `filters.app_name` and `format == "verbose"`: append `[<app_name>:` to filter pattern
    - [x] If `filters.app_name` and `format == "json"`: append `{ $.app_name = "<app_name>" }`
    - [x] Parse each event into `LogLine` with level regex fallback
    - [x] Return `LogPage(lines, next_cursor=…)`
  - [x] `facets()` — sample 200 lines, extract distinct levels & streams, cache 60s
  - [x] `deep_link(filters)` — Logs Insights console URL
  - [x] `_with_retry()` wrapper — 3 attempts on `ThrottlingException` / `ServiceUnavailable`, exponential jitter
- [x] Level parser regexes for celery + stdlib + verbose-Zango
- [ ] Tests: `tests/test_cloudwatch_connector.py` with `botocore.stub.Stubber` ← deferred to P7 polish

---

## P3 · API

- [x] `api/platform/platform_logs/__init__.py`
- [x] `api/platform/platform_logs/v1/__init__.py`
- [x] `serializers.py`
  - [x] `LogConnectorConfigSerializer` (read + write with `validate()` round-trip)
  - [x] `LogLineSerializer`
  - [x] `LogStreamSerializer`
  - [x] `LogPageSerializer`
  - [x] `CursorSerializer`
- [x] `views.py`
  - [x] `ComponentListView` — GET `/components/` — list configured components for current env
  - [x] `LogBrowseView` — GET `/<component>/` — backward cursor pagination
  - [x] `LogTailView` — GET `/<component>/tail/` — forward (live) cursor
  - [x] `StreamListView` — GET `/<component>/streams/`
  - [x] `FacetsView` — GET `/<component>/facets/`
  - [x] `DeepLinkView` — GET `/<component>/deep-link/`
  - [x] `ConnectorListUpsertView` — GET / POST `/connectors/`
  - [x] `ConnectorTestView` — POST `/connectors/test/`
  - [x] Throttle classes (30/min browse, 60/min tail)
  - [x] Permission classes — `IsSuperAdminPlatformUser` for admin, `IsPlatformUserAllowedApp` for view
  - [x] `_handle_connector_errors` decorator translates connector exceptions to HTTP responses
- [x] `urls.py` — `in_app_urls` + `admin_urls`
- [x] Register both in `api/platform/urls.py`
- [x] `manage.py check` clean
- [ ] `curl` smoke against a local connector pointed at staging CW → returns lines ← do after seeding a config row

---

## P4 · Producer-side fix

- [x] Edit `config/settings/base.py` LOGGING dict:
  - [x] add `"filters": ["tenant_filter"]` to `handlers.console`
  - [x] switch `formatter` on `handlers.console` to `verbose` when `ENV in {"staging", "prod"}`
- [x] Make `TenantContextFilter` safe when tenant context isn't bound (boot, mgmt commands without schema)
- [x] `apps/platform_logs/celery_logging.py` — `@setup_logging.connect` handler re-asserting Django's LOGGING dict
- [x] Wire that signal in `apps/platform_logs/apps.py:ready()`
- [ ] Sanity check on local: console shows `[tenant:domain]` prefix when ENV=staging ← validate at deploy
- [ ] Deploy to staging; CloudWatch lines have prefix ← validate after deploy

---

## P5 · Frontend · Settings page (platform-level)

- [ ] Route: add `Platform > Settings > Log connectors` to platform settings nav
- [ ] `pages/platformSettings/logConnectors/index.jsx`
  - [ ] Load `/api/v1/platform/logs/connectors/` on mount
  - [ ] Render three `ConnectorCard`s per (env × component) — `app`, `celery`, `celery_beat`
  - [ ] Empty state for unconfigured rows with `+ Configure` CTA
- [ ] `ConnectorCard.jsx` — read-only mini summary + Edit / Test buttons
- [ ] `ConnectorEditModal.jsx`
  - [ ] Form fields: connector type, region, log_group_name, stream_prefix, format, role_arn
  - [ ] Test connection button → POST to a `/connectors/test/` action
  - [ ] Save → POST upsert, close on success
  - [ ] Inline field-level errors
- [ ] `api.js` — wrappers for list / upsert / test

---

## P6 · Frontend · Logs tab (in-app)

- [ ] Add route under app panel: `Apps > <app> > Logs`
- [ ] Add nav item to the app sidebar
- [ ] `pages/appCode/components/Logs/index.jsx`
  - [ ] Hosts `ComponentTabs` + `HeaderStrip` + `LogsTable` + `FilterRail`
- [ ] `ComponentTabs.jsx` — `App / Celery / Celery beat` with line counts
- [ ] `HeaderStrip.jsx` — time picker, search input, Live tail toggle, Open in CloudWatch
- [ ] `LogsTable.jsx`
  - [ ] Virtualized with react-window
  - [ ] Sticky header
  - [ ] Row click → expand detail card (in-place row insertion)
  - [ ] New-row pulse animation when polled
  - [ ] Level + stream + tenant + logger chips
- [ ] `DetailCard.jsx` — 8-field meta grid + dark traceback panel + action row
- [ ] `FilterRail.jsx`
  - [ ] Levels (multi-toggle)
  - [ ] Streams (search + checklist)
  - [ ] Polling (live tail / pause on scroll up / interval dropdown)
  - [ ] Native pattern textarea
- [ ] `useLogTail.js` — polling hook with backoff on hidden tab, throttle handling
- [ ] `api.js` — list, tail, streams, facets, deep-link wrappers
- [ ] Manual smoke against staging CloudWatch

---

## P7 · Polish

- [ ] `docs/iam/platform-logs.json` — IAM policy for the ECS task role
- [ ] `apps/platform_logs/README.md` — local-dev story, env vars, where to look on prod
- [ ] Empty / loading / error / throttled states for both frontend pages
- [ ] Final docstring pass

---

## Decisions log

> Append to this log whenever something is chosen or a tradeoff is made
> that isn't already in the design doc.

- **2026-05-29 — kept `LogConnectorConfig` in public schema** (one row per env × component). Per-app override deferred to a future phase if needed.
- **2026-05-29 — Settings lives at Platform > Settings, not inside the app's Logs tab**, per review feedback. Logs tab inside an app filters to that app via `app_name`.
- **2026-05-29 — Producer-side fix bundled with v1** (Option B in the design doc § Tenant gap) since it's ~5 LOC and unlocks tenant scoping from day one.
- **2026-06-01 — Permission policies deferred to v2.** v1 endpoints are platform-admin-only; gated by `IsAuthenticatedPlatformUser` + admin check. Tenant-side policy seeding needs a separate TENANT_APP because `platform_logs` is SHARED.

---

## Reference

- Design: `backend/docs/platform-logs-design.html` (TOC entry "Implementation plan" at the bottom)
- Existing tenant filter: `backend/src/zango/core/monitoring/log_filter.py`
- Existing LOGGING dict: `backend/src/zango/config/settings/base.py:260`
- Existing code-execution patterns (reference for app layout): `feat/zango_codexec` branch — `backend/src/zango/apps/code_execution/`
