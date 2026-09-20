---
name: zango-app-developer-server
description: Server-mode Zango app development, used by Agent Mode inside the Zango platform. Implements backend and frontend features on an existing, already-deployed Zango app - modules, DynamicModelBase models, BaseCrudView CRUD views, forms, tables, workflows, policies, async tasks, AppBuilder routes, custom React pages, entity-360 detail views with child tables, and a branded login page - working only inside that app's workspace directory. Assumes no interactive user feedback.
version: 1.6.0
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

**The first version must already look like a product.** Node is available, so an
app whose every page is the default CRUD shell is an incomplete first version,
not a safe one.

Classify each entity, in this order:

1. **Focus object?** Read the FK graph: other models declare a `ZForeignKey` to
   it **and** a user works on it directly (Patient, Order, Case, Employee,
   Customer, Program). Gets an **entity-360** — full-page route showing
   identity, key facts, and each related record set as a **child table in a
   tab**. A Patient page shows that patient's Orders, Programs and Documents
   rather than sending the user to three menu items to filter by hand. **No
   fixed cap** — decide from the app's shape and justify the selection in your
   summary. A lookup table never qualifies, however many FKs point at it.
2. **Primary entity, no children yet?** Profile-style custom detail page, no
   tabs — held to the **same bar as entity-360**: identity block, synthesis lead
   card, rail, one anchor (verify-gate.md item 26). No tabs
   does not mean no design effort.
3. **List needs a non-standard layout?** Kanban (statuses), calendar (dates),
   cards (visual), timeline (sequence) — via `CrudHandler`'s `customTableBody`,
   not a fully custom component.
4. **Lookup entity?** (Department, City, Category, Document Type, Status master
   — referenced from dropdowns, never opened.) Default CRUD; custom work here is
   waste.

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

Dashboard stat cards need aggregates, not rows. `useTableRows` works for
small tables, but doesn't have to be the default — a custom view that
aggregates in the database and returns just the numbers is equally valid,
and scales better once a table outgrows one page.

Detail-view mechanics, child tables and the failure modes that make them break
are in [frontend/entity-360.md](references/frontend/entity-360.md). The
primitives every page composes from are in
[frontend/shared-primitives.md](references/frontend/shared-primitives.md), and
the values they use are in
[frontend/design/](references/frontend/design/). All are
required reading before you write components — **at STEP 5, not here.** You
are planning now; naming them is enough. See "When to read a reference" below.

### Reference index

Look up the rows for what this app actually needs. Skip the rest. Each row
names the file to read — open it directly rather than listing its directory.
A directory's `README.md` indexes the rest of that directory, for the cases a
row below does not cover.

#### When to read a reference

**Read each reference immediately before writing the code that uses it — not
here, and not in a batch.** This index tells you *which* file answers a
question; it is not a reading list to work through before you start.

This matters because everything you read stays in context for the rest of the
run and is re-sent on every turn. A reference opened while planning is charged
against all ~180 turns that follow; the same file opened at the sub-step that
needs it is charged against the few that remain. Front-loading the index has
put real runs over the context limit mid-build, and what gets discarded when
that happens is the detail you were going to implement.

So: at this step, **name** the references each part of the build will need and
write those names into your plan. Open each one at the moment you write its
code — the model reference when you write models, `entity-360.md` when you
write the detail page, `appbuilder/api-configuration.md` when you register
routes at 5h.

**Deferring is not skipping, and this is the trap.** Every reference must
still be read before the code that depends on it. "I will read it later" that
turns into writing from memory is an improvised Zango API — the exact failure
STEP 2 exists to prevent, and worse than front-loading. If you reach the code
and have not read its reference, stop and read it then.

The five largest files are the ones this matters most for — together they are
over half of all reference bytes, and none is needed before STEP 5:

| File | Read at |
|---|---|
| [frontend/entity-360.md](references/frontend/entity-360.md) | 5d, writing that detail page |
| [frontend/appbuilder.md](references/frontend/appbuilder.md) | 5a scaffold, then 5h wiring |
| [appbuilder/api-configuration.md](references/packages/appbuilder/api-configuration.md) | 5h, registering routes and menus |
| [packages/crud/detail.md](references/packages/crud/detail.md) | when writing a `BaseDetail` view |

| What you need to build | Read |
|------------------------|------|
| Module | [core/modules.md](references/core/modules.md) |
| Model | [core/models.md](references/core/models.md) |
| CRUD view | [core/modules.md](references/core/modules.md) + [core/models.md](references/core/models.md), then [crud/views/core.md](references/packages/crud/views/core.md), [crud/forms/core.md](references/packages/crud/forms/core.md), [crud/tables/core.md](references/packages/crud/tables/core.md) — those three and nothing else |
| Workflow | [`overview.md`](references/packages/workflow/overview.md) always — it indexes the rest — then [statuses.md](references/packages/workflow/statuses.md) and [transitions.md](references/packages/workflow/transitions.md) |
| Policies | [core/policies.md](references/core/policies.md) |
| Async task | [core/async-tasks.md](references/core/async-tasks.md) |
| Routes and menus (see STEP 5) | [appbuilder/api-configuration.md](references/packages/appbuilder/api-configuration.md) |
| Secrets / encrypted fields | [core/secrets.md](references/core/secrets.md) |
| Detail view with child tables | [frontend/entity-360.md](references/frontend/entity-360.md) |
| Branded login / custom auth screens | [frontend/auth-login.md](references/frontend/auth-login.md) |
| The values that meet that bar — tokens, direction, card treatments | [frontend/design/](references/frontend/design/) — read at 5c/5d |
| Shared UI primitives (write these first) | [frontend/shared-primitives.md](references/frontend/shared-primitives.md) |
| Frontend patterns | [frontend/crud/core.md](references/frontend/crud/core.md) always (imports, API shapes, CrudHandler), then only what the page needs |

## STEP 4: Implement

Read the reference for each thing you build **before writing its code**. Use
their exact patterns and attributes — do not improvise Zango APIs. A pattern
you half-remember is an improvised Zango API, which is the failure STEP 2
exists to prevent.

Read only the rows you actually need, and read each **at the point of use** —
the model reference when you write models, not all of them before you start.
Rows naming a **directory** are deliberate: list it and read the file you need
from its `README.md` index — never every file in it.

Reading at the point of use never means writing the code first and checking
afterwards. Open the reference, then write.

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
| 5b | **Read treatments.md + directions.md, then plan the pages** | `design-plan.md` at the workspace root, with an anchor treatment named per page |
| 5c | Write the tokens + shared primitives | `src/custom/pages/tokens.css` + `shared.tsx` |
| 5d | Write the custom pages | entity-360, landing pages |
| 5e | Brand the login page | `AppLoginCard.tsx` |
| 5f | Build the bundle | `frontend/zango-build/zango-app.<ts>.min.js` |
| 5g | Create the `app` module | `backend/app/` + `app.html` |
| 5h | Register routes and menus | navigation for every role |

### 5c, 5d and 5e — write these yourself

**Do not dispatch `Task`/`Agent` subagents for the frontend.** This was tried
— one subagent per page, in parallel — and measured worse on every real run:
each parallel dispatch independently re-read the same shared reference
material (`entity-360.md`, `shared-primitives.md`, the
full `design-plan.md`), so cache-creation, output and thinking tokens all went
up by multiples (3–9x on a same-size comparison) for a total cost higher than
writing the whole frontend phase yourself, even though per-dispatch cache-read
looked fine in isolation. The duplication is structural to per-page parallel
dispatch, not a prompt-wording bug — it does not go away by trimming what each
dispatch reads, only by not forking the reads at all.

Write `tokens.css`, `shared.tsx`, every entity-360 page, the dashboard/landing
pages, and the login page in this thread, in that order. Read each reference
immediately before the code that needs it (see "When to read a reference"
above) rather than up front — that is what actually controls peak context,
not who writes the file.

The one thing delegation was correctly solving for — the backend phase's
context still being live when the frontend is written — is real: a run that
carried the whole backend phase forward peaked at **359k context** and
compacted mid-build, producing visibly worse pages than the plan called for,
because compaction discards exactly the design detail you are implementing.
Manage that directly instead of forking contexts to dodge it:

- Keep `design-plan.md` (5b) as the one artifact you actually re-read per
  page — it already distills what `entity-360.md` and the design kit say for
  this app, so once those are read once during planning you should not
  need to reopen them per page.
- Do not re-read backend files (`models.py`, `views.py`) while writing
  frontend pages — the facts you need (model/module names, field names and
  types, the CRUD view URL, per-child-tab FK) were already established in
  STEP 4; carry them forward as your own working notes instead of rereading
  source.
- If you are deep enough into the frontend phase that context is genuinely
  getting tight, that is a signal to keep pages leaner (compose from
  `shared.tsx` primitives, avoid re-deriving anything already decided in
  `design-plan.md`) — not a reason to reach for a subagent.

**Do not treat the install wait as spare time.** `npm install` runs for
several minutes; do not fill it by writing 5c/5d ahead of the scaffold being
ready — write them in order, after the install completes.

### 5a. Scaffold the frontend — FIRST, before any of the rest

**This is the step that gets skipped**, and skipping it makes every later
frontend instruction unreachable: no `frontend/` at the end of your run means no
custom pages, no entity-360 and no branded login, whatever else you did.

Skip **only** if `frontend/` already exists — check, do not assume.

```bash
npx @zango-core/create-zango-app frontend --skip-install   # in the workspace root
```

- **`--skip-install` is required** — the scaffold's own `npm install` uses strict
  peer resolution and fails on this stack. Install separately with
  `--legacy-peer-deps`.
- **Configure `frontend/.env`** with `VITE_PROXY_ROUTES` listing every backend
  route the app serves (`/api`, `/appbuilder`, each CRUD module route).
  **Never include `/app`** — a frontend route, not a backend proxy. See
  [frontend/appbuilder.md](references/frontend/appbuilder.md).

Target layout — `src/custom/auth/AppLoginCard.tsx` (5e),
`src/custom/pages/<Entity>Detail.tsx` and `Dashboard.tsx` (5d), and
`src/custom/pages/index.js`, whose **export names MUST match
`route.component`**. `App.tsx` carries the `authConfig` + `customPages` wiring.

The run prompt lists the npm commands and design packages you may install;
anything else is denied, so say so in your summary rather than trying.

**Always pass `--legacy-peer-deps` to `npm install`/`npm ci`** — this stack's
peer dependencies do not resolve cleanly under npm's default strict algorithm,
and a plain `npm install` fails or produces a broken `node_modules`.

**Do not treat the install wait as spare time.** It runs for several minutes.
Use it for 5b (planning), which needs no scaffold — but do not start writing
5c/5d/5e "while npm finishes"; that is how the frontend ends up written from a
context already carrying the whole backend phase, observed on a real run that
peaked at 359k context and compacted mid-build. Let the install finish, then
write 5c → 5d → 5e in order.

Icons and fonts are already available: `lucide-react` ships with `@zango-core`,
and Inter and JetBrains Mono load from Google Fonts — see
[frontend/design/tokens.md](references/frontend/design/tokens.md). The earlier
claim that they were unavailable was wrong, and it is why generated apps
looked plain.

### 5b. Plan the pages — write `design-plan.md` before any component

Every rule in §6/§1a is satisfiable *nominally* — a second Section that adds
nothing, tabs with zero counts, an Overview re-listing the header. That passes a
grep and fails a glance. So write `design-plan.md` at the workspace root first:
a real file, because the verify gate reads it back against the finished pages.

**Read [frontend/design/treatments.md](references/frontend/design/treatments.md)
and [frontend/design/directions.md](references/frontend/design/directions.md)
before writing a single line of `design-plan.md`, not after.** A plan drafted
without treatments.md in context comes out as "N sections with MetricTile
counts" — a flat, anchor-less list — and 5d then "implements it literally,"
shipping the flat page verbatim even though treatments.md gets read later in
the run. Reading the doc late does not help once the plan already shipped
without an anchor. This applies to **every** page you plan, including the
role landing page (Home) below — it is not exempt just because it isn't a
focus entity.

For **each focus entity**, answer all six — a few lines each, not a document:

1. **The question this page answers.** One sentence in the user's words, not the
   schema's: *"Can we still bid on this, and are we ready to?"*, not *"shows
   tender fields"*. Can't write it without listing fields? You don't understand
   the entity yet.
2. **The lead card** — a **synthesis, not a field dump**: a computed answer to
   (1) from several fields plus derived state (progress against an allowance, a
   countdown with readiness checklist, a balance with ageing). Name what it
   computes and from which fields. *Re-listing header facts is the single most
   common failure and is never acceptable.*
3. **The layout** — default **main column + right rail** (§6). State the rail's
   contents: status with who changed it and when, the flat attributes
   at-a-glance, open tasks, consent/compliance state. The rail carries the flat
   fields, which is what frees Overview to be a synthesis.
4. **The aesthetic direction** — pick **one row** from the table in
   [frontend/design/directions.md](references/frontend/design/directions.md)
   and record the row name, its accent hex and its density. One row per app,
   not per page. Do not describe a direction in prose instead of picking a
   row: "commit to a direction" without a row is how every app ends up
   looking the same.
5. **Every tab** — count source, child table or composed view, and its
   **empty-state copy written out in full**. Copy invented at implementation
   time reverts to "No data".
6. **The anchor and its treatment** — name the single element on this page
   that is visually heavier than everything else (the lead card, a hero
   figure, the primary chart), then pick its treatment from
   [design/treatments.md](references/frontend/design/treatments.md): gradient
   hero for an identity/summary page, sunken band for grouped metrics,
   top-accent for rail blocks. Record which treatment goes where **in this
   plan**, not as a decision left for 5d. If you cannot name an anchor, you do
   not yet know what the page is for, and it will come out as a flat list of
   equal-weight boxes — the exact failure this step exists to prevent.

Then one app-level entry: the **identity strip** — per entity, the four to six
facts that identify a record at a glance (reference number, dates, the one
relationship that matters, contact). The header is not a title plus a chip.

**The role landing page (Home) gets the same six answers**, not a shorter
version — it is the first page every user sees and is not exempt just
because it is not a focus entity. In particular: name its anchor (typically a
gradient-hero summary of what needs attention today) and do not default it to
"N sections with MetricTile counts at the top" — three identical stat tiles
with no hero is the flat-list failure by another name.

Write it, then build exactly it.

### 5c. Write the shared primitives — before any page

Write this before any page (5d) or the login page (5e) — both import from it.
Set the direction row (name, accent hex, density) from what you decided at
5b; you already have it in context.

Write **two** files here, in this order:

1. `src/custom/pages/tokens.css` — copy the block from
   [frontend/design/tokens.md](references/frontend/design/tokens.md), setting
   `--accent` (and its `-50`/`-600`/`-700` steps) from the direction row
   chosen at 5b. This is the file that gives the pages a tonal range to
   design with; without it they come out flat however well they are composed.
2. `src/custom/pages/shared.tsx` — imports `./tokens.css` once, at the top.

Then compose every later page from `shared.tsx`. Full contract and a copyable
floor: [frontend/shared-primitives.md](references/frontend/shared-primitives.md).

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

Write each page, one at a time, then `index.js` from the export names.

**Implement `design-plan.md` literally** — the lead card, rail, tabs and
empty-state copy it names, per entity. Concluded the plan is wrong? Edit
`design-plan.md` and say why in your summary; never drift silently, because the
gate compares finished pages to that file.

Rules:

- **Every focus object gets a full-page entity-360 with child tabs; every role
  gets a landing page.** Appbuilder's shell renders only `page_type: "crud"`,
  so anything beyond a plain lookup table is your build. Every entity the team
  works in daily gets a detail page, including ones whose list looks plain.
- **Two or three card treatments per page, and exactly one anchor.** A page
  where every block is a white bordered card renders as identical grey-capped
  boxes — the wireframe failure. Pick treatments by role from
  [design/treatments.md](references/frontend/design/treatments.md): gradient
  hero for the anchor (one per page), sunken band for grouped metrics,
  bordered card for the rest, top-accent for rail blocks. The primitives that
  carry them: `Section` (field group), `Card`+`Inset`+`MetricTile` (lead
  card), `Card tone=` (status), `RailCard` (rail). Name your anchor before
  writing; if you cannot, you do not yet know what the page is for.
- **Numbers go in `MetricTile` with a `qualifier`**, never bare.
- **Import 5c's primitives; never re-implement layout per page.** Do not paste a
  reference skeleton and swap classes for inline `style` — the scaffold ships
  Tailwind v4, and inline styles cannot express hover, focus or responsive
  behaviour.
- **Export every page from `src/custom/pages/index.js`. The export name must
  match the route's `component` value exactly**, or the page renders blank.

Patterns: [frontend/entity-360.md](references/frontend/entity-360.md),
[frontend/design/treatments.md](references/frontend/design/treatments.md),
[frontend/crud/core.md](references/frontend/crud/core.md) +
[crud/detail.md](references/frontend/crud/detail.md),
[frontend/form.md](references/frontend/form.md).

### 5e. Brand the login page

Write this after 5d. Apply the `authConfig` line to `App.tsx` in the same
pass.

**Every app gets a branded login page. Always** — no toggle, no condition. It
is the first screen anyone sees, and the framework default says nothing about
the product.

Full contract, copy rules and a copyable skeleton:
[frontend/auth-login.md](references/frontend/auth-login.md). Follow it. The
four things agents get wrong even with it open:

1. **Never hand-roll auth.** Render the framework's own `PasswordLoginForm`,
   `RoleSelection` and `PasswordResetRequired` inside your layout. Your own
   POST loses SAML, password policy, rate limiting and role selection.
2. **Drive the flow from `PasswordLoginForm`'s `onSuccess`**, *not*
   `LoginContext.onLogin` (which mis-handles the single-role case), and
   normalise `next_step` across its four response shapes.
3. **Register a full override** on `ZangoApp`, passing the **component**, not
   an element:
   `authConfig={{ customComponents: { LoginPage: AppLoginCard } }}`
4. **The left panel must be full, and fullness is measured, not judged.** A
   headline floating in a gradient satisfies every structural rule and still
   ships a page that reads as unfinished. It needs a **middle band** (journey
   stepper or proof tiles), 3 feature rows with icon tiles, a `700`-weight
   headline capped at 640px, an eyebrow in both panes, and a layered
   background. Gates and copy-paste CSS: auth-login.md §5b.

The component's CSS goes in an inline `<style>` in the component itself — it
mounts over the whole viewport.

Keep the split-screen archetype and the "Powered by Zelthy" attribution —
re-theme and rewrite the copy, do not invent a different layout.

### 5f. Build the bundle — once, at the end of frontend work

**Gate — run this before building, every time:**

```bash
ls frontend/src/custom/pages/ frontend/src/custom/auth/
```

Every page named in `design-plan.md` plus `tokens.css`, `shared.tsx` and
`AppLoginCard.tsx` must be there. **If a file is missing, write it now,
before you build.** `tokens.css` missing is not cosmetic: every
primitive resolves its colours, shadows and fonts from it, so the app builds
and ships unstyled. Building without it silently ships an app missing that page, and
neither the build nor the platform will tell you.

Not after every change:

```bash
cd frontend && npm install --legacy-peer-deps && npm run build:zango
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

Without it `/app/` returns 404 and the app has no front door.

**Copy the module from
[templates/app-module/](references/templates/app-module/README.md) into
`backend/app/` and follow it** — `urls.py`, `views.py`, `policies.json` and
`templates/app.html` are all there, with the exact route patterns, the
`settings.json` entry and the mount rules. Copy them exactly; do not
improvise the patterns — in particular the root entry is `re_path(r"^/", ...)`
and **never** `r"^$"`, and the `app_routes` mount is `"^"`, **not** `"^app/"`.

Also confirm `RedirectAppView` maps `/` and `/login` to `/app`; the React router
owns `/app/login`, where your branded login renders (5e).

Three things that silently produce a broken app, so check them before you
finish:

- **`app.html` points at *your* bundle** — the 5f filename you read off disk,
  not the placeholder.
- **`policies.json` grants `AnonymousUsers`** on `AppView` and
  `RedirectAppView`, or the login page 403s and nobody can reach the app.
- **`app.html` contains neither `app_initializer_endpoint` nor
  `packages/appbuilder/js/`.** Either means you copied appbuilder's own shell:
  **nothing errors**, the stock CRUD UI renders, and your custom pages and
  branded login are simply absent.

### 5h. Register routes and menu configs

Every page needs a route; every role needs a menu. Both are API calls and
**neither has a file-based substitute** — a payload written to disk is not a
saved config.

Sequence, payload shapes, the permitted `curl` flags and the read-back checks:
[appbuilder/api-configuration.md](references/packages/appbuilder/api-configuration.md).
Follow it. The five things agents get wrong even with it open:

1. **Order.** Save routes first, read back the server-generated `route_id`s,
   *then* create one menu config per role from those ids. Ids you invent save
   fine and produce a sidebar of dead links.
2. **`save_routes` replaces the whole array** — fetch, merge, send. And every
   route `path` must start with `/app`.
3. **`create_config` takes the role's NUMERIC id, not its name.** The field is
   `user_role` for frontend compatibility but resolves as a primary key, so a
   name returns `Field 'id' expected a number but got 'Approver'.` Resolve via
   `action=get_available_roles`, which **shrinks as configs are created** —
   re-fetch rather than caching, or the last role silently gets no menu.
4. **Every menu item gets its own inline-SVG icon. Never emoji.**
   `clean_icon()` rewrites any icon containing a replacement character to
   `"📄"`, and emoji need only one mis-encoded hop to become one. The POST
   still returns `success: true`. Use 32×32 viewBox paths with
   `stroke="currentColor"`.
5. **Custom pages are `page_type: "custom"` with `component` matching the
   export name exactly.** An app whose routes are all `"crud"` has no custom
   frontend — if none are custom, you skipped 5a–5d.

**Verify by reading back, not by status code.** `get_routes` must not be `[]`;
`get_configs` must return one config per role; every menu `route_id` must exist
in `get_routes`; every `icon` must contain `<svg`. All four failure modes
return `success: true`, so the read-back is the only evidence.

> **A failure here is not an outstanding item — it is a blocker.** The observed
> pattern: the POST fails, the agent files it as a remaining task, finishes
> everything else and reports success — leaving an app whose sidebar is empty
> or entirely dead links, indistinguishable to the user from no frontend at
> all.

The only reason to skip 5h is `appbuilder_config_url` being UNAVAILABLE — then list
what an operator must add. Never skip 5a–5g for it; the build does not depend
on this API.

### Verify STEP 5 before moving on

Work through the full gate in
[frontend/verify-gate.md](references/frontend/verify-gate.md) — 25 items, each
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
everywhere; one visual anchor per page; detail pages match entity-360.md §6;
`design-plan.md` exists and the pages match it.

**Correct, full and not flat** — the four most recently observed to fail:

- **Open one record and check the page against the stored data.** A page whose
  numbers are all `0` is internally consistent and uniformly wrong. The usual
  cause is a `BaseDetail` with no `Meta.fields` (entity-360.md §3b).
- **Add a row from a child tab, then check the page's own numbers without
  reloading.** The table refreshes itself; tab badges and stat cards fetched by
  the page do not (entity-360.md §4b).
- **The page fills the screen.** Content width within ~300px of
  `viewport - 260`, and the rail at least 0.6x the main column's height. A
  1080px column on a 1920px screen leaves ~640px of empty grey.
- **The page is not flat.** Run the snippet in verify-gate.md item 22: at least 2
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

The platform creates them after your run, generates a password for each, and
shows the credentials on the run detail. Do **not** invent passwords yourself
and do not put any password in a file — they are generated.

Use addresses that are obviously non-production (`@demo.test`,
`@example.com`). One user per role is enough.

You do not need to do anything about access policies: every role you define
is given the baseline `AllowFromAnywhere` userAccess policy automatically.
Without it a role fails the userAccess check before any view permission is
evaluated, and its users can load nothing.

## STEP 7: Hand off

**Apply your own work and fix what it reports.** Run the management commands
the run prompt permits — `ws_makemigration`, `ws_migrate`, `ws_sync`,
`sync_static`, `collectstatic` — **in that order, and read the output.** A
migration error is yours to fix; that is the point of running them yourself.
Iterate until they pass.

You cannot restart the app server or Celery. If you changed `models.py`,
`tasks.py` or `settings.json`, **say so** — a restart is needed before the
change takes effect.

Then write the summary. It **must** cover every item in the required
checklist, including the claims that have been reported as done when they were
not: [handoff-summary.md](references/handoff-summary.md). Quote the `src` line
from `app.html` and the routes/menus read-back rather than asserting them.

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
