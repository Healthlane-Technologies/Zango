# Setup: the Zango environment, the app, and how commands run

This skill is self-contained: it sets up what it needs itself. Read this in Phase 0, and whenever a
command has to run inside Zango. Exact file templates for a new environment:
`references/zango/bootstrap-templates.md`. App Panel endpoints: `references/zango/app-panel-api.md`.

## 1. Is there a Zango platform, and how is it run?

```bash
python3 <skill>/scripts/zango_env.py health                       # platform answering on :8000?
python3 <skill>/scripts/zango_env.py detect --project <project dir>   # docker or venv → .claude/zango-config.json
```

`detect` reads `.claude/zango-config.json` from the project dir or a parent. If the file is missing,
it works out the mode and writes it:

- **docker**: a running `app` service in the `docker_compose.yml` next to the project dir
  (the `deploy/` folder, mounted at `/zango`).
- **venv**: exactly one virtualenv with `bin/zango` in or next to the project.

If it can't decide (exit 2), that's one of the few questions this skill asks: "Docker, or which
virtualenv?" Then write the file:
`{"setup_mode": "docker"}` or `{"setup_mode": "venv", "venv_path": "/abs/path"}`.

**No platform at all** (health fails and there is no project): bootstrap one, following
`references/zango/bootstrap-templates.md`. Docker mode is the default; use venv only if the user asks.

| Step | Docker mode | Venv mode |
|---|---|---|
| prerequisites | `docker --version`, `docker compose version` | Python 3.10+, Docker (for Postgres/Redis) |
| files | `deploy/.env`, `deploy/Dockerfile`, `deploy/init.sh`, `deploy/docker_compose.yml` | `deploy/docker_compose_db.yml`, `deploy/.env` (venv variant); `python3 -m venv <venv> && <venv>/bin/pip install zango` |
| start | `chmod +x deploy/init.sh; export HOST_UID=$(id -u) HOST_GID=$(id -g); docker compose -f deploy/docker_compose.yml up -d --build` | `docker compose -f deploy/docker_compose_db.yml up -d`, then `<venv>/bin/zango start-project <PROJECT> --db_name=… --platform_username=… …`, then `cd <PROJECT> && <venv>/bin/python manage.py runserver 0.0.0.0:8000` (a long-running process: start it in the background and say so) |
| ready | poll `zango_env.py health` until it says up (first build takes minutes) | same |

Defaults (no need to ask): project `zango_project`, platform admin `platform_admin@zango.dev` /
`Zango@123`, Postgres `zango_admin` / `zangopass` / `zango`. They are written to `deploy/.env`,
which `zango_platform.py` reads (`PLATFORM_USERNAME`, `PLATFORM_USER_PASSWORD`).

**Platform credentials elsewhere** (a custom install without `deploy/.env`): pass
`PLATFORM_USERNAME` / `PLATFORM_USER_PASSWORD` as environment variables, or `--user/--password`.
If none are available, ask for them once. They are never written to the repo or printed.

## 2. The app

```bash
python3 <skill>/scripts/zango_platform.py app --project <project dir> --name <app.code> [--domain <host>]
```

This command:

- creates the app if it is missing (App Panel API, async; polls until it is deployed)
- sets its domain (default `<app code without _>.local`)
- installs **appbuilder → crud → workflow** in that order, re-reading the version lists before each
  install (workflow's list changes after crud is installed), then checks `manifest.json`
- prints the workspace: `<project dir>/workspaces/<app.code>`

If the domain does not resolve, it prints the `/etc/hosts` line to add (`127.0.0.1 <domain>`).
Adding it needs sudo, so ask the user to add it, then continue. Test users and the browser tests use
`http://<domain>:8000`.

An app that already exists is reused as is. `zango_platform.py packages --workspace <ws>` installs
only what is missing.

## 3. Running commands inside Zango

Never type `docker compose exec …` or `<venv>/bin/python …` by hand. Use:

| Need | Command |
|---|---|
| a manage.py command | `zango_env.py manage --workspace <ws> -- ws_makemigration <app>` (also `ws_migrate <app>`) |
| the zango CLI | `zango_env.py zango --workspace <ws> -- update-apps --app_name <app>` (syncs policies and tasks; the App Panel API route `zango_platform.py sync` does the same) |
| static files after a frontend build | `zango_env.py static --workspace <ws>` (`sync_static <app>` + `collectstatic --noinput`) |
| Celery after `tasks.py` or schedules change | `zango_env.py celery --workspace <ws>` (docker: restarts the worker; venv: prints the command, which is a manual step to report) |

Only `ws_makemigration` / `ws_migrate`, never `makemigrations` / `migrate`. Logs: docker:
`docker compose -f <deploy>/docker_compose.yml logs app --tail 200`; venv: the runserver terminal.

## 4. The frontend scaffold (once per app)

```bash
cd <ws> && npx @zango-core/create-zango-app frontend
cd <ws>/frontend && npm install --save-exact --legacy-peer-deps @zango-core/crud@2.0.0 lucide-react@1.31.0
grep '"version"' node_modules/@zango-core/crud/package.json   # must print 2.0.0 (require('…/package.json') is not exported)
mkdir -p patches && cp <skill>/assets/frontend/patches/*.patch patches/
npm install --save-dev --legacy-peer-deps patch-package && npm pkg set scripts.postinstall=patch-package && npx patch-package
cp <skill>/assets/templates/frontend/index.css src/index.css
```

**Two crud 2.0.0 gaps the skill fixes in every app** (keep both on re-runs):
- `patches/@zango-core+crud+2.0.0.patch`: the table sends `order[0][column]` from the columns it shows
  (the package looked in an empty `columns` prop, so header clicks only sorted the loaded page).
- `src/index.css`: `@source "../node_modules/@zango-core/crud/dist"` + colour names, because the package
  ships Tailwind class names without CSS (no brand on primary buttons, black borders on controls).

**Pinned frontend versions.** The `zas` runtime is type-checked and built against these npm packages:
`@zango-core/crud` **2.0.0** (npm `latest`), `@zango-core/appbuilder` 1.0.0-rc.1, `@zango-core/components`
^0.2.1, `lucide-react` 1.31.0, React 18.3.1. `create-zango-app` (2.0.2) installs crud `1.0.13-rc.11` and no
`lucide-react`, so the second command is required, on new and existing frontends alike. `--legacy-peer-deps`
is needed because appbuilder 1.0.0-rc.1 still declares a peer of crud `^1.0.13-rc.11`. Don't use a local
`zango-core-crud-*.tgz` build: it may differ from the npm 2.0.0.

In `frontend/.env`, set `VITE_PROXY_ROUTES` to `/api,/zango,/appbuilder,/crud,/workflow,` plus every
module URL prefix (`/vendors,/procurement,…`). **Never `/app`**: that is a frontend route.
Build: `npm run build:zango` → `frontend/zango-build/zango-app.<ts>.min.js`. Copy it to `<ws>/static/js/`
(remove older builds), put its name in `backend/app/templates/app.html`, then run `zango_env.py static`.
The `app` module (serves the React shell): `assets/templates/app-module/` and
`references/zango/app-module.md`. Background on `ZangoApp` / `customPages`: `references/zango/frontend/appbuilder.md`.
