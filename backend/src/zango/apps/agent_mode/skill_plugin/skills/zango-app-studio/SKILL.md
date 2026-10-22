---
name: zango-app-studio
description: Build a complete Zango app from a Zango App Studio spec (app_spec.yaml, spec_version 1) - models, CRUD pages, workflows, policies, role menus, entity-360 detail pages, custom logic from plain-language items, branded frontend in the Studio's design system, and API + Playwright + design tests. Use when the user gives an App Studio YAML / "app spec" / "zango_app_spec" and asks to build, generate, regenerate or update the app from it, or to re-run the build after editing the spec. Self-contained: it also sets up the Zango environment and the app if they don't exist yet. Does not use other skills.
---

# Zango App Studio → app

> **Running inside the Zango platform** (Agent Mode): read `references/server-mode.md` first; it
> overrides the phases below.

You turn one App Studio spec into a running Zango app whose screens match the Studio preview.
The spec is the contract: what each role may see and do is defined there, and the tests prove it.

**Nobody approves anything mid-build.** Decide, record the decision in the build log, and
report it at the end. Ask the user only for the things in "Ask only these" below.

## How the skill is built (read once)

- `scripts/spec_check.py` normalises and lints the YAML, and writes `.zas/` with everything later
  phases read: `spec.resolved.json` (never re-read the YAML), `spec.ui.json`, `holes.md`,
  `plan.md`, `issues.md`.
- A **runtime** is copied into the app: `backend/zas_core/` (expressions, access and row scoping,
  sequences, duplicates, app-user logins, the 360 payload, and the mixins every generated class
  uses) and `frontend/src/zas/` (design tokens, components, list page, 360 page, dialogs, login).
  Both read their configuration from the spec copy (`backend/zas_core/spec.json`,
  `frontend/src/custom/spec.ui.json`).
- So **the code you generate is thin and declarative**: classes with `zas_entity = "<code>"`,
  columns, fields and dicts copied from the resolved spec. Behaviour comes from the runtime, and
  prose items become **holes** (hooks/slots) you implement in Phase 4.
- Names, URLs, hook signatures, payload shapes: `references/contracts.md`. It wins over everything else.

## Layering

| Concern | Owner |
|---|---|
| Zango environment (docker/venv), creating the app, packages, running manage.py | `references/setup.md`, `scripts/zango_env.py`, `scripts/zango_platform.py app` |
| How Zango/crud/workflow/appbuilder work | `references/zango/` (vendored package docs, see `VENDORED.md`) |
| Spec → code rules | `references/map/*.md`, `references/contracts.md` |
| Runtime + design system | `assets/backend/zas_core/`, `assets/frontend/zas/`, `references/design-system.md` |
| Platform calls (app, packages, roles, sync, schedules, users, routes, menus) | `scripts/zango_platform.py` |
| Tests and report | `scripts/zas_test/`, `references/testing.md`, `references/report.md` |

`<skill>` below is this skill's directory, and `<ws>` is the app workspace
(`<project dir>/workspaces/<app>`). Every manage.py / zango CLI command goes through
`python3 <skill>/scripts/zango_env.py manage|zango --workspace <ws> -- <args>`, which runs it the right way
for docker or venv (`references/setup.md` §3). Never type `docker compose exec` or a venv path yourself.
This skill never invokes another skill. Log every step: `python -m zas_test.log --workspace <ws> --phase N --step "…" --status ok|fail|skip --detail "…"`
(run from `<skill>/scripts`).

## Ask only these (then never again)

1. The spec file, if not given.
2. Which Zango project, if more than one candidate exists and nothing in the request picks one.
   A missing app is created (`zango_platform.py app`), not asked about.
3. Docker or which virtualenv, only if `zango_env.py detect` can't tell (exit 2).
4. Platform admin credentials, only if there is no `deploy/.env` and no `PLATFORM_USERNAME`/`PLATFORM_USER_PASSWORD` env vars.
5. Adding `127.0.0.1 <domain>` to `/etc/hosts` (needs sudo), only if the app's domain doesn't resolve.

Everything else is decided: the checker's suggested fix for a lint error that is a pure typo,
guesses for vague prose (hole status `needs-review`), external systems (stub + `blocked`).
**Exception:** spec errors that change meaning (an unknown role, a link to a missing entity,
an expression that cannot be resolved) stop the build. Report them with the YAML path and the
checker's fix. Do not guess intent.

## Phase 0: Preflight (environment and app; `references/setup.md`)

1. **Python for the skill's scripts.** In venv mode, use the Zango venv's interpreter (`venv_path` in
   `.claude/zango-config.json`, e.g. `<venv>/bin/python`) wherever this file says `python3`. It already
   has Django, PyYAML, requests and Pillow. Add only what's missing, without upgrading Zango's packages:
   `<venv>/bin/python -m pip install playwright` (check first with `pip list`), then
   `<venv>/bin/python -m playwright install chromium`. In docker mode, use a host Python with
   `pip install pyyaml requests django playwright pillow`.
2. **Platform:** `python3 <skill>/scripts/zango_env.py health`. If nothing answers and there is no Zango
   project, bootstrap one (setup.md §1, templates in `references/zango/bootstrap-templates.md`;
   docker by default). Then `zango_env.py detect --project <project dir>`. Exit 2 is ask-list item 3.
3. **App:** `python3 <skill>/scripts/zango_platform.py app --project <project dir> --name <app.code>`
   creates it if missing, sets the domain, installs appbuilder → crud → workflow, and prints `<ws>`.
   For an existing app: `settings.json` `app_name` must equal the spec's `app.code` (else it's a
   different app: stop and say so), and `zango_platform.py packages --workspace <ws>` adds any missing
   package (crud 1.0.17+, workflow 1.0.1+).
4. **Re-run?** If `<ws>/.zas/spec.resolved.json` exists, this is an **update**: keep `hooks.py`, `tasks.py`,
   `slots/`, `.zas/holes.md` and `.zas/test_users.json`, and regenerate everything else.

## Phase 1: Parse and lint

```bash
python3 <skill>/scripts/spec_check.py <spec.yaml> --workspace <ws>
```

Exit 1 means errors: fix only pure typos the checker pinpoints (and say so), otherwise stop and
report. Read `.zas/plan.md` (module order, names, pages per role) and `.zas/holes.md`.
Reference: `references/spec/schema.md`, `references/spec/expressions.md`.

## Phase 2: Runtime

```bash
cp -R <skill>/assets/backend/zas_core <ws>/backend/zas_core      # replace on re-run
cp <ws>/.zas/spec.resolved.json <ws>/backend/zas_core/spec.json
python3 <skill>/scripts/selftest_runtime.py --workspace <ws>      # expression engine + spec load, offline
```

Register `{"name": "zas_core", "path": "backend.zas_core"}` in `settings.json` `modules` (it has
a model, `ZasSequence`, and no URLs). Never edit files under `zas_core/` in the app. A runtime bug
is fixed in `<skill>/assets/` and copied again, and the report lists it.

## Phase 3: Backend, module by module (`plan.md` order)

For each module, from `spec.resolved.json`, write in this order:

| File | Rules | Example |
|---|---|---|
| `models.py` | `references/map/models.md` | `references/examples/vendors/models.py` |
| `forms.py` | `references/map/forms.md` | `…/forms.py` |
| `workflow.py` | `references/map/workflow.md` | `…/workflow.py` |
| `detail.py` (heroes only) | `references/map/detail-views.md` | `…/detail.py` |
| `tables.py`, `views.py`, `urls.py` | `references/map/tables.md` | `…/tables.py` … |
| `policies.json` | `references/map/access.md` | `…/policies.json` |
| `hooks.py`, `tasks.py` | header from `assets/templates/hooks.py.tmpl`; **stubs only** in this phase (`raise NotImplementedError`), so imports work | |
| `__init__.py` | empty | |

Register each module in `settings.json` `modules` + `app_routes` (`re_path: "^<module url>/"`).
Imports from packages use three dots (`from ...packages.crud.base import BaseCrudView`).
After each module: `python3 -m py_compile` on every file. Generic Zango questions:
`references/zango/` (start at `packages/crud/README.md`, `packages/workflow/README.md`, `core/README.md`).

## Phase 4: Custom code (holes)

Implement every row of `.zas/holes.md` by `references/custom-code.md`: exact name and signature,
`# zas:hole H-NN` marker, status `done | needs-review | blocked | covered`. Slots go in
`frontend/src/custom/slots/` (written in Phase 6, after the scaffold exists). Then:

```bash
python3 <skill>/scripts/spec_check.py <spec.yaml> --workspace <ws> --audit-holes   # must exit 0 before Phase 7
```

## Phase 5: Bring-up

```bash
S=<skill>/scripts
python3 $S/zango_platform.py roles --workspace <ws>       # create missing roles; all roles → AllowFromAnywhere
python3 $S/zango_env.py manage --workspace <ws> -- ws_makemigration <app>
python3 $S/prune_first_migration.py <ws>/migrations/0001_initial.py   # first build only
python3 $S/zango_env.py manage --workspace <ws> -- ws_migrate <app>
python3 $S/zango_platform.py sync --workspace <ws>        # App Panel API: sync policies + tasks
python3 $S/zango_platform.py schedule --workspace <ws>    # cron from `# zas:schedule` lines in tasks.py
python3 $S/zango_platform.py users --workspace <ws>       # one test user per role → .zas/test_users.json
python3 $S/zango_platform.py check --workspace <ws>       # roles ↔ policies read back
```

Fix every error in the generated code, never by editing packages or the database. Restart Celery
if `tasks.py` or schedules changed (`zango_env.py celery --workspace <ws>`). Then run the API layer once (`python -m zas_test.api --workspace <ws>`) to
catch backend bugs before the frontend exists.

## Phase 6: Frontend

1. Scaffold if `frontend/` is missing: `npx @zango-core/create-zango-app frontend` in `<ws>`, and set
   `.env` `VITE_PROXY_ROUTES` (setup.md §4; never `/app`). Background: `references/zango/frontend/appbuilder.md`.
   **Then pin the packages the runtime is built for** (the scaffold installs crud 1.0.13-rc.11 and no lucide):
   `cd <ws>/frontend && npm install --save-exact --legacy-peer-deps @zango-core/crud@2.0.0 lucide-react@1.31.0`
   (`--legacy-peer-deps` because appbuilder 1.0.0-rc.1 still declares crud `^1.0.13-rc.11`). Check with
   `grep '"version"' node_modules/@zango-core/crud/package.json` → `2.0.0` (`require('…/package.json')` fails: not exported). Do this on re-runs too.
   **Then apply the crud 2.0.0 patch** (server-side sort: the package looks the sorted column up in an empty
   `columns` prop, sends no `order[0][…]` and sorts only the loaded page in the browser):
   `mkdir -p patches && cp <skill>/assets/frontend/patches/*.patch patches/ && npm install --save-dev --legacy-peer-deps patch-package`,
   add `"postinstall": "patch-package"` to `package.json` scripts, then `npx patch-package` (prints the applied patch).
2. `cp -R <skill>/assets/frontend/zas <ws>/frontend/src/zas`,
   `cp <ws>/.zas/spec.ui.json <ws>/frontend/src/custom/spec.ui.json` and
   `cp <skill>/assets/templates/frontend/index.css <ws>/frontend/src/index.css` (replaces the scaffold's).
   `index.css` makes Tailwind scan `@zango-core/crud/dist`: crud 2.0.0 ships class names, not CSS, so without it
   primary buttons have no brand background and bordered controls get black `currentColor` borders.
   (`zas/index.ts` imports `tokens.css`; nothing to add to the entry files.)
3. `python3 <skill>/scripts/lucide_icons.py --workspace <ws>` (icons.gen.ts + `.zas/menu_icons.json`).
4. `src/custom/pages/index.ts` and `src/App.tsx` from `assets/templates/frontend/` (keep the
   scaffold's `appInitializerEndpoint`; add the shell props when the bundle has a `/shell` screen,
   custom-code.md §The app shell). One export per page (`references/map/pages-menus.md`).
5. Slots for `custom_page` / `custom_tab` / `custom_panel` holes from `Slot.tsx.tmpl`, exported in
   `slots/index.ts` (`references/custom-code.md` §Slots). A hole that names `.zas/bundle/screens/…`
   was approved in the preview: port its `sketch.js` onto the zas kit, block for block
   (`references/custom-code.md` §Porting a sketch; start from `.zas/bundle/index.md`).
6. `npx tsc --noEmit && npm run build:zango`, copy `frontend/zango-build/zango-app.<ts>.min.js` to `<ws>/static/js/` (remove older builds), then add the `app`
   module from `assets/templates/app-module/` (`app.html` with the build file name,
   `app_routes` `{"module": "app", "re_path": "^", "url": "urls"}` **last**; `references/zango/app-module.md`),
   then `python3 <skill>/scripts/zango_env.py static --workspace <ws>`.
7. `python3 <skill>/scripts/zango_platform.py appbuilder --workspace <ws>`: routes + per-role menus
   with SVG icons, merged and read back. It fails loudly. Never report an app with unsaved routes.
8. `python -m zas_test.design --workspace <ws> --only lint` must pass.

List pages and 360 related tabs render `ZasTable` (the preview's toolbar, table, pager), and rows
without a 360 open `RecordDrawer` (the preview's drawer: status, primary transitions, fields, activity).
Both use the crud endpoints but not crud's `CrudHandler` UI, whose crud 2.0.0 header/toolbar/drawer
don't match the preview (and drop `headerProps.customLeftActions/customRightActions`). Forms still use crud's
`FormRenderer` (`dialogs.tsx`). Details: `references/design-system.md` §Lists and drawers.

## Phase 7: Verify and report

1. **Write the test intelligence** from `.zas/test_plan.md` (written by `spec_check`): `.zas/test_fixtures.py`
   for every "Fixture needs" item, and `.zas/test_scenarios.py` with one `@scenario` per hole under
   "Scenarios to write" (templates in `assets/templates/tests/`, rules in `references/testing.md` §Fixtures, §Scenarios).
   Read the `intent` findings `spec_check` printed and carry any real contradiction to the final message.
2. Run the layers:

```bash
python -m zas_test.api       --workspace <ws>  # access matrix, CRUD, transitions, tags, row actions, rules, 360 payload
python -m zas_test.ui        --workspace <ws>  # Playwright headless, per role, generated from the spec
python -m zas_test.design    --workspace <ws>  # lint, gallery goldens, tokens, design tree, layout sanity
python -m zas_test.scenarios --workspace <ws>  # behaviour of every plain-language item (Claude-written)
python -m zas_test.report    --workspace <ws>  # .zas/build_report.html (polished, self-contained) + .md
```

Run them from `<skill>/scripts` (or with it on `PYTHONPATH`). What each layer proves and how to read failures: `references/testing.md`.
3. **Fix loop.** For each failure: find the cause (generated code, hook, slot, runtime, fixture, environment),
   fix it there, re-run only that group (`--only`). At most 3 rounds per failure; then report it. Never edit a
   test to pass, never change the spec's meaning, never mark a skip as passed. Prove at least the riskiest
   scenario can fail (break the hook, `--only H-NN`, restore). Final message: the
`build_report.md` summary (verdict, URL, test users without passwords, holes needing attention,
manual steps) + the HTML path. Rules: `references/report.md`.

## Critical rules

- **Generated classes are declarative.** Never hand-write `can_perform_row_action_*`,
  `process_row_action_*`, `<transition>_condition/_done`, `get_table_data_queryset`,
  `fetch_item_details` or form `clean()` for spec rules. The mixins do these. Logic goes in holes.
- **Copy from `spec.resolved.json`, don't retype.** Role names, transition names, keys and labels must
  match the spec exactly, because the runtime looks them up by name.
- Models: `DynamicModelBase`, `ZForeignKey(<class>, related_name="+")`, no `Meta`, no M2M, no `status` field.
- Every write path is scoped by role (`access.in_scope`). Don't bypass it with `Model.objects.get(object_uuid=…)` in hooks
  that act on user-supplied ids. Use the scoped queryset.
- Frontend: compose from `src/zas` only. No hex colours or colour styles in `src/custom/`, except in the
  slot of a screen approved in the preview, which reproduces its sketch (custom-code.md §Porting a sketch).
- Match what the user approved: every screen in `.zas/bundle/index.md` has screenshots, and the platform
  blocks writing its file until you have Read them. Custom screens are ported from their sketch; standard
  screens are arranged with their levers only: the switcher's place (`makeViewsPage(…, { switcher })`,
  views.md §Matching the approved page) and the shell's logo, user card and top bar (`ZangoApp` props in
  `src/App.tsx`, components in `src/custom/shell/`, custom-code.md §The app shell).
- Never edit `packages/`, the runtime inside the app, or the database by hand. Fix the generated code,
  the runtime in the skill (`assets/`), or report a spec problem.
- Never print or commit passwords or tokens. `.zas/test_users.json` is chmod 600.
- A check you skipped is reported as skipped, with the reason. Never as passed.

## Reference index

| Need | Read |
|---|---|
| names, URLs, hooks, payloads, `data-zas` | `references/contracts.md` |
| spec keys / expressions | `references/spec/schema.md`, `references/spec/expressions.md` |
| spec → models / forms / tables / workflow / access / 360 / pages+menus | `references/map/<topic>.md` |
| prose → hooks and slots | `references/custom-code.md` |
| 360 pitfalls / child tables | `references/zango/entity-360.md`, `references/zango/child-tables.md` |
| look and feel | `references/design-system.md` |
| tests / report | `references/testing.md` (layers, intent review, fixtures, scenarios), `references/report.md` |
| a full worked module | `references/examples/vendors/` |
| environment, app, running commands | `references/setup.md` |
| Zango packages (crud, workflow, appbuilder), core, frontend libs, App Panel API, bootstrap templates | `references/zango/` |
| regression spec | `evals/vendor_hub.yaml`, expectations in `evals/expected.md` |
