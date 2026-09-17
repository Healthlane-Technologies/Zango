# Vendored skill — provenance and delta

**Source:** `~/.claude/skills/zango-app-developer/` (user-level Claude Code skill)
**Vendored:** 2026-09-10
**Vendored as:** `zango-agent-mode:zango-app-developer-server`

The interactive skill runs on a developer's laptop with Docker, a human to
answer questions, and a Node toolchain. None of those exist in server mode, so
this copy is a fork rather than a mirror.

## Delta from the source

### SKILL.md — rewritten (406 → ~190 lines)

| Source section | Change |
|---|---|
| Capability 1 — Bootstrap Docker environment | **Deleted.** The platform is already running. `references/bootstrap-templates.md` deleted with it. |
| Post-Bootstrap: Create App | **Deleted.** The app exists before the run starts. |
| Capability 3 — App Panel API automation | **Deleted.** It authenticated with platform admin credentials via a curl cookie jar; the agent must never hold those. `references/app-panel-api.md` is kept as reference only. |
| STEP 1 — Discover Context | Replaced: the run-context block in the prompt is authoritative; discovery is confined to the workspace. |
| STEP 3 — Create Roles | The agent now *names* required roles in its summary instead of creating them (role creation needs platform credentials). |
| STEP 4 (planning) — "ask the user" throughout | Converted to "decide, and record the assumption". This is the single most important edit: a headless run that tries to ask burns turns and then guesses anyway. The UX decision tables are kept — they are the most valuable part of the skill. |
| Two sections both numbered **STEP 4** | Renumbered. This was a bug in the source. |
| STEP 5 — Post-Implementation (`docker compose exec … ws_makemigration / ws_migrate / update-apps`, Celery restart) | Replaced with a hand-off: the platform runs the sequence and reports each step. |
| STEP 5 — Frontend setup (`npx @zango-core/create-zango-app`, `npm run build:zango`) | **Deleted.** No Node in the platform container. The agent implements the backend plus a CRUD route and describes remaining React work. |
| STEP 6 — Verify (`docker compose logs`) | Replaced: report what to verify. |
| STEP 7 — Create Test Users | **Deleted** (needs platform credentials). |
| Capability 4 — Frontend Reference | Kept as reference so existing React sources can still be edited coherently; the build step is gone. |
| Critical Rules | Kept verbatim apart from the docker-logs debugging line. These rules are the highest-value part of the skill. |

### references/ — kept, with two bug fixes and five banners

Otherwise byte-identical to the source, so upstream diffs stay reviewable.

**Bugs fixed** (both present in the source and verified against this repo):

1. `templates/app-module/README.md` told the agent to run
   `zango manage-app <app> sync_policies`. **No such CLI command exists** — the
   registered commands are `start-project`, `list-packages`, `install-package`,
   `git-setup`, `update-apps`. Replaced with a note pointing at `ws_sync`.
2. `zango-architecture.md` listed `urls_tenant.py`; the real project-template
   file is `urls_tenants.py` (plural).

**Server-mode banners** prepended to the five files whose commands cannot run
here (`core/models.md`, `core/async-tasks.md`, `app-panel-api.md`,
`templates/app-module/README.md`, `frontend/appbuilder.md`) rather than
deleting content that remains useful as background.

### Known divergences left alone

- The source lists packages `appbuilder`/`crud`/`workflow`/`communication`,
  while `examples/tutorial_app/` in this repo still references the legacy
  `frame`/`login` packages. The modern set is correct.

## 2026-09-17 — frontend setup made a hard, ordered gate (v1.2.0)

v1.1.0 asked for a polished frontend but did not get one. Observed in a real
run (`wapp2`, Vendor Onboarding): **no `frontend/` directory was ever created**,
`static/` was empty, all three registered routes were `page_type: "crud"`, and
`backend/app/templates/app.html` was a verbatim copy of
`packages/appbuilder/templates/appbuilder/app.html` — `app_initializer_endpoint`
script block and `packages/appbuilder/js/build.<version>.js` bundle included.
No error was raised at any point.

Root cause was **ordering plus an escape hatch**, not missing instructions:

- The frontend was sub-step **5d of 5**, after the `app` module (5a) and route
  registration (5b/5c), described in the same register as those. It read as an
  enhancement to an already-working app.
- 5a was reached while no `frontend/` existed, so its own text — *"Load the
  appbuilder bundle only as an interim"*, and
  *"`packages/appbuilder/templates/appbuilder/app.html` is a working
  reference"* — made copying the platform shell the sanctioned move. Nothing
  ever brought the agent back to replace it.

| Change | Detail |
|---|---|
| STEP 5 title + intro | "Make the app reachable" → "**Build the frontend** and make the app reachable". Adds an ordered sub-step table and states that the order is load-bearing. |
| **Sub-steps reordered** | Was 5a app module → 5b routes → 5c menus → 5d frontend → 5e login. Now **5a scaffold → 5b custom pages → 5c branded login → 5d build → 5e app module → 5f routes and menus**. `app.html` is now written once, after a real bundle exists. This matches the upstream interactive skill, whose STEP 5 also puts "Frontend Setup (one-time)" before the app module. |
| 5a | **New framing.** Named as the step that gets skipped, with the consequence stated. Scaffold, `.env`/`VITE_PROXY_ROUTES`, target `src/` layout and the npm allowlist all moved here from the old 5d. |
| 5e | Escape hatches removed: no "interim" bundle, and the instruction to use appbuilder's `app.html` as a reference is replaced by an explicit prohibition naming both tells (`app_initializer_endpoint`, `packages/appbuilder/js/`). Full `app.html` body now inlined rather than a 3-line fragment. |
| 5f | Adds: an app whose routes are *all* `page_type: "crud"` has no custom frontend. The `appbuilder_config_url` UNAVAILABLE branch now skips only 5f — it previously read as licence to skip frontend work too. |
| Verify gate | **New.** Six booleans at the end of STEP 5, including the two `app.html` string tells. |
| `templates/app-module/README.md` | "When to create this" section added (after 5a–5d, never before) with the same prohibition. `{{BUILD_FILE}}` instruction now says to read the name off disk and shows the finished tag. |
| STEP 7 + Critical rules | Report the bundle filename and quote `app.html`'s `src` line. New critical rule: `frontend/` missing at end of run means the frontend was not built. |

Not changed: `entity-360.md`, `auth-login.md`, `design-system.md` — their
content was never the problem; they were simply never reached.

## 2026-09-16 — polished frontend & branded login (v1.1.0)

Node is now guaranteed in the Agent Mode runtime (the platform installs it if
absent), which invalidates the assumption behind most of the original frontend
delta. The server copy now asks for *more* frontend than the interactive skill,
not less.

| Change | Detail |
|---|---|
| `SKILL.md` header + description | Node stated as available; appbuilder's shell described as the floor, not the target. v1.0.0 → v1.1.0. |
| STEP 3 UX decisions | Rewritten. Focus objects (inbound `ZForeignKey` **and** worked on directly) get full-page entity-360 views with child tables. No cap — the agent justifies its selection. Adds a per-role landing page and the branded login as standing requirements. |
| STEP 5 intro | 5a–5e all mandatory; the "only when genuinely needed / if Node is available" hedge is gone. |
| **STEP 5a** | **Bug fix.** It instructed `app.html` to load appbuilder's prebuilt bundle and said "you are not building your own". With a custom frontend that silently discards every custom page and the login, with no error. Now serves the app's own `js/zango-app.<ts>.min.js`, and requires `AnonymousUsers` on `AppView`/`RedirectAppView`. |
| STEP 5d | "Do not scaffold a frontend just because you can" deleted, along with the Node-unavailable branch. Adds the expected `frontend/src` layout. |
| STEP 5e | **New.** Branded login, always. |
| STEP 7 + Critical rules | Report which bundle is served, entity-360 selection and its justification, server-side child filtering, and which of the three login paths were verified. |
| Server-mode banners (5 files) | Corrected, not deleted: Bash is still read-only, but the "npm/npx cannot run, Node is unavailable" claim was false. |

### New references (written here first)

- `references/frontend/entity-360.md`
- `references/frontend/auth-login.md`
- `references/frontend/design-system.md`

These have **no upstream counterpart**. They are deliberately written to be
portable — nothing in them is server-mode-specific — so they should be
contributed back to the interactive skill once proven in a real run. Until
then this is the only copy.

Two corrections captured in them that the rest of the docs get wrong:

1. Child-table scoping is `get_table_data_queryset()` on the **table class**
   (reading `self.crud_view_instance.request`). `BaseCrudView` has no
   `get_queryset()`; overriding that name silently no-ops and leaves child
   tables unfiltered — a cross-record data leak.
2. `customMainDetail` receives **camelCase** props (`generalDetails`,
   `workflowDetails`). The long snake_case example in `frontend/crud.md` is for
   `customDrawerDetail` only; copying it into `customMainDetail` renders a
   blank page with no error.

### `zango-requirements-analyst`

Phase 1 previously talked users *out* of custom UI ("a fully custom-designed
screen would take much longer than the rest of the app put together"), directly
contradicting Phase 2's new defaults. That example and the "steer away from
custom React" note are removed; the question table now asks what else belongs
on an entity's page (which becomes its child tabs) and collects product name
and brand colours for the login screen.

## Keeping it in sync

This copy is the source of truth for Agent Mode. When the interactive skill
changes, re-apply the delta above rather than copying over it.
