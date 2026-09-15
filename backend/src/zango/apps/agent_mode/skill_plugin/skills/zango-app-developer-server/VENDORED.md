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

## Keeping it in sync

This copy is the source of truth for Agent Mode. When the interactive skill
changes, re-apply the delta above rather than copying over it.
