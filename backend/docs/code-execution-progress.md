# Code Execution — Implementation Progress

Branch: `feat/zango_codexec`
Spec: `code-execution-spec.html`

This file tracks what's done and what's left. Update inline as work progresses.

---

## Status legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done
- `[!]` blocked / needs decision

---

## Environment & setup

- [x] Branch `feat/zango_codexec` created
- [x] `psycopg2-binary` bumped 2.9.9 → 2.9.10 in `requirements/base.txt` (Python 3.13 compat)
- [x] `lxml` + `xmlsec` rebuilt from source against shared libxml2 (mismatch fix)
- [x] `pip install -e .` succeeds
- [!] `lxml` actually installed at **6.1.1** (not the pinned 5.3.0). Works. If a future `pip install` downgrades it, either bump the pin to 6.1.1 or rebuild from source.

---

## Design artifacts

- [x] End-to-end spec: `backend/docs/code-execution-spec.html`
  - Hero + goals + user flow
  - Mockup 1: list view
  - Mockup 2: editor modal (with file upload zone + helpers cheatsheet)
  - Mockup 3: execution detail with tabs
  - Data model (CodeSnippet, CodeSnippetFile, CodeExecution, CodeExecFile, CodeExecutionLogLine)
  - API surface
  - Security & deny list
  - Tenant isolation — four layers (AST / Postgres role / search_path / ConnectionGuard)
  - Execution runtime sequence
  - Logs & observability (print + logger)
  - Files & I/O (`codexec` helper API)
  - Edge cases
  - Implementation phases

---

## Codebase conventions confirmed (so the new code looks like it belongs)

- Apps live under `src/zango/apps/<name>/` with `apps.py`, `models.py`, `migrations/`, `__init__.py`
- New tenant-scoped apps go in `TENANT_APPS` in `src/zango/config/settings/base.py`
- API views extend `ZangoGenericPlatformAPIView` from `zango.core.api`, use `TenantMixin`
- Standard decorator: `@method_decorator(set_app_schema_path, name="dispatch")`
- URL pattern: nested under `api/platform/v1/apps/<uuid:app_uuid>/<area>/`
- Response helper: `get_api_response(success, response, status)`
- Pagination: `ZangoAPIPagination` from `zango.core.api.utils`
- Models inherit `FullAuditMixin` from `zango.core.model_mixins`
- Auditlog registration: `auditlog.register(Model, m2m_fields=...)`

---

## Phase 1 — MVP

### Backend

- [x] **App scaffold** `zango.apps.code_execution`
  - `apps.py` (CodeExecutionConfig)
  - `__init__.py`, `admin.py`, `migrations/__init__.py`
  - Registered in `TENANT_APPS` (settings/base.py:60)

- [x] **Models** + initial migration generated
  - `CodeSnippet` — UUID PK · name (unique) · slug · description · code · code_hash · version · timeout_seconds · is_archived · audit
  - `CodeSnippetFile` — UUID PK · FK snippet · name · file (FileField, upload_to=codexec/snippets/&lt;sid&gt;/&lt;uuid&gt;) · size · sha256 · unique(snippet, name)
  - `CodeExecution` — UUID PK · FK snippet (PROTECT) · snippet_version · source_snapshot · source_hash · status · celery_task_id · queued/started/ended_at · duration_ms · stdout · stderr · return_value · return_value_truncated · exception_* · triggered_by · trigger_kind
  - `CodeExecFile` — UUID PK · FK execution (CASCADE) · kind · name · file (FileField, upload_to=codexec/runs/&lt;eid&gt;/&lt;kind&gt;/&lt;uuid&gt;) · FK source_snippet_file (SET_NULL) · unique(execution, kind, name)
  - Auditlog registered on all four
  - Migration: `src/zango/apps/code_execution/migrations/0001_initial.py`
  - **NOT applied yet** — needs `python manage.py migrate_schemas --schema=&lt;tenant&gt;` per tenant, or `migrate_schemas` for all

- [x] **AST deny-list validator** (`validator.py`)
  - `validate(source) -> list[Violation]`, `assert_valid()`, `CodeValidationError`
  - Banned: imports (subprocess/socket/ctypes/…/django_tenants.utils), builtin names (eval/exec/compile/__import__/getattr-reflection-on-connection), dunders, attribute paths (`os.system`, `connection.set_tenant`, etc.), assignment to `connection.schema_name`/`tenant`, SQL literals matching `SET search_path|SCHEMA|ROLE`
  - Alias-aware (catches `import os as oo; oo.system(...)`)
  - Smoke-tested with 12 cases (all pass)

- [x] **`zango.codexec` helper module** (`src/zango/codexec.py`)
  - All 11 helpers: `read`, `read_text`, `read_json`, `open`, `local_path`, `list_inputs`, `write`, `write_text`, `write_json`, `open_output`, `list_outputs`
  - `FileRef` proxy with `.name`/`.size`/`.read`/`.read_text`/`.open`
  - `bind_execution()` context manager for executor to scope a call
  - `CodexecOutsideRunError`, `CodexecFileNotFound`
  - Name sanitization (basename, no `..`, no NUL, 255-char cap)

- [x] **Celery task** `codexec_executor` (`apps/code_execution/tasks.py`)
  - Resolves tenant, marks status=running with started_at + celery_task_id
  - Runs `Workspace(tenant).ready()`
  - AST recheck at pickup (catches deny-list updates between save and run)
  - Wraps stdout/stderr with `CapturingStream` (1 MB / 256 KB caps + 8 KB per-line)
  - Inside `transaction.atomic()`: `begin_isolated_session()` (search_path + statement_timeout) → `install_connection_guard()` (L4) → `codexec.bind_execution()` → `compile + exec`
  - Catches `SoftTimeLimitExceeded` → status=timeout; any other exception → status=failed; exceptions caught inside the atomic so outputs persist
  - Picks up `codexec_result` from the namespace as the return value (JSON-serialized, 64 KB cap, `return_value_truncated` flag)
  - End-to-end smoke-tested: success path, ValueError, AST block, file write

- [~] **Tenant isolation** (L1/L3/L4 done; **L2 PARKED**)
  - [x] L1 (AST): in `validator.py`
  - [!] **L2 (Postgres role): PARKED per user direction.** No DB-level role provisioning at this time. This was the load-bearing cross-tenant defense; without it, snippets *can* still reach other tenant schemas via fully-qualified raw SQL (`SELECT … FROM "tntApp"."x"`). Documented gap. To revisit, restore L2 provisioning (commit history before the revert).
  - [x] L3 (search_path + statement_timeout): in `isolation.py` → `begin_isolated_session()`
  - [x] L4 (ConnectionGuard): in `guard.py`. Patches `set_tenant` / `set_schema` / `set_schema_to_public` and `__setattr__` on the live DatabaseWrapper class. Thread-local active flag.

- [x] **Permission policies** seeded via `0002_initial_policies.py` migration
  - `platform.code_execution.use` (name=`codexec.use`)
  - `platform.code_execution.edit` (name=`codexec.edit`)
  - `platform.code_execution.run` (name=`codexec.run`)
  - **Enforcement note**: APIs are gated by `IsAuthenticatedPlatformUser` only. Fine-grained per-policy enforcement (binding to user roles via PolicyGroupModel) deferred — the policy records exist; admins can attach them, but the API doesn't yet check them individually.

- [x] **API: snippets** (`api/platform/code_execution/v1/`)
  - GET/POST `/snippets/`
  - GET/PATCH/DELETE `/snippets/{id}/`
  - POST `/snippets/{id}/run/`
  - POST `/snippets/validate/`

- [x] **API: snippet files**
  - GET/POST `/snippets/{id}/files/` (multipart upload)
  - DELETE `/snippets/{id}/files/{file_id}/`
  - GET `/snippets/{id}/files/{file_id}/download/`

- [x] **API: executions**
  - GET `/executions/` (filterable by snippet_id, status)
  - GET `/executions/{id}/`
  - GET `/executions/{id}/files/`
  - GET `/executions/{id}/files/{file_id}/download/`

- [x] **Snapshot-on-run** in the run endpoint — every `CodeSnippetFile` of the snippet becomes a `CodeExecFile(kind=input, source_snippet_file=ref)` sharing the storage path. No byte copy.

- [x] **URL routing** wired into `api/platform/urls.py` at `v1/apps/<uuid:app_uuid>/code-execution/`

### Frontend (zelthy3-app-panel under `/Users/rajat/poc_projects/Zango/frontend`)

- [x] **List view page** at `src/pages/appCode/components/CodeExecution/index.jsx`
  - Search box, paginated table, "+ Add New", row actions (run, edit, archive)
  - Status pills (success/failed/running/queued/timeout/aborted/draft) with pulse on in-flight
  - Polls every 5s while any row is queued/running
  - Row click → opens latest execution detail
- [x] **Editor modal** at `src/pages/appCode/components/CodeExecution/EditorModal.jsx`
  - Monaco editor (vs-dark, Python, 4-space indent)
  - Name, description, timeout (5–300s) fields
  - File upload zone — shows saved snippet files + pending files separately
  - Always-visible helpers cheatsheet (11 functions, read/write color-coded)
  - Debounced inline AST validation (calls `/snippets/validate/` 600ms after typing)
  - Save / Save & Run actions · ⌘S / ⌘↵ keyboard shortcuts · Esc to close
- [x] **Execution detail page** at `src/pages/appCode/components/CodeExecution/ExecutionDetail.jsx`
  - Breadcrumb + status pill + 5-tile metadata strip (run id, started, duration, triggered_by, source version)
  - 5 tabs: Logs (stdout/stderr/traceback) · Return value · Files (inputs + outputs side-by-side, downloads) · Source at run · Metadata
  - Polls every 2s while status is queued/running
- [x] **Tab registered** in `AppCode/index.jsx` as "Code Execution" — sibling to Async Tasks

**API contract**: GET + POST only (per user direction). Update is `POST /snippets/{id}/update/`, archive is `POST /snippets/{id}/archive/`, file delete is `POST /snippets/{id}/files/{file_id}/delete/`.

---

## Phase 2 — Live & richer history

- [x] `CodeExecutionLogLine` table + buffered batch insert (BATCH_SIZE=32 inside `LineLogger`)
- [x] `GET /executions/{id}/log-tail/?after_seq=N` returns lines + run status + is_terminal + next_seq
- [x] Frontend: live polling on detail page (1s log-tail, 3s metadata), status pills auto-update, log lines rendered with level colors (out/err/warn/info/sys)
- [x] POST `/executions/{id}/abort/` revokes celery task with terminate=True + frontend Abort button (shown only while in-flight)
- [x] Worker heartbeat sweeper task `zango.code_execution.sweep_stuck_runs` — marks executions stuck >2× the longest plausible timeout as `failed · WorkerLost`. Register in beat schedule.
- [x] Export run history as CSV via `GET /executions/export.csv?snippet_id=&status=&from=&to=`
- [!] **Cross-snippet "Run history" UI page deferred** — existing flow (list → execution detail) covers the common case. A dedicated cross-snippet page is a small UI addition for a follow-up.
- [!] **OpenTelemetry spans DEFERRED** — needs integration with the existing `zango.core.monitoring.telemetry` pipeline. Add in a follow-up session.

---

## Deferred (Phase 3 — Later)

- Dedicated `codexec` celery queue + worker pool
- Per-tenant rate limits
- Drafts vs. published states · approval workflow
- Diff view between snippet versions
- Parameterized runs (typed inputs)
- Cron scheduling (overlap with AppTask, evaluate consolidation)
- Saved fixture files attached to snippets (auto-staged on every run)
- Websocket-based live tail (replacing polling)

---

## Open decisions

- [x] Tenant isolation: 4-layer defense (AST / Pg role / search_path / ConnectionGuard) — **decided**
- [x] File scope: two-level (snippet + execution) with snapshot on run — **decided**
- [x] CodeSnippetFile deletion: hard delete, no `is_deleted` flag — **decided**
- [x] Snapshot mode: share storage_key with reference counting (not copy bytes) — **decided**
- [x] Filename preservation: DB `name` is the source of truth; storage key uses UUID — **decided**
- [x] Visibility field on snippet: removed — **decided**

---

## Notes / gotchas

- Project root: `/Users/rajat/poc_projects/poc/` — settings.py at `poc/poc/settings.py`
- Zango backend: `/Users/rajat/poc_projects/Zango/backend/` (this repo)
- Frontend: `/Users/rajat/poc_projects/Zango/frontend/`
- Python 3.13, Postgres 17, Django 5, DRF
- Storage backend per project: `STORAGES['default'] = zango.core.storage_utils.S3MediaStorage` for newmi
- `pip install -e .` is the install command (NOT `pip install .`)
