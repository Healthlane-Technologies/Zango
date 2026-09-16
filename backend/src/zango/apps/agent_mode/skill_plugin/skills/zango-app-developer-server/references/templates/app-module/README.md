> **Server-mode note (Agent Mode).** Commands in this file that use
> `docker compose` or the `zango` CLI **cannot be run** in server mode, and
> Bash is otherwise read-only. Treat those as background reference.
> Two exceptions: the **npm commands allowed by STEP 5d** (scaffold, install,
> build) do run — Node is available — and you run the **`manage.py` commands
> listed in STEP 7** (migrations, sync, static) yourself.

# App Module Template

This template provides the necessary files for creating an "app" module in Zango that serves the frontend React application.

## Structure

```
backend/app/
├── urls.py          # URL routing for app views
├── views.py         # AppView and RedirectAppView
├── policies.json    # Access policies for views
└── templates/
    └── app.html     # HTML template that loads the React app
```

## Purpose

The app module serves as the entry point for your React frontend application. It:
- Renders the HTML template that loads the React app bundle
- Handles redirects from `/` and `/login` to `/app`
- Provides the necessary Django views and URL routing

## Setup Steps

### 1. Create the app module

Create the `backend/app/` directory with all template files from this reference.

### 2. Add to settings.json

Add the app module route to `settings.json`:

```json
{
  "app_routes": [
    {
      "re_path": "^",
      "module": "app",
      "url": "urls"
    }
  ]
}
```

**Important**: This should be the FIRST route in `app_routes` to catch all root-level paths.

### 3. Build and Deploy Frontend

After frontend setup is complete:

#### Build the React app:
```bash
cd frontend
npm run build:zango
```

This creates `frontend/zango-build/zango-app.<timestamp>.min.js`

#### Copy build to static directory:
```bash
# From workspace root
cp -r frontend/zango-build/* static/js/
```

#### Sync static files:
```bash
docker compose -f deploy/docker_compose.yml exec app bash -c "cd <PROJECT_NAME> && python manage.py sync_static <app_name> && python manage.py collectstatic --noinput"
```

#### Update app.html with build filename:
Replace `{{BUILD_FILE}}` in `backend/app/templates/app.html` with the actual build filename (e.g., `zango-app.1768223010381.min.js`).

### 4. Sync policies

After creating the app module, sync policies:

```bash
# (server mode) The platform syncs policies for you after the run finishes.
# Do not run anything here. The CLI equivalent, for reference only, is:
#   python manage.py ws_sync <app_name>
# (An earlier version of this doc named a `manage-app` subcommand that the
#  zango CLI has never had.)
```

## Notes

- The build file uses a timestamp in the filename for cache busting
- After each new build, you need to:
  1. Copy the new build file to `static/js/`
  2. Sync static files with `sync_static` and `collectstatic` commands
  3. Update the filename in `app.html`
- The `RedirectAppView` ensures users accessing `/` or `/login` are redirected to `/app`
- Policies allow `AnonymousUsers` access - adjust roles as needed for your app
