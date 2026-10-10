# Zango Framework Architecture Reference

## What is Zango

Zango is an open-source multi-tenant Django meta-framework for building custom business applications. It extends Django with built-in multi-tenancy, role-based access control, a permission framework, and a package ecosystem for rapid development.

## Multi-Tenancy Model

- Each "app" in Zango is a tenant with its own PostgreSQL schema
- Apps share the same Django project but have isolated data
- A "platform" layer manages all apps (accessible at `/platform`)
- Apps are accessed via configured domain URLs

## Project Structure

```
<project_name>/
├── manage.py
├── <project_name>/
│   ├── __init__.py
│   ├── settings.py        # Imports from zango.config.settings.base
│   ├── urls.py             # Main URL router
│   ├── urls_public.py      # Public tenant URLs
│   ├── urls_tenants.py     # Tenant-specific URLs
│   ├── asgi.py
│   └── wsgi.py
└── workspaces/
    └── <app_name>/
        ├── settings.json    # App configuration (modules, routes, packages)
        ├── manifest.json    # Installed packages list
        ├── migrations/
        │   └── __init__.py
        ├── <module_name>/   # App modules
        │   ├── models.py
        │   ├── views.py
        │   ├── urls.py
        │   ├── forms.py
        │   ├── tables.py
        │   ├── workflow.py
        │   ├── tasks.py
        │   └── policies.json
        └── packages/        # Installed packages
            ├── appbuilder/
            ├── crud/
            └── workflow/
```

## App Configuration Files

### settings.json
```json
{
    "version": "1.0.0",
    "modules": [
        {"name": "module_name", "path": "module_name"}
    ],
    "app_routes": [
        {
            "re_path": "^module_name/",
            "module": "module_name",
            "url": "urls"
        }
    ],
    "package_routes": [
        {"re_path": "^app/", "package": "appbuilder", "url": "urls"},
        {"re_path": "^crud/", "package": "crud", "url": "urls"},
        {"re_path": "^workflow/", "package": "workflow", "url": "urls"}
    ]
}
```

### manifest.json
```json
{
    "packages": [
        {"name": "crud", "version": "1.0.0"},
        {"name": "workflow", "version": "1.0.0"}
    ]
}
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `zango start-project <name>` | Create a new Zango project with DB setup and platform user |
| `zango update-apps --app_name <app_name>` | Update app code, run migrations, sync policies/tasks |
| `zango install-package` | Install a package from the Zango package registry |
| `zango list-packages` | List available packages |
| `zango git-setup` | Setup Git integration for an app |

### start-project Full Syntax
```bash
zango start-project <project_name> \
  --db_name="$POSTGRES_DB" \
  --db_user="$POSTGRES_USER" \
  --db_password="$POSTGRES_PASSWORD" \
  --db_host="$POSTGRES_HOST" \
  --db_port="$POSTGRES_PORT" \
  --platform_username="$PLATFORM_USERNAME" \
  --platform_user_password="$PLATFORM_USER_PASSWORD" \
  --redis_host="$REDIS_HOST" \
  --redis_port="$REDIS_PORT" \
  --platform_domain_url="$PLATFORM_DOMAIN_URL"
```

## Core Services Required

| Service | Purpose | Default Port |
|---------|---------|-------------|
| PostgreSQL | Database (schema-per-tenant) | 5432 |
| Redis | Caching, Celery broker | 6379 |
| App (Django) | Web server | 8000 |
| Celery Worker | Async task execution | — |
| Celery Beat | Periodic task scheduling | — |

## Key Imports Reference

| Import | From | Purpose |
|--------|------|---------|
| `DynamicModelBase` | `zango.apps.dynamic_models.models` | Base class for all app models |
| `ZForeignKey` | `zango.apps.dynamic_models.fields` | Tenant-aware ForeignKey |
| `ZOneToOneField` | `zango.apps.dynamic_models.fields` | Tenant-aware OneToOneField |
| `get_current_request()` | `zango.core.utils` | Access current request from anywhere |
| `get_current_role()` | `zango.core.utils` | Get user's current role |
| `get_app_object()` | `zango.core.utils` | Get current app context |
| `BaseCrudView` | `..packages.crud.base` | CRUD view base (relative import) |
| `BaseForm` | `..packages.crud.forms` | CRUD form base |
| `BaseSimpleForm` | `..packages.crud.forms` | Non-model form base |
| `ModelField` | `..packages.crud.form_fields` | CRUD form field |
| `ModelTable` | `..packages.crud.table.base` | CRUD table base |
| `ModelCol` | `..packages.crud.table.column` | Table column definition |
| `WorkflowBase` | `..packages.workflow.base.engine` | Workflow base class |
| `shared_task` | `celery` | Async task decorator |

## Core Packages

| Package | Purpose |
|---------|---------|
| `appbuilder` | Complete React-based frontend framework with dynamic routing, themes, and CRUD pages |
| `crud` | CRUD views, forms, tables — rapid data management UI |
| `workflow` | Status-based workflow engine with transitions |
| `communication` | Communication and notification system |

## DynamicModelBase Built-in Fields

Every model extending `DynamicModelBase` automatically gets:
- `id` — Auto-incrementing primary key
- `created_at` — Timestamp, auto-set on creation
- `created_by` — ForeignKey to AppUserModel, set on creation
- `modified_at` — Timestamp, auto-updated on save
- `modified_by` — ForeignKey to AppUserModel, set on save
- `object_uuid` — UUID, unique identifier

## Permission System

- **Permissions**: Auto-generated from views and models. Synced via App Panel.
- **Policies**: Group permissions together. Defined in `policies.json` per module.
- **Roles**: Assigned to users. Roles have policies attached.
- **Row-level security**: Via `RestrictedQuerySet` on model queries.

## App Lifecycle

1. App is launched via the Platform App Panel (`/platform`)
2. Domain is configured for the app
3. Code is written in `workspaces/<app_name>/`
4. `zango update-apps --app_name <app_name>` syncs code: runs migrations, syncs policies, syncs tasks
5. App is accessible at configured domain

## Update Apps Flow

When `zango update-apps --app_name <app_name>` runs:
1. Install/update packages (if configured)
2. Run app migrations: `python manage.py ws_migrate <app_name>`
3. Run package migrations: `python manage.py ws_migrate <app_name> --package <pkg_name>`
4. Sync static files: `python manage.py sync_static <app_name>`
5. Sync workspace: policies, tasks
6. Execute fixtures from `release/<version>/fixtures/` if present
