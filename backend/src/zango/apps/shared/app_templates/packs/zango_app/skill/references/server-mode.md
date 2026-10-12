# Server mode: building inside the Zango platform (Agent Mode)

When the Zango platform runs this skill (Agent Mode, "Commit for build"), the build is split
between the **platform** and **you**. The platform runs every deterministic script of this skill
itself, with its own Python, before and after your turn. You only write code. This file overrides
the phases in `SKILL.md` wherever they conflict.

You cannot run Python, `cp`/`mkdir`/`mv`, migrations, the zango CLI or the platform API. Your Bash
is read-only except the npm/npx commands listed below. Write every file with Write/Edit.

## What the platform has already done when you start

| Skill phase | Done by the platform |
|---|---|
| Phase 0 Preflight | The app and its workspace exist; appbuilder, crud and workflow are installed. No environment detection, no credentials, no `/etc/hosts`. |
| Phase 1 Parse and lint | `spec_check.py` ran on the approved spec. `.zas/` is written: `spec.resolved.json`, `spec.ui.json`, `plan.md`, `holes.md`, `issues.md`, `test_plan.md`. Read them directly. A spec with errors never reaches you. |
| Phase 2 Runtime | `backend/zas_core/` is copied in, `spec.json` is current, `zas_core` is registered in `settings.json`, `selftest_runtime.py` passed. |
| Phase 6 steps 1–3 | When the run context says the frontend is prepared: `frontend/` is scaffolded, crud 2.0.0 + lucide-react 1.31.0 are pinned, the crud patch is applied with `patch-package`, `frontend/src/zas/`, `frontend/src/custom/spec.ui.json` and `frontend/src/index.css` are in place, and `lucide_icons.py` wrote `icons.gen.ts` + `.zas/menu_icons.json`. When it says the frontend phase is skipped, do the backend only and say so in your summary. |

On an **update** build (the run context says so), `hooks.py`, `tasks.py`, `slots/`, `.zas/holes.md`
and `.zas/test_users.json` are yours from the previous build: keep them and regenerate the rest.

## What you do

1. **Phase 3, every module in `plan.md` order**: `models.py`, `forms.py`, `workflow.py`,
   `detail.py` (heroes), `tables.py`, `views.py`, `urls.py`, `policies.json`, `hooks.py`/`tasks.py`
   (stubs first), `__init__.py`; register each module in `settings.json` `modules` + `app_routes`.
   You cannot `py_compile`: read your files back and be exact about imports and names.
2. **Phase 4, every hole in `.zas/holes.md`** by `references/custom-code.md`, with the
   `# zas:hole H-NN` marker and a status. You cannot run `--audit-holes`; the platform runs it after
   you finish and sends you what it reports.
3. **Phase 6 steps 4–6** (only when the frontend is prepared): `src/custom/pages/index.ts`, `src/App.tsx`,
   slots and `slots/index.ts`, then
   - `npx --no tsc --noEmit` and `npm run build:zango` (run from `frontend/`; `--no` keeps npx
     from downloading a package when typescript is missing),
   - deploy the build with exactly `cp -r frontend/zango-build/. static/js/` (the one permitted copy;
     remove nothing — the platform publishes static files),
   - the `app` module from `assets/templates/app-module/` with the build file name in `app.html`,
     its `app_routes` entry **last**.
   `npm install` (no arguments) is allowed if you need to restore `node_modules`.

   **The `app` module is mandatory whenever the frontend is prepared** — without it nothing serves
   `/app` and the build has no UI. Before you finish, make sure all of this holds; the platform checks
   exactly this (`app_shell`) and sends you back if any of it is missing:
   - `backend/app/` has `urls.py`, `views.py`, `policies.json` and `templates/app.html`;
   - `settings.json` has `{"name": "app", "path": "backend.app"}` in `modules` and
     `{"module": "app", "re_path": "^", "url": "urls"}` in `app_routes`;
   - `app.html` names the real build file (`zango-app.<timestamp>.min.js`, never `{{BUILD_FILE}}`),
     that file is in `static/js/`, and it was built after your last change to `frontend/src/`.
   **Declared list views.** When `.zas/views.md` lists any, the spec declares views (a kanban
   board, cards, a calendar, a timeline) on a list page that this runtime has no component for.
   Write each as a custom view, exactly as `references/views.md` says, **before** the type-check
   and build. The user approved those views in the preview: a build without them is not done, and
   the platform checks each one (`views`).
4. **Phase 7 step 1**: `.zas/test_fixtures.py` and `.zas/test_scenarios.py` from `.zas/test_plan.md`.
5. Finish with a summary: modules written, holes and their status, anything you could not do and why.

## What the platform does after you finish

In this order, each step recorded on the run:

1. `zango_platform.py roles`, `ws_makemigration`, `prune_first_migration.py` (first build only),
   `ws_migrate`, `zango_platform.py sync`, `schedule`, `users`, `check`, `sync_static` + `collectstatic`,
   `zango_platform.py appbuilder`. It signs in with a short-lived service account that exists only
   for the run.
2. The `app_shell` check above, the `views` check (every view in `.zas/views.md` is built), `spec_check.py --audit-holes`, then the test layers: `design --only lint`, `api`, `ui`, `design`,
   `scenarios`, and `report` (`.zas/build_report.html` / `.md`). Layers the platform cannot run in its
   environment (for example no Playwright) are reported as skipped, never as passed.

## Fix rounds

If a bring-up step, the hole audit or a test layer fails, the platform resumes your session with a
short digest: the failing step or check ids, their spec paths and details. Fix the cause where it is
(generated code, hook, slot, fixture), never by editing a test, the runtime in `backend/zas_core/`,
`packages/` or the spec. Then stop; the platform re-runs only the failing groups. There are at most
a couple of rounds, so fix everything the digest lists in one go.
