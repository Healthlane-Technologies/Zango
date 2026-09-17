---
name: zango-app-developer-server
description: Server-mode Zango app development, used by Agent Mode inside the Zango platform. Implements backend and frontend features on an existing, already-deployed Zango app - modules, DynamicModelBase models, BaseCrudView CRUD views, forms, tables, workflows, policies, async tasks, AppBuilder routes, custom React pages, entity-360 detail views with child tables, and a branded login page - working only inside that app's workspace directory. Assumes no interactive user feedback.
version: 1.5.0
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
  the npm commands in STEP 5a and 5f. Otherwise use Read, Write, Edit, Glob and Grep.
- **Node is available** — the platform guarantees it. You build a real frontend
  (STEP 5a-5f) and serve your own bundle (STEP 5g).
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
- **A branded login page.** Always. See STEP 5e.

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
| Shared UI primitives (write these first) | [frontend/shared-primitives.md](references/frontend/shared-primitives.md) |
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

Backend code alone is not a working app. **Every sub-step 5a–5h is mandatory**
and each is separately verifiable. Node is available — the platform guarantees
it — so none of the frontend sub-steps is optional or conditional.

**Do them in this order.** The order is load-bearing: the frontend is
scaffolded and built *before* `app.html` is written, so `app.html` is written
once, already pointing at a bundle that exists. Writing the app module first
is what leads to it being left on appbuilder's prebuilt shell forever.

| | Sub-step | Produces |
|---|---|---|
| 5a | Scaffold `frontend/` | `frontend/` with `src/custom/` |
| 5b | **Plan the pages** | `design-plan.md` at the workspace root |
| 5c | Write the shared primitives | `src/custom/pages/shared.tsx` |
| 5d | Write the custom pages | entity-360, landing pages |
| 5e | Brand the login page | `AppLoginCard.tsx` |
| 5f | Build the bundle | `frontend/zango-build/zango-app.<ts>.min.js` |
| 5g | Create the `app` module | `backend/app/` + `app.html` |
| 5h | Register routes and menus | navigation for every role |

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
│   │   └── AppLoginCard.tsx     branded login (5e)
│   └── pages/
│       ├── <Entity>Detail.tsx   entity-360 pages (5d)
│       ├── Dashboard.tsx        per-role landing page (5d)
│       └── index.js             export names MUST match route.component
└── App.tsx                      authConfig + customPages wiring
```

Permitted npm commands: the scaffold above, `npm install`, `npm ci`,
`npm run build:zango`, `npm run build`, and installing **only** these design
packages — `echarts`, `echarts-for-react`, `recharts`, `date-fns`, `clsx`,
`tailwind-merge`. Any other package is denied; say so in your summary rather
than trying.

You do **not** need to install icons: `lucide-react` already ships with
`@zango-core`. Inter and JetBrains Mono load from Google Fonts. See
[frontend/design-system.md](references/frontend/design-system.md) §10 — the
earlier claim that fonts and icons were unavailable was wrong, and it is why
generated apps looked plain.

### 5b. Plan the pages — write `design-plan.md` before any component

**This step exists because the previous version of this skill produced pages
that satisfied every structural rule and still looked like wireframes.** The
rules below (§6 anatomy, §1a aesthetic direction) are all satisfiable
*nominally*: a page can have "two or more titled Sections" where the second
section adds nothing, tabs that carry counts of zero, and an Overview that
re-lists the same five fields already shown in the header. That page passes a
grep and fails a glance.

So before writing a single component, write `design-plan.md` at the workspace
root. It is a real file, committed to the workspace, because the verify gate
reads it back and checks the finished pages against it. A plan you only thought
about cannot be checked.

For **each focus entity**, the plan must answer all six:

1. **The question this page answers.** One sentence, in the user's words, not
   the schema's. *"Can we still bid on this, and are we ready to?"* — not
   *"shows tender fields"*. Every later decision serves this sentence. If you
   cannot write it without listing fields, you do not yet understand the
   entity well enough to design its page.

2. **The lead card.** The first thing inside Overview is **a synthesis, not a
   field dump** — a computed answer to (1), assembled from several fields plus
   derived state. A progress bar against an allowance, a countdown with a
   readiness checklist, an outstanding balance with its ageing. *Re-listing the
   key facts that are already in the header is the single most common failure
   and is never acceptable.* Name what it computes and from which fields.

3. **The layout.** Detail pages default to **main column + right rail** (§6).
   State what goes in the rail: status with who changed it and when, an
   at-a-glance block of the flat attributes, open tasks, and any
   consent/compliance state. The rail is what carries the flat fields, which is
   precisely why Overview is then free to be a synthesis.

4. **The aesthetic direction** from design-system.md §1a — one of Operational,
   Editorial, Clinical, Approval — and the **signature treatment** that makes
   it legible. "Default" is not a direction.

5. **Every tab**, with: its count source, whether it is a child table or a
   composed view, and its **empty-state copy written out in full**. Copy
   invented later at implementation time reverts to "No data".

6. **The one deliberate moment** — the single element you will execute with
   more care than the brief requires, and which you can point at afterwards.

Then one plan-level entry for the app as a whole: the **identity strip**. The
header is not a title plus a chip; it is the title plus the four to six facts
that identify this record at a glance — reference number, dates, the one
relationship that matters, contact. List them per entity.

Keep it short. Six answers per entity, a few lines each — this is a design
decision record, not a document. Write it, then build exactly it.

### 5c. Write the shared primitives — before any page

Write `src/custom/pages/shared.tsx` **first**, and compose every later page
from it. Full contract and a copyable floor:
[frontend/shared-primitives.md](references/frontend/shared-primitives.md).

It exports the layout, state and formatting primitives every page needs:
`PageShell`, `PageHeader`, `Avatar`, `IdentityStrip`, `KeyFacts`,
`FieldGrid`, `Section`, `Tabs`, `Card`, `Button`, `StatusChip`, `Skeleton`,
`EmptyState`, `ErrorState`, `Money`, `DateText`, `Num`, `NavigateTableBody`
— plus the detail-page shape from §6: `DetailLayout` (main + right rail),
`RailCard`, `AtAGlance`, `Meter`, `ProcessStepper` and `ActivityFeed`.

`DetailLayout`, `RailCard` and `AtAGlance` are not optional extras: they are
how the rail gets built, and the rail is what lets Overview be a synthesis
instead of a second copy of the header.

This is not an optimisation, it is the polish mechanism. Pages that each
hand-roll their own tab strip, key-facts grid and (missing) loading state
diverge immediately, and no fix can be applied in one place. **Set `LOCALE`
and `CURRENCY` from the requirement spec while you are here** — a hard-coded
`$` on a non-US app is a defect.

If at the end of your run `shared.tsx` is a near-empty file and the detail
pages are ~100 lines of inline-styled JSX each, this step was skipped.

### 5d. Write the custom pages

**Build the plan from 5b, page by page.** Open `design-plan.md` and implement
each entity's six answers literally: the lead card it names, the rail it names,
the tabs and empty-state copy it names. If while building you conclude the plan
was wrong, change `design-plan.md` and say why in your summary — but do not
silently drift, because the gate compares the finished page to that file.


Under STEP 3's defaults essentially every app needs these: focus objects get
full-page entity-360 views with child tables, and each role gets a landing
page. Appbuilder's prebuilt shell renders only `page_type: "crud"` pages, so
anything beyond a plain lookup table requires your own build.

**Compose from 5c's primitives, and pick a treatment per block.**
`shared-primitives.md` has a card-treatment library: `Section` (plain field
group), `Card`+`Inset`+`MetricTile` (the lead block), `Card tone=` (status),
`RailCard` (rail). **Every detail page needs exactly one lead `Card`** — a page
composed entirely of `Section`s is structurally correct and renders as
identical grey-capped white boxes, which is the observed wireframe failure.
Numbers go in `MetricTile` with a `qualifier`, never bare.

Import the primitives; do not re-implement layout per
page, and do not paste a reference skeleton and swap its classes for inline
`style` objects — the scaffold ships Tailwind v4, and inline styles cannot
express hover, focus or responsive behaviour, so a page written that way
cannot meet the visual bar.

Every entity the team works in daily gets a detail page — including the ones
whose list is otherwise plain. An entity left on the default drawer shows the
user almost nothing.

Export every page from `src/custom/pages/index.js`. **The export name must
match the route's `component` value exactly**, or the page renders blank.

Patterns: [frontend/entity-360.md](references/frontend/entity-360.md),
[frontend/design-system.md](references/frontend/design-system.md),
[frontend/crud.md](references/frontend/crud.md),
[frontend/form.md](references/frontend/form.md).

### 5e. Brand the login page

**Every app gets a branded login page. Always** — there is no toggle and no
condition. It is the first screen anyone sees, and the framework default says
nothing about the product.

Full contract and a copyable skeleton:
[frontend/auth-login.md](references/frontend/auth-login.md). In short:

- **The left panel must be full, and fullness is measured, not judged.** A
  headline floating in a gradient is the observed failure mode — it satisfies
  every structural rule and still ships a page that reads as unfinished. It
  needs a **middle band** (journey stepper or proof tiles) plus 3 feature rows
  with icon tiles, a `700`-weight headline capped at 640px, an eyebrow in both
  panes, and a layered background. Gates and copy-paste CSS: auth-login.md §5b.

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
- Inline `<style>` in the component (it mounts over the whole viewport).
  `lucide-react` is available for icons, and Inter/JetBrains Mono may be loaded
  from Google Fonts — see design-system.md §10 for what is and is not allowed.

### 5f. Build the bundle — once, at the end of frontend work

Not after every change:

```bash
cd frontend && npm install && npm run build:zango
```

This writes `frontend/zango-build/zango-app.<timestamp>.min.js`.

**Read the built filename off disk** — it carries a build timestamp, so never
guess it:

```bash
ls frontend/zango-build/
```

Then deploy it into the workspace's `static/js/`. This one copy is the sole
exception to the read-only Bash rule — the bundle is multi-megabyte minified
JS, so it cannot go through the Write tool:

```bash
cp -r frontend/zango-build/. static/js/
```

Only this exact form is permitted: source `frontend/zango-build/`, destination
`static/js/`, both workspace-relative. Anything else — another source, another
destination, `mv`, `rm` — is denied.

`sync_static` and `collectstatic` then publish it, and you run both in STEP 7.
`sync_static` copies from `<workspace>/static` only, so a bundle left in
`frontend/zango-build/` is never served no matter what `app.html` points at.

### 5g. Create the `app` module so `/app/` serves the UI

Without it `/app/` returns 404 and the app has no front door. Copy the
template from
[templates/app-module/README.md](references/templates/app-module/README.md)
into `backend/app/`:

```
backend/app/
├── urls.py          AppView at ^app/, RedirectAppView for / and /login
├── views.py
├── policies.json    grant AnonymousUsers access to the view
└── templates/app.html
```

`urls.py` is **exactly this** — do not improvise the patterns:

```python
from django.urls import re_path
from .views import AppView, RedirectAppView

urlpatterns = [
    re_path(r"^app/", AppView.as_view()),
    re_path(r"^login/?$", RedirectAppView.as_view()),
    re_path(r"^/", RedirectAppView.as_view()),
]
```

The root entry must be `re_path(r"^/", ...)`. Writing `r"^$"` instead does
**not** work in this deployment — an agent improvised it on one run and the
root redirect broke. Keep the three patterns, in this order.

Register it **first** in `settings.json` so it catches root paths:

```json
{"app_routes": [{"re_path": "^", "module": "app", "url": "urls"}]}
```

The mount is `"^"`, **not** `"^app/"`. The module is mounted at the site root
and its own `urls.py` owns the rest of the path — that is why `urls.py` above
carries `^app/` itself, and why the root redirect is reachable at all. Mount it
at `"^app/"` and the module never sees `/` or `/login`, so both redirects are
dead. It must also be the **first** entry, or another module's `^` catches
root paths first.

`app.html` mounts the React root and loads **your** bundle — the one you built
in 5f, whose real filename you just read off disk:

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
`/app/login`, which is where your branded login renders (5e).

### 5h. Register routes and menu configs

Every page you built needs a route; every role needs a menu. Both are API
calls, and **neither has a file-based substitute** — a payload written to disk
is not a saved config.

Full sequence, payload shapes and failure modes:
[appbuilder/api-configuration.md](references/packages/appbuilder/api-configuration.md).
The essentials:

- **Order matters.** Save routes first, read back the server-generated
  `route_id`s, then create one menu config per role using those ids. Ids you
  invent yourself save fine and produce a sidebar of dead links.
- `save_routes` **replaces the whole array** — fetch, merge, send.
- Custom pages are `page_type: "custom"` with `component` matching the export
  name exactly. **An app whose routes are all `"crud"` has no custom
  frontend** — if none are custom, you skipped 5a–5d.
- **`create_config` takes the role's NUMERIC ID, not its name.** The field is
  called `user_role` for frontend compatibility but resolves as a primary key,
  so a name returns `Field 'id' expected a number but got 'Approver'.` Resolve
  it via `action=get_available_roles`, which shrinks as configs are created —
  re-fetch rather than caching, or the last role silently gets no menu.
- **Give every menu item its own icon, and every icon is inline SVG. Never
  emoji.** `clean_icon()` replaces any icon
  containing a replacement character with `"📄"`, and emoji only have to
  survive one mis-encoded hop to become one. The POST still returns
  `success: true`. Use 32×32 viewBox paths with `stroke="currentColor"`.
- `curl` is permitted against this app's own domain and localhost, and **POST
  with a body is allowed** — `-X POST`, `-d`, `--data-raw`, `--data-binary`,
  `-F`, `-H` all work. The token lasts 30 minutes.

**Verify by reading back, not by status code.** `get_routes` must not return
`[]`; `get_configs` must return one config per role; every menu `route_id` must
exist in `get_routes`; every `icon` must contain `<svg`. All four failure modes
return `success: true`, so the read-back is the only evidence.

If `appbuilder_config_url` is UNAVAILABLE, skip 5h and list what an operator
must add. Do **not** skip 5a-5g for it — the build does not depend on this API.

> **That is the only reason to skip 5h.**
> **A failure here is not an outstanding item — it is a blocker.**
> The observed pattern is: the POST fails, the agent files
> it as a remaining task, finishes everything else and reports success — leaving
> an app whose sidebar is empty or entirely dead links, indistinguishable to the
> user from no frontend at all.
>
> So **attempt the call before concluding anything is blocked** — a guess about
> the sandbox is not evidence. Read the response body (it names the fix), fix,
> and retry. Only if it still fails, stop and report the run **incomplete** with
> the exact command and verbatim response. Never write "routes and menus still need registering" in a
> summary that otherwise reads as success — the correct first line is that **the
> app has no working navigation**.
### Verify STEP 5 before moving on

Work through the full gate in
[frontend/verify-gate.md](references/frontend/verify-gate.md) — 24 items, each
binding. Several of these failures return HTTP 200 and look correct, so the
gate is what catches them, not the absence of errors.

**Wired up** — `frontend/` exists; the bundle is built and copied to
`static/js/`; `app.html` loads *your* bundle (never `app_initializer_endpoint`
or `packages/appbuilder/js/`); at least one route is `page_type: "custom"`; the
branded login renders and its left panel passes the §5b fill gate; routes and
menus read back correctly, with every menu `route_id` present in `get_routes`
and every `icon` an inline SVG.

**Polished** — `shared.tsx` exports the primitives and the pages compose them.
**No literal hex colour in `src/custom/pages/`.**
`src/custom/auth/` is the one exception — the login renders pre-auth with no
theme tokens in scope, so it takes its palette from the run context. No
inline `style={{...}}` for static styling. Four states on every data surface,
**including each child tab** opened and confirmed to render. `Money`/`DateText`
everywhere; one visual anchor per page; detail pages match design-system.md §6;
`design-plan.md` exists and the pages match it.

**Correct, full and not flat** — the three most recently observed to fail:

- **Open one record and check the page against the stored data.** A page whose
  numbers are all `0` is internally consistent and uniformly wrong. The usual
  cause is a `BaseDetail` with no `Meta.fields` (entity-360.md §3b).
- **The page fills the screen.** Content width within ~300px of
  `viewport - 260`, and the rail at least 0.6x the main column's height. A
  1080px column on a 1920px screen leaves ~640px of empty grey.
- **The page is not flat.** Run the snippet in design-system.md §1: at least 2
  distinct card fills, every card carrying the hairline shadow, page ground
  differing from card fill. All-white boxes with grey title bars passes every
  structural rule and still reads as a wireframe.
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
- **Shared primitives before pages**: `src/custom/pages/shared.tsx` is STEP 5c
  and is written **before** the first page. Pages compose from it. Four detail
  pages that each hand-roll a tab strip, carry literal hexes and have no
  loading or empty state are a failed run even though every file exists and
  nothing errors.
- **Reference skeletons are a floor, not a template**: adapt them to the app in
  front of you. Transcribing a skeleton and converting its Tailwind classes to
  inline `style` objects is a downgrade — inline styles cannot express hover,
  focus or responsive behaviour, so the result cannot meet the visual bar.
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
