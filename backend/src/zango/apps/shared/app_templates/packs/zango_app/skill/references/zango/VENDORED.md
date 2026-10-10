# references/zango — vendored Zango docs (provenance)

**Source:** agent-mode skill `zango-app-developer-server/references/` in the Zango repo
(`backend/src/zango/apps/agent_mode/skill_plugin/skills/`). It is a superset of the
interactive `zango-app-developer` plugin's references: the CRUD and frontend docs are
split finer and carry fixes from live runs.
**Vendored:** 2026-10-09. **Pinned to:** backend `crud` 1.0.17, `workflow` 1.0.1,
`appbuilder` (api-configuration as of the source date), frontend `@zango-core/crud` **2.0.0 from npm**
(pinned in every app by `references/setup.md` §4; the scaffold's default 1.0.13-rc.11 is not supported).
When a doc and the installed package disagree, the package source wins. Check
`<ws>/packages/<pkg>/` and `frontend/node_modules/@zango-core/*`, then fix the doc here.

## What is here, and when this skill reads it

| Path | Read when |
|---|---|
| `packages/crud/` (overview, views/, tables/, forms/, detail.md) | writing or debugging a CrudView, ModelTable, form or BaseDetail that the `map/*.md` rules do not cover |
| `packages/workflow/` (statuses, transitions, tags, advanced, utils) | writing `workflow.py`, debugging a transition/tag that does not show or does not fire |
| `packages/appbuilder/` | registering routes/menus (`scripts/zango_platform.py appbuilder` does it, and this is its reference) |
| `core/` (models, modules, policies, async-tasks, secrets) | models/migrations, module wiring, `policies.json`, Celery tasks, secrets |
| `frontend/crud/`, `frontend/form.md`, `frontend/workflow.md` | changing `zas/*` runtime or writing a slot that uses `@zango-core/crud` directly |
| `frontend/appbuilder.md`, `frontend/auth-login.md` | `App.tsx`, custom pages registration, the login page |
| `app-panel-api.md` | creating roles, test users, syncing policies/tasks via the App Panel API |
| `zango-architecture.md` | the workspace layout and multi-tenant model |
| `entity-360.md`, `child-tables.md` | **rewritten for this skill** (not verbatim). They describe `ZasDetail`, `Detail360.tsx` and the parent parameter |

The `map/*.md` files say what this skill generates. These files say how Zango
works. If they conflict, `map/*.md` and `contracts.md` win, because the runtime
(`zas_core`, `zas/*`) already handles what the generic docs leave to the developer.

## The two rewritten files

- `entity-360.md`: from agent-mode `references/frontend/entity-360.md` (written from real broken runs).
  There, the agent hand-writes every 360 page; here `ZasDetail` (backend) and `Detail360.tsx` (frontend)
  implement each rule once, so the file became a map of "pitfall → where the runtime handles it → what
  not to break". The source's `patient__uuid` / `Vehicle.objects.filter(uuid=…)` became `object_uuid`.
- `child-tables.md`: from agent-mode `packages/crud/tables/advanced.md` (*Custom Table Queryset*),
  `packages/crud/forms/core.md` (*The parent FK on a child-tab form*) and `frontend/entity-360.md` §4,
  rewritten for the zas runtime. The source's `__uuid` lookups became `__object_uuid`.

## Also ported from the interactive `zango-app-developer` plugin (1.1.0)

So this skill never has to invoke that skill:

- `bootstrap-templates.md`: verbatim (docker and venv environment files and commands). The one link
  to the plugin's "Capability 1" now points to `references/setup.md`.
- `app-module.md`: the plugin's `templates/app-module/README.md`. Its nonexistent
  `zango manage-app … sync_policies` command was replaced with `zango_platform.py sync`.
- The plugin's procedures (choose setup mode, create the app, set the domain, install packages in order,
  add roles to `AllowFromAnywhere`, run manage.py per mode, sync static, restart Celery) are now
  `references/setup.md` + `scripts/zango_env.py` + `scripts/zango_platform.py` (`app`, `packages`, `roles`).
- Not ported: `ai-agents.md` (the spec has no AI features).

## Changes made while vendoring

- Removed the "Server-mode note (Agent Mode)" banners from `core/models.md`,
  `core/async-tasks.md`, `app-panel-api.md` and `frontend/appbuilder.md`. Here the developer's machine
  runs docker/zango CLI/npm normally.
- Re-pointed links to `SKILL.md STEP n` and to `frontend/entity-360.md`
  (now `entity-360.md` at this level).
- `packages/crud/forms/core.md`: `Vehicle.objects.filter(uuid=…)` changed to `object_uuid=…`
  (`DynamicModelBase` has no `uuid` field).
- Not vendored: `frontend/design/*`, `shared-primitives.md`, `assets/shared.tsx` and
  `verify-gate.md`. This skill uses its own design system (`zas/tokens.css`,
  `design-system.md`) and its own test gate (`testing.md`). `handoff-summary.md` is
  also left out because it is agent-mode only.

## Known source issues (not fixed in the text; the runtime works around them)

- `BaseDetail.get_sections` (used only when `Meta.sections` is set) looks the object up by `?pk=`
  through `get_object`, which expects an `object_uuid`. Generated detail classes never set
  `Meta.sections`. The 360 layout comes from `data.zas` (`ZasDetail.zas_payload`).
- Mutating a `ModelField` on a form instance mutates the class-level field shared by all
  instances. Always `copy.copy()` first (`ZasFormMixin` does).
