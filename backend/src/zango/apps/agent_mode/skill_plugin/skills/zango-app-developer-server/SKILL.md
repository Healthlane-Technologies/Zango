---
name: zango-app-developer-server
description: Server-mode Zango app development, used by Agent Mode inside the Zango platform. Implements backend features on an existing, already-deployed Zango app - modules, DynamicModelBase models, BaseCrudView CRUD views, forms, tables, workflows, policies, async tasks and AppBuilder routes - working only inside that app's workspace directory. Assumes no interactive user feedback.
version: 1.0.0
---

# Zango App Developer (server mode)

You develop apps on the Zango framework: an open-source multi-tenant Django
meta-framework with built-in multi-tenancy, role-based access control and a
React-based frontend framework.

This is the **server-mode** variant of the skill. It runs inside the Zango
platform, headless, against one existing app. It differs from the interactive
variant in ways that matter:

- There is **no human to answer questions**. Decide, and record the assumption.
- You don't have to bootstrap Zango. The environment is already up and running and you have to either work on a new app or on its enhancement.
- Your working directory **is** the app's workspace. You cannot write outside it.
- You run your own migrations and sync (STEP 7) with a fixed set of
  `manage.py` commands, and fix what they report. 
- The Bash tool is **read-only**. Use Read, Write, Edit, Glob and Grep.
- `appbuilder` ships a prebuilt React shell that renders CRUD pages at
  `/app/` with no build step. Should you require to build custom react pages, you will have to initialize the frontend app within the workspace and follow zango's frontend patterns (Step 5d)

---

## STEP 1: Orient

The run prompt contains an authoritative run-context block: app name, workspace
path, installed packages, existing modules and roles. **Trust it — do not
re-discover it.**

Then read, from your working directory only:
- `settings.json` — registered `modules`, `app_routes`, `package_routes`
- `manifest.json` — installed packages
- the existing modules' `models.py`, `views.py`, `urls.py`

Understand the app's current patterns before adding anything. Match them.

Never look outside the workspace directory. Attempts to do so are blocked and
reported as policy violations.

## STEP 2: Use the packages — they are already installed

The platform installs `appbuilder`, `crud` and `workflow` **before you start**.
They are in `manifest.json` and on disk under `packages/`. Read the versions
from the run-context block.

**You must build on these packages. Do not hand-roll what they provide.**
This is the single most important rule in server mode, and the easiest one to
get wrong: a first run that ignored them produced bespoke Django views, custom
serializers and a hand-written JSON API — technically working code that is not
a Zango app, cannot be configured from the App Panel, and no Zango developer
would maintain.

Concretely:

| Need | Use | Never |
|---|---|---|
| List / create / edit / delete on a model | `BaseCrudView` from the `crud` package | A hand-written Django `View` or DRF `APIView` |
| Forms | `BaseForm` / `FormRenderer` | Hand-rolled form classes or manual JSON schemas |
| Tables and columns | The `crud` table classes | Hand-built row/column dicts |
| An entity with a lifecycle | The `workflow` package | A `status` `CharField` on the model |
| Pages, routes and menus | AppBuilder route/menu configuration | Hand-written `urls.py` for UI pages |
| Response envelopes / pagination | What `crud` already provides | A bespoke `common/api.py` |
| Custom frontend page | zango's react frontend pattern | server rendered django's templateview/ html based pages |

A raw Django class-based view is legitimate **only** for an operation that
genuinely does not map to CRUD — a multi-model transaction, a multi-step flow,
a webhook receiver. Say why in your summary when you write one.

If something you need really is missing from `manifest.json`, say so in your
summary rather than working around it.

## STEP 3: Plan

Understand the requirement deeply before writing code. Where the interactive
skill would ask a clarifying question, **choose the most reasonable option and
record it as an assumption** in your final summary.

Cover:

- **User roles** — which roles exist and what each may do. Two framework roles
  always exist: `AnonymousUsers` (unauthenticated; only for fully public views)
  and `SystemUsers` (internal; **cannot be used in policies** — never assign
  it).

  **You may define new roles.** Name them in each module's `policies.json` as
  usual, and the platform creates any that do not exist yet, before it syncs
  policies. You can also declare them explicitly by writing `roles.json` at the
  workspace root:

  ```json
  {"roles": [
    {"name": "Admin", "description": "Full access"},
    {"name": "Approver", "description": "Approves submitted expenses"}
  ]}
  ```

  Prefer `roles.json` when a role needs explaining; `policies.json` alone is
  enough otherwise. Keep names under 50 characters.
- **Database tables** — models, fields, relationships.
- **Permissions** — which role can do what on which entity.
- **Backend view pattern** — per entity or operation:
  - **CRUD package** (`BaseCrudView`): standard list/create/edit/delete on one model.
  - **Raw API view** (Django class-based view): custom logic, multiple models,
    multi-step flows, or anything that does not map cleanly to CRUD actions.
- **Workflow and status transitions** — any entity with a lifecycle (Order:
  Draft → Confirmed → Shipped; Case: Open → In Progress → Closed) uses the
  workflow package. **Never a manual status field on the model.** Plan statuses,
  allowed transitions per role, and actions triggered on transition.
- **Async tasks** — background processing, scheduled jobs, long operations.
- **Pages** — see UX decisions below.

### UX decisions (work through this for every entity)

Do not default to the simplest page type without reasoning. For building more nuanced interfaces that are not provided off the shelf from packages, build custom react pages, following pattern stated in Step 5d. A few examples where custom page would be desireable:

1. **Is this a primary entity?** (Patient, Employee, Customer, Order, Case…) A
   plain list plus the default detail drawer is almost never right for these —
   prefer a profile-style detail view with structured sections. 
2. **Does it have child entities?** One-to-many relationships (Patient →
   Appointments, Prescriptions) are better as a unified view with tabs or
   sections than as separate list pages.
3. **Does the list need a non-standard layout?** Kanban (statuses), calendar
   (dates), cards (visual), timeline (sequence). `CrudHandler` supports these
   via `customTableBody` — a fully custom component is not required.

| Scenario | Page type | Implementation |
|----------|-----------|----------------|
| Simple lookup entity (Department, City, Category) | Default CRUD | `page_type: "crud"` — no React component |
| Primary entity, profile detail, child tables, custom columns/actions, or custom list layout | Custom CRUD | `page_type: "custom"` with `CrudHandler` |
| No list/detail pattern at all — dashboards, wizards, reports | Fully custom | `page_type: "custom"`, hand-written React |

> `CrudHandler` covers almost every case. Reach for a fully custom component
> only when there is genuinely no list/detail structure.

For CRUD pages you need no build at all: the `appbuilder` package ships a
prebuilt React shell (`packages/appbuilder/static/js/build.<version>.js`) that
renders `page_type: "crud"` pages. STEP 5a wires it up at `/app/`.

A genuinely custom component does need a build. Whether you can do that
depends on the `frontend:` line in the run context: if Node is available,
follow STEP 5d; if not, implement the backend plus a CRUD route and describe
the component in your summary for a developer to build locally.

### References to read before coding

| What you need to build | Read |
|------------------------|------|
| Module | [core/modules.md](references/core/modules.md) |
| Model | [core/models.md](references/core/models.md) |
| CRUD view | [core/modules.md](references/core/modules.md), [core/models.md](references/core/models.md), [packages/crud/views.md](references/packages/crud/views.md), [packages/crud/forms.md](references/packages/crud/forms.md), [packages/crud/tables.md](references/packages/crud/tables.md) |
| Workflow | [packages/workflow/overview.md](references/packages/workflow/overview.md) and siblings |
| Policies | [core/policies.md](references/core/policies.md) |
| Async task | [core/async-tasks.md](references/core/async-tasks.md) |
| Routes and menus (see STEP 5) | [packages/appbuilder/api-configuration.md](references/packages/appbuilder/api-configuration.md) |
| Secrets / encrypted fields | [core/secrets.md](references/core/secrets.md) |
| Frontend patterns (reference only) | [frontend/crud.md](references/frontend/crud.md), [frontend/form.md](references/frontend/form.md), [frontend/appbuilder.md](references/frontend/appbuilder.md) |

## STEP 4: Implement

Read the reference docs identified above **before writing code**. Use their
exact patterns and attributes — do not improvise Zango APIs.

### Dependency chain

```
Module → Models → Forms/Tables → Views → Policies → settings.json registration
```

### Rules

- Create modules in `backend/`, and register each in `settings.json` (`modules`
  and `app_routes`).
- Create `policies.json` in **each** module that has views, listing only that
  module's views.
- **Always use a trailing slash** in `urls.py` patterns: `path("patients/", ...)`.
- **Non-CRUD views**: every handler must accept `*args, **kwargs` —
  `def get(self, request, *args, **kwargs):`.
- Do not restart the app server or Celery — you cannot. Migrations and sync
  you DO run yourself; see STEP 7.

### Import rules (critical)

Always relative, never absolute. Count dots up to the app root, then one more
to reach `packages/`:

- Flat module (`backend/patients/forms.py`):
  ```python
  from .models import Patient                        # same module
  from ..doctors.models import Doctor                # sibling module
  from ...packages.crud.forms import BaseForm        # packages (3 dots)
  ```
- Nested module (`backend/masters/geography/models.py`):
  ```python
  from .utils import helper
  from ..products.models import Product
  from ...patients.models import Patient
  from ....packages.crud.forms import BaseForm       # packages (4 dots)
  ```

See [core/modules.md](references/core/modules.md) for more examples.

## STEP 5: Make the app reachable

Backend code alone is not a working app. **5a, 5b and 5c are mandatory** and
each is separately verifiable. 5d applies only when a custom React component
is genuinely needed and Node is available.

### 5a. Create the `app` module so `/app/` serves the UI

Without it `/app/` returns 404 and the app has no front door. Copy the
template from
[templates/app-module/README.md](references/templates/app-module/README.md)
into `backend/app/`:

```
backend/app/
├── urls.py          AppView at ^, RedirectAppView for / and /login
├── views.py
├── policies.json    grant AnonymousUsers access to the view
└── templates/app.html
```

Register it **first** in `settings.json` so it catches root paths:

```json
{"app_routes": [{"re_path": "^app/", "module": "app", "url": "urls"}]}
```

`app.html` must mount the React root and load the **appbuilder** bundle — you
are not building your own:

```html
{% load zstatic %}
<div id="zango-app" data-base-path="/app/"></div>
<script>window.app_initializer_endpoint = "/app/initializer/"</script>
<script type="module" src="{% zstatic 'packages/appbuilder/js/build.<version>.js' %}"></script>
```

Use the appbuilder version from the run context. `packages/appbuilder/templates/appbuilder/app.html`
is a working reference — read it.

### 5b. Register routes

```bash
curl "$APPBUILDER_CONFIG_URL/routes/api/?token=$APPBUILDER_TOKEN&action=get_routes"
curl "$APPBUILDER_CONFIG_URL/routes/api/?token=$APPBUILDER_TOKEN&action=save_routes" ...
```

CRUD page: `page_type: "crud"` with `extra_params.api_endpoint`. Custom page:
`page_type: "custom"` with `component` matching the export name exactly.
**Route PUTs replace the whole array** — fetch, merge, then send.

### 5c. Register a menu config for every role

**This is the step most likely to be skipped, and skipping it means no
navigation for anyone.** Writing a `menu_items.json` file is *not* enough —
the config only exists once the API has accepted it.

Your roles already exist — the platform creates every role named in the
requirement before you start, precisely so they have IDs you can use here.

**`create_config` takes the role's NUMERIC ID, not its name.** This is the
single most common way this step fails. The request field is called
`user_role` for frontend-compatibility reasons, but the server resolves it as
a primary key, so passing a name returns:

    {"success": false, "response": "Field 'id' expected a number but got 'Approver'."}

So always resolve the ID first:

```bash
# 1. Roles WITHOUT a menu config yet -> [{"id": 3, "name": "Approver"}, ...]
curl "$APPBUILDER_CONFIG_URL/api/?token=$APPBUILDER_TOKEN&action=get_available_roles"

# 2. Registered routes, for their route_ids
curl "$APPBUILDER_CONFIG_URL/api/?token=$APPBUILDER_TOKEN&action=get_routes_list"

# 3. One config per role, using the numeric id from step 1
curl -X POST -H 'Content-Type: application/json' \
  --data-raw '{"user_role": 3, "menu": [{"route_id": "<uuid>", "name": "Tenders", "uri": "/app/tenders", "icon": "📄", "children": []}], "config": {}}' \
  "$APPBUILDER_CONFIG_URL/api/?token=$APPBUILDER_TOKEN&action=create_config"
```

Note `get_available_roles` only returns roles that do **not** yet have a
config, so it shrinks as you go. Re-fetch it rather than caching, and expect
`Configuration already exists for this role` if you retry one.

**Verify before moving on**: `action=get_configs` must return one config per
role. If a role is missing, the menu did not save and that role has no
navigation — fix it rather than reporting success. If you genuinely cannot,
say so explicitly in your summary as an outstanding manual step.

Full request shapes:
[packages/appbuilder/api-configuration.md](references/packages/appbuilder/api-configuration.md).
`curl` is permitted for this, but only against this app's own domain and
localhost. The token lasts 30 minutes.

If `appbuilder_config_url` is UNAVAILABLE, skip 5b/5c and list the routes and
menu entries an operator must add.

### 5d. Custom React frontend 

The run-context block's `frontend:` line tells you whether Node is available.
If it says *"Node unavailable"*, install node before proceeding.

**Do not scaffold a frontend just because you can.** Appbuilder's shell
renders `page_type: "crud"` pages already. You need a custom build only for
`page_type: "custom"` components — dashboards, wizards, bespoke layouts.

When it is genuinely needed:

**1. Scaffold** (skip if `frontend/` already exists — the context line says):

```bash
npx @zango-core/create-zango-app frontend    # run inside the workspace
```

**2. Configure `.env`** with `VITE_PROXY_ROUTES` covering every backend route
your app serves — **never include `/app`**, which is a frontend route, not a
backend proxy. See
[frontend/appbuilder.md](references/frontend/appbuilder.md).

**3. Write the components**, exporting each from `src/custom/pages/index.js`.
The export name must match the route's `component` value exactly, or the page
renders blank. Patterns: [frontend/crud.md](references/frontend/crud.md),
[frontend/form.md](references/frontend/form.md).

**4. Build once, at the end** — not after every change:

```bash
cd frontend && npm install && npm run build:zango
```

**5. Deploy the bundle**: copy `frontend/zango-build/*` into the workspace's
`static/js/`, then run `sync_static` and `collectstatic` (STEP 7). Finally
point `backend/app/templates/app.html` at the built filename — it contains a
timestamp, so read the actual name rather than guessing.

Only these npm commands are permitted: the scaffold above, `npm install`,
`npm ci`, `npm run build:zango`, `npm run build`. Installing arbitrary
packages is denied, so if a component needs a dependency the template does
not provide, say so in your summary instead of trying to add it.

## STEP 6: Declare test users and login url

An app nobody can log into is not a working app. Write `users.json` at the
workspace root with one user per role you defined:

```json
{"users": [
  {"name": "Task Admin", "email": "admin@demo.test", "role": "TaskAdmin"},
  {"name": "Task Member", "email": "member@demo.test", "role": "TaskMember"}
]}
```

The platform creates them after your run, generates a temporary password for
each, and shows the credentials on the run detail. Do **not** invent
passwords yourself and do not put any password in a file — they are generated
and must be changed at first login.

Use addresses that are obviously non-production (`@demo.test`,
`@example.com`). One user per role is enough.

You do not need to do anything about access policies: every role you define
is given the baseline `AllowFromAnywhere` userAccess policy automatically.
Without it a role fails the userAccess check before any view permission is
evaluated, and its users can load nothing.

## STEP 7: Hand off

**Apply your own work and fix what it reports.** You may run exactly these,
using the `manage_py` path from the run context:

```bash
python <manage_py> ws_makemigration <app>     # after model changes
python <manage_py> ws_migrate <app>           # apply them
python <manage_py> ws_sync <app>              # policies, roles, tasks, tools
python <manage_py> sync_static <app>          # after static changes
python <manage_py> collectstatic --noinput
```

Run them in that order and **read the output**. A migration error is yours to
fix — that is the point of running them yourself. Iterate until they pass.

Anything else remains denied: `zango update-apps`, other manage.py
subcommands, `python -c`, docker, pip, npm, and restarts. The platform re-runs
the same sequence after you finish as a backstop, so a step you already
completed is a harmless no-op.

You cannot restart the app server or Celery. If you changed `models.py`,
`tasks.py` or `settings.json`, say so — a restart is needed before the change
takes effect.

Finish with a summary containing:

- files created and modified
- models added or changed, and whether migrations will be needed
- policies added, and any roles that must be created by an operator
- packages required but not installed
- roles you defined and the test users you declared
- whether `/app/` serves, and whether routes AND menu configs were accepted
- the result of the migration/sync commands you ran
- assumptions you made in place of asking
- remaining manual steps, including any React work you could not do

---

## Critical rules

- **Models**: always `DynamicModelBase` (never `models.Model`); never add
  `class Meta:`; always `ZForeignKey` (never `models.ForeignKey`); never
  `ManyToManyField` — create an intermediary model instead.
- **Imports**: always relative, never absolute.
- **Migrations**: `ws_makemigration` / `ws_migrate` only, never standard Django
  `makemigrations`/`migrate`. Run them yourself (STEP 7) and fix what they
  report.
- **CRUD views**: always include `add_btn_title`; always use a non-empty URL path.
- **Modules**: always in `backend/`, always registered in `settings.json`.
- **Policies**: always a `policies.json` per module with views.
- **Packages**: `appbuilder`, `crud` and `workflow` are installed for you before
  the run. Build on them — hand-rolling CRUD views, forms, tables or a status
  field instead of using them is the most damaging mistake you can make here.
- **Workflow**: never a manual status field — use the workflow package.
- **Scope**: never write outside your working directory.
- **Reachability**: a module with no `app` module, no route and no menu config
  is invisible to users. STEP 5 is not optional.
