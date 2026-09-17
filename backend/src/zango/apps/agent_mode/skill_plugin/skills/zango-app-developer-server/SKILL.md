---
name: zango-app-developer-server
description: Server-mode Zango app development, used by Agent Mode inside the Zango platform. Implements backend and frontend features on an existing, already-deployed Zango app - modules, DynamicModelBase models, BaseCrudView CRUD views, forms, tables, workflows, policies, async tasks, AppBuilder routes, custom React pages, entity-360 detail views with child tables, and a branded login page - working only inside that app's workspace directory. Assumes no interactive user feedback.
version: 1.2.0
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
- The Bash tool is **read-only**, except the `manage.py` commands in STEP 7 and
  the npm commands in STEP 5a and 5d. Otherwise use Read, Write, Edit, Glob and Grep.
- **Node is available** — the platform guarantees it. You build a real frontend
  (STEP 5a-5d) and serve your own bundle (STEP 5e).
- `appbuilder` ships a prebuilt React shell that renders `page_type: "crud"`
  pages with no build step. It is the floor, not the target: focus objects get
  full-page entity-360 views with child tables, each role gets a landing page,
  and **every app gets a branded login**. See STEP 3 and STEP 5.

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

**The first version must already look like a product.** Node is available, so a
custom frontend is always within reach: an app whose every page is the default
CRUD shell is an incomplete first version, not a safe one.

Decide per entity, in this order.

**1. Is it a focus object?** Read the FK graph. An entity qualifies when *other
models declare a `ZForeignKey` to it* **and** *a user works on it directly* —
Patient, Order, Case, Employee, Customer, Program. These get an **entity-360**
page: a full-page route showing identity, key facts, and each related record set
as a **child table inside a tab**. A Patient page shows that patient's Orders,
Programs and Documents; it does not make the user visit three menu items and
filter by hand.

There is **no fixed cap** — decide from the app's own shape how many entities
qualify, and justify the selection in your summary. A lookup table never
qualifies, however many FKs point at it.

**2. Is it a primary entity with no children yet?** A profile-style custom
detail page, without tabs.

**3. Does the list need a non-standard layout?** Kanban (statuses), calendar
(dates), cards (visual), timeline (sequence). `CrudHandler` supports these via
`customTableBody` — a fully custom component is not required.

**4. Is it a lookup entity?** Department, City, Category, Document Type, Status
master — something referenced from dropdowns but never opened and worked on.
Default CRUD. Custom work here is waste.

| Scenario | Page type | Implementation |
|----------|-----------|----------------|
| Focus object (inbound FKs + worked on directly) | Entity-360 | `page_type: "custom"`, full-page route + child tables — [frontend/entity-360.md](references/frontend/entity-360.md) |
| Primary entity, no child relations | Custom detail | `page_type: "custom"` with `CrudHandler` |
| Non-standard list layout | Custom CRUD | `page_type: "custom"`, `CrudHandler` + `customTableBody` |
| Dashboard, report, wizard — no list/detail shape | Fully custom | `page_type: "custom"`, hand-written React |
| Lookup entity (Department, City, Category) | Default CRUD | `page_type: "crud"` — no React component |

Also plan, for every app:

- **A landing page per role.** Never drop a user on a raw list as their home.
  A small dashboard — what is mine, what is overdue, what needs action — is
  usually the right first screen.
- **A branded login page.** Always. See STEP 5c.

Detail-view mechanics, child tables and the failure modes that make them break
are in [frontend/entity-360.md](references/frontend/entity-360.md). The visual
bar every custom page must meet — tokens, states, responsive floor — is in
[frontend/design-system.md](references/frontend/design-system.md). Read both
before writing components.

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
| Detail view with child tables | [frontend/entity-360.md](references/frontend/entity-360.md) |
| Branded login / custom auth screens | [frontend/auth-login.md](references/frontend/auth-login.md) |
| Visual quality bar, tokens, states | [frontend/design-system.md](references/frontend/design-system.md) |
| Frontend patterns | [frontend/crud.md](references/frontend/crud.md), [frontend/form.md](references/frontend/form.md), [frontend/appbuilder.md](references/frontend/appbuilder.md) |

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

## STEP 5: Build the frontend and make the app reachable

Backend code alone is not a working app. **Every sub-step 5a–5f is mandatory**
and each is separately verifiable. Node is available — the platform guarantees
it — so none of the frontend sub-steps is optional or conditional.

**Do them in this order.** The order is load-bearing: the frontend is
scaffolded and built *before* `app.html` is written, so `app.html` is written
once, already pointing at a bundle that exists. Writing the app module first
is what leads to it being left on appbuilder's prebuilt shell forever.

| | Sub-step | Produces |
|---|---|---|
| 5a | Scaffold `frontend/` | `frontend/` with `src/custom/` |
| 5b | Write the custom pages | entity-360, landing pages |
| 5c | Brand the login page | `AppLoginCard.tsx` |
| 5d | Build the bundle | `frontend/zango-build/zango-app.<ts>.min.js` |
| 5e | Create the `app` module | `backend/app/` + `app.html` → your bundle |
| 5f | Register routes and menus | navigation for every role |

### 5a. Scaffold the frontend — FIRST, before any of the rest

**This is the step that gets skipped, and skipping it makes every later
frontend instruction unreachable.** If `frontend/` does not exist at the end of
your run, the app has no custom frontend, no entity-360 page and no branded
login, regardless of what else you did.

Skip **only** if `frontend/` already exists in the workspace — check, do not
assume:

```bash
npx @zango-core/create-zango-app frontend    # run inside the workspace root
```

Then configure `frontend/.env` with `VITE_PROXY_ROUTES` listing every backend
route your app serves (`/api`, `/appbuilder`, plus each CRUD module route).
**Never include `/app`** — that is a frontend route, not a backend proxy. See
[frontend/appbuilder.md](references/frontend/appbuilder.md).

Target layout:

```
frontend/src/
├── custom/
│   ├── auth/
│   │   └── AppLoginCard.tsx     branded login (5c)
│   └── pages/
│       ├── <Entity>Detail.tsx   entity-360 pages (5b)
│       ├── Dashboard.tsx        per-role landing page (5b)
│       └── index.js             export names MUST match route.component
└── App.tsx                      authConfig + customPages wiring
```

Only these npm commands are permitted: the scaffold above, `npm install`,
`npm ci`, `npm run build:zango`, `npm run build`. Installing arbitrary
packages is denied, so if a component needs a dependency the template does
not provide, say so in your summary instead of trying to add it.

### 5b. Write the custom pages

Under STEP 3's defaults essentially every app needs these: focus objects get
full-page entity-360 views with child tables, and each role gets a landing
page. Appbuilder's prebuilt shell renders only `page_type: "crud"` pages, so
anything beyond a plain lookup table requires your own build.

Export every page from `src/custom/pages/index.js`. **The export name must
match the route's `component` value exactly**, or the page renders blank.

Patterns: [frontend/entity-360.md](references/frontend/entity-360.md),
[frontend/crud.md](references/frontend/crud.md),
[frontend/form.md](references/frontend/form.md).

### 5c. Brand the login page

**Every app gets a branded login page. Always** — there is no toggle and no
condition. It is the first screen anyone sees, and the framework default says
nothing about the product.

Full contract and a copyable skeleton:
[frontend/auth-login.md](references/frontend/auth-login.md). In short:

- Register a full override —
  `authConfig={{ customComponents: { LoginPage: AppLoginCard } }}` on
  `ZangoApp`. Pass the **component**, not an element.
- **Never hand-roll auth.** Render the framework's own `PasswordLoginForm`,
  `RoleSelection` and `PasswordResetRequired` inside your layout. Rolling your
  own POST loses SAML, password policy, rate limiting and role selection.
- Drive the flow from `PasswordLoginForm`'s `onSuccess`, **not**
  `LoginContext.onLogin` (which mis-handles the single-role case), and
  normalise `next_step` across its four response shapes.
- **Layout is the split-screen archetype**: left = brand mark, product name and
  a headline naming the domain outcome (hidden below 880px); right = the auth
  form in a card. Re-theme it and rewrite the copy — do not invent a different
  layout. Keep the "Powered by Zelthy" attribution.
- **Copy must name this app's real domain outcome**, taken from the
  requirement spec — never generic filler like "Welcome, please sign in".
- Use only the brand name, tagline and palette the spec or app theme supplies.
  **Never reproduce a real third-party company's branding, logo or trade
  dress**; if the spec names a real organisation, use its name as plain text
  and nothing more.
- Inline `<style>` and inline SVG only — no new packages, no external fonts,
  no CDN.

### 5d. Build the bundle — once, at the end of frontend work

Not after every change:

```bash
cd frontend && npm install && npm run build:zango
```

This writes `frontend/zango-build/zango-app.<timestamp>.min.js`. Copy
`frontend/zango-build/*` into the workspace's `static/js/`, then run
`sync_static` and `collectstatic` in STEP 7.

**Read the built filename off disk** — it carries a build timestamp, so never
guess it:

```bash
ls frontend/zango-build/
```

### 5e. Create the `app` module so `/app/` serves the UI

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

`app.html` mounts the React root and loads **your** bundle — the one you built
in 5d, whose real filename you just read off disk:

```html
{% load zstatic %}
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>{{ APP_NAME }}</title>
  </head>
  <body>
    <div id="zango-app" data-base-path="/app/"></div>
    <script type="module" src="{% zstatic 'js/zango-app.<timestamp>.min.js' %}"></script>
  </body>
</html>
```

> **Do not copy `packages/appbuilder/templates/appbuilder/app.html`.** It is
> the platform's own shell, not a template for your app. Copying it gives you
> an `app_initializer_endpoint` script block and
> `{% zstatic 'packages/appbuilder/js/build.'|add:build_version|add:'.js' %}` —
> appbuilder's prebuilt bundle. Your custom pages and your branded login are
> not in that bundle. **Nothing errors.** The app renders the stock CRUD UI and
> the entire frontend looks like it was never built.
>
> The two tells that this has gone wrong: `app.html` contains the string
> `app_initializer_endpoint`, or it contains `packages/appbuilder/js/`. If
> either is true at the end of your run, the frontend is not being served —
> fix it before you finish.

**`policies.json` must grant `AnonymousUsers`** on both `AppView` and
`RedirectAppView`. Without it the login page 403s before it can be shown —
nobody, including you, can reach the app.

`RedirectAppView` maps `/` and `/login` to `/app`; the React router owns
`/app/login`, which is where your branded login renders (5c).

### 5f. Register routes and menu configs

#### Routes

```bash
curl "$APPBUILDER_CONFIG_URL/routes/api/?token=$APPBUILDER_TOKEN&action=get_routes"
curl "$APPBUILDER_CONFIG_URL/routes/api/?token=$APPBUILDER_TOKEN&action=save_routes" ...
```

CRUD page: `page_type: "crud"` with `extra_params.api_endpoint`. Custom page:
`page_type: "custom"` with `component` matching the export name exactly.
**Route PUTs replace the whole array** — fetch, merge, then send.

**An app whose routes are all `page_type: "crud"` has no custom frontend.**
Every entity-360 page and every landing page you wrote in 5b must appear here
as `page_type: "custom"`. If none do, you skipped 5a–5b.

#### Menu configs — one per role

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

If `appbuilder_config_url` is UNAVAILABLE, skip 5f and list the routes and
menu entries an operator must add. Do NOT skip 5a-5e because of it - the
frontend build does not depend on the config API.

### Verify STEP 5 before moving on

All six must be true. Any that is false is a bug in your run, not a nice-to-have:

1. `frontend/` exists in the workspace.
2. `frontend/zango-build/zango-app.<ts>.min.js` exists and was copied to `static/js/`.
3. `backend/app/templates/app.html` references `js/zango-app.` and contains **neither** `app_initializer_endpoint` **nor** `packages/appbuilder/js/`.
4. At least one registered route has `page_type: "custom"`.
5. `/app/login` renders your branded card.
6. Every role has a menu config accepted by the API.

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
- whether `frontend/` was scaffolded and built, and the exact bundle filename
- whether `/app/` serves **your own bundle** (not appbuilder's) — quote the
  `src` line from `app.html` — and whether routes AND menu configs were accepted
- which entities got an entity-360 page, and why each remaining model did not
- that every child table is filtered **server-side**, not just by query string
- whether the branded login is live, and which of the three login paths
  (single-role, multi-role, first-login) you verified
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
- **Frontend setup**: scaffolding `frontend/` is STEP 5a and runs **before**
  the `app` module and before route registration. If `frontend/` does not
  exist at the end of the run, the frontend was not built — no amount of
  backend work substitutes for it.
- **Bundle**: `app.html` must load **your** bundle (`js/zango-app.<ts>.min.js`)
  and must never contain `app_initializer_endpoint` or
  `packages/appbuilder/js/`. Never copy
  `packages/appbuilder/templates/appbuilder/app.html`. Leaving `app.html` on
  appbuilder's prebuilt shell silently discards every custom page and the
  branded login, with no error.
- **Frontend defaults**: focus objects get full-page entity-360 views with child
  tables; every role gets a landing page; every app gets a branded login. An app
  that is default CRUD throughout is an incomplete first version.
- **Child tables**: always filter the child queryset server-side in
  `get_table_data_queryset()`. A query-string filter alone lets any user read
  another parent's records.
- **Auth**: never hand-roll a login POST. Wrap the framework's auth components.
