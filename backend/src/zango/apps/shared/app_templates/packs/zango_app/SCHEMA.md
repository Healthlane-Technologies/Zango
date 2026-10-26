# Zango app spec v1 — reference

One file (`app_spec.yaml`) describes one Zango app: who uses it, what it
stores, how records move, and what every screen shows. It is written from the
user's requirement, previewed live as a clickable app with demo data, and later
turned into plain Zango code (no template codebase):

| Spec                     | Becomes in Zango                                                         |
|--------------------------|--------------------------------------------------------------------------|
| `roles`, `pages`, menu   | UserRoleModel, AppBuilder routes and menus, policies                     |
| `modules`                | one `backend/<module>/` folder each (models, forms, tables, workflow…)   |
| `entity.fields`          | a DynamicModelBase model                                                 |
| `entity.form`            | BaseForm (create / edit); `clean()` for validation and duplicates        |
| `entity.table`           | ModelTable (columns, filters, row actions)                               |
| `entity.workflow`        | WorkflowBase (statuses, transitions, tags, conditions, done hooks)        |
| `entity.access`          | view policies and `get_queryset()` row scoping                           |
| `detail_views`           | a custom React 360 page and one aggregate API endpoint                   |

`example.yaml` (Vendor Hub) uses every construct below; read it when unsure
how deep an answer should go. `starter.yaml` is the smallest valid app.

## Conventions

- **Codes** (`code`, field keys, status codes, transition names) are
  `snake_case` and unique in their scope. Entity codes are singular and unique
  across all modules.
- **Roles** are referenced everywhere by their exact `name` ("Procurement
  Manager"), never by a code.
- **Field paths** use dots across link fields: `purchase_order.vendor.city`.
- **Built-in fields** on every entity: `id`, `created_at`, `created_by`,
  `modified_at`, `modified_by`. Entities with a workflow also have `status`
  and `tags`.
- **Lists of keyed things** (fields, columns, form fields) are lists of
  single-key maps: `- legal_name: { type: text, required: true }`. In tool
  paths pick one with `@key`: `/modules/@vendors/entities/@vendor/fields/@gstin`.
- **Plain language** goes in `text`, `on_done`, `on_create`, `shows`,
  `computed` and `custom_requirements[].text`. The build hand-writes code for
  these, so make them specific and testable ("email the vendor contact the
  reason and a re-upload link"), never vague ("notify relevant people").

### Writing YAML the build reads the same way

The build skill re-reads the spec with its own checker and stops on anything
ambiguous, so:

- **Quote every prose value inside `{ }`** — any value with a comma, colon,
  `?`, `#` or quotes: `computed: "Sum of line amounts, recalculated on save."`.
  Unquoted, `, recalculated on save.` silently becomes a separate key.
- **Modules must not link in a cycle.** If `a` has a link into module `b`,
  nothing in `b` may link back into `a`; put entities that point at each other
  in the same module.
- `navigate` row actions go to a detail view, a page, a URL, or
  `{ field: <url field> }` — nothing else.
- `limit_choices` compares fields of the **linked** entity with literals or
  `form.<field of this form>`; it cannot follow a path through `form.`.
- `rows: { own: <path> }` is only for the role whose users log in as the
  owning record (an `app_user` link); other roles use
  `rows: { where: "<path>.<user link> == current_user" }`.
- `default_sort` names a real field (or `-field`), never a label.

### Expressions

Used in `condition`, `where`, `show_when`, `limit_choices`, `create_on`,
`readonly_when.when`:

```
<path> == | != | > | >= | < | <= <value>
<path> in [a, b]          <path> not_in [a, b]
<path> is_set | is_empty | is_true | is_false     (there is no is_not_set: use is_empty)
status == <code>          has_tag <code>
current_user.role == "<Role>"
```

Combine with `all: [...]` / `any: [...]`. Anything the grammar cannot express
goes in a `text:` item as plain language:

```yaml
condition:
  all:
    - gstin is_set
    - text: At least one GST certificate document is verified.
```

### Enums

| Key                | Values                                                                                 |
|--------------------|----------------------------------------------------------------------------------------|
| `field.type`       | text, long_text, integer, decimal, money, percent, boolean, date, datetime, time, email, phone, url, choice, multi_choice, link, multi_link, file, image, json |
| `entity.kind`      | hero (centre of a 360 page), transactional (own lifecycle and list page), child (only under a parent), master (reference data) |
| access `actions`   | view, add, edit, delete, export, detail                                                |
| `row_action.type`  | edit, form, confirm, navigate, download, delete                                        |
| column `source`    | field, status, tags, computed, path                                                    |
| column `format`    | money, percent, number, date, datetime, days (no `integer`/`decimal`: use `number`)    |
| sidebar section `type` | fields, mini_table, custom, timeline, stats                                        |
| banner `tone`      | info, warning, danger, success                                                         |
| `page.type`        | crud, detail, dashboard, custom                                                        |
| `tab.type`         | summary, related_table, timeline, fields, custom                                       |
| colours            | gray, blue, green, amber, red, purple, teal, indigo, pink                              |
| `custom_requirements[].area` | backend, frontend, integration, permission, notification, scheduled, report  |

## Top level

```yaml
spec_version: 1         # always 1
app: {...}
choice_sets: {...}      # optional
roles: [...]
pages: [...]
modules: [...]
detail_views: [...]     # optional
prototype: {...}        # open mode only
```

## `app`

`code` (snake_case), `name`, `description`, `timezone` (e.g. Asia/Kolkata),
`locale` (en-IN), `currency` (ISO code, INR), `theme: {primary, secondary}`
(hex colours; the preview uses `primary` as the brand colour),
`ui: {radius, density}` for the look, and `custom_requirements` for app-wide
needs (SSO, audit export…).

`ui` is the whole of what the look can be, as choices the preview and the
built app make the same way: `radius` sharp · rounded (default) · soft and
`density` compact · comfortable (default). "It feels cramped" is
`density: comfortable`; "make it look sharper" is `radius: sharp`. Anything
more (fonts, layouts) is not offered: say so rather than writing it as a
custom requirement.

**Open mode ("Free design") only: `app.design`.** The look lives in the
prototype, and `app.design` records it for the build, which themes the
standard screens with it:

```yaml
app:
  design:
    source: prototype
    fonts: { body: Inter, display: Inter, mono: JetBrains Mono }   # Google Fonts families
    tokens:              # concrete values, no var(); canonical names first
      brand: "#458261"
      accent: "#B58812"
      page: "#F7F7FA"
      card: "#FFFFFF"
      text: "#14171F"
      border: "#E2E4E9"
      radius: 10px
      shadow: "0 2px 4px rgba(16,18,30,.04)"
```

Don't type it by hand: `proto_design` fills it from the prototype's `:root`
tokens. Canonical names (what the build maps): brand, brand-strong,
brand-soft, accent, accent-soft, page, card, sunk, nav, text-strong, text,
text-2, text-3, text-faint, border-faint, border, border-strong, ok, ok-bg,
warn, warn-bg, bad, bad-bg, info, info-bg, radius-sm, radius, radius-lg,
shadow-sm, shadow, shadow-lg. Other tokens keep their own names. Keep
`theme.primary` equal to `tokens.brand`.

**Open mode only: `prototype`.** Which declared page each prototype screen
is. The build reads it to decide, per screen, whether the standard page is
themed with `app.design` or rebuilt from the approved prototype:

```yaml
prototype:
  screens:
    - { id: requests, maps: /pages/@requests }                 # themed list page
    - { id: request,  maps: /detail_views/@request_360 }       # themed 360
    - { id: home,     maps: /pages/@home }                     # a custom page: rebuilt
    - { id: board,    maps: /pages/@requests, rebuild: true,
        why: "User wants the exact lane layout the table can't show" }
    - { id: signin,   only: prototype, why: "The platform's sign-in is used" }
    - { id: agents,   only: prototype, why: "AI helpers come in a later version",
        menu: { group: AI, label: Agents, icon: bot } }      # greyed out in the menu
    - id: request
      maps: /detail_views/@request_360
      not_built:
        - { text: Run AI review, why: "The AI review is a later custom requirement" }
```

- Every manifest screen is listed once. `maps` is `/pages/@<code>` or
  `/detail_views/@<code>`. A screen that is not built is `only: prototype`
  with a `why`.
- Standard pages (crud, detail) are **themed**: the runtime page in the
  prototype's tokens. Custom pages are **rebuilt** from their screen.
- The YAML says everything each screen shows, in the prototype's words:
  menu items, labels, groups and order (`roles[].menu`), page titles,
  columns, status tabs (`quick_filters`), 360 tabs, sections, sidebar
  panels, dashboard blocks, buttons and field labels. `spec_mark_ready`
  renders the prototype and refuses while any of these is missing.
- `rebuild: true` (with `why`) rebuilds a standard page from its screen:
  when it shows what the YAML can't say (a stage tracker, a custom list
  row). The page keeps its data, actions and permissions.
- `menu` on an `only: prototype` screen keeps it in the menu, greyed out,
  under `group` (`roles` limits it to those roles).
- `not_built: [{text, why}]` lists what the build leaves out of a screen.
  The user sees each one before approving.

## `choice_sets`

Shared option lists keyed by code. Each option is `{id, label, color?}`;
`color` drives badge tones. A field uses one with `choices: <set code>`, or
lists options inline with the same shape.

```yaml
choice_sets:
  risk_rating:
    - { id: low,  label: Low,  color: green }
    - { id: high, label: High, color: red }
```

## `roles`

```yaml
- name: Procurement Manager
  description: Approves vendors and purchase orders.
  landing: purchase_orders          # page code opened after login
  menu:
    - { page: dashboard, icon: layout-dashboard }
    - { page: vendors, label: My Vendors, icon: building-2 }
    - group: Master Data            # collapsible menu section
      icon: database
      items:
        - { page: cities }
```

Icons are lucide icon names. A role only sees pages that are in its menu (or
reached from one, such as a 360 page) and that its entity access allows.

## `pages`

Global routes; menus refer to them by `code`.

- `crud` — the list page of one `entity` (table, create form, row actions).
- `detail` — a 360 page; `detail_view` names its spec in `detail_views`.
  `route` carries `:id`, e.g. `/app/vendors/:id`.
- `dashboard` — KPI tiles, charts, lists, tables and boards over the app's
  records, declared block by block in `blocks` (below). No code: the preview
  draws it and the build makes exactly these blocks.
- `custom` — any other screen (wizards, a dashboard the blocks cannot
  express). Name a `component` and describe it precisely in `text`; `roles`
  limits who sees it. It needs a `preview` sketch and a contract (below).

Every page has a `route` starting with `/app/` and usually a `title`.

### Other ways to show a list: `views` (crud pages)

A `crud` page may list `views`; the first is the default and a switcher
appears when there is more than one. Without `views` the page is the table.
Use them whenever the user asks for a board, cards, a calendar or a timeline
of the same records — never a custom page for that.

```yaml
views:
  - type: kanban
    group_by: status            # status, or a choice field
    columns: [todo, in_progress, done]   # optional order / subset
    card: { title: title, subtitle: project.name, fields: [assignee, due_date], badge: priority }
    move: transitions           # transitions | update | none
  - type: table
```

| `type` | keys |
|---|---|
| `table` | — (the entity's `table`) |
| `kanban` | `group_by` (required), `columns`, `card`, `move` — `transitions` moves a card only along a workflow transition the role may perform |
| `cards` | `card` (required: `title`; `subtitle`, `fields`, `badge`, `image`) |
| `calendar` | `date_field` (required), `end_field`, `title`, `color_by` |
| `timeline` | `date_field` (required), `title`, `group_by` |

### Custom screens with a preview: `preview`

Every `custom` screen gets a sketch: dashboards included (compute their KPIs
and charts from `ctx.rows`). For what nothing above can express — a workload
board per person, a seating plan, a gantt — keep the `custom` page, tab (`type: custom`) or sidebar
section (`type: custom`) with its `component` and a precise `text`, and add
`preview`: the body of a JavaScript function `ctx => html` that sketches it
from the demo data, so the user sees it. It is preview-only; the build reads
`text`. `ctx.rows(entity)` (role-scoped demo rows: field keys, `id`, `status`, links as ids), `ctx.entity(entity)` (`fields[]` with `key`, `type`, `label`, `opts` for choices; `wf.statuses[]` with `code`, `label`, `color`),
`ctx.record` and `ctx.related(entity, via)` (on tabs and panels), `ctx.fmt(row, field)`,
`ctx.esc(text)`, `ctx.icon(name)`, `ctx.tone(color)`, `ctx.role`, `ctx.user`.
Return a string; synchronous, no network. Write it as a YAML block scalar
(`preview: |`). The full contract is in `SPEC_EXTENSIONS.md` next to this file.

**Compose with `ctx.ui`** — the preview's component kit — rather than writing
markup and CSS yourself; it renders in the same style as the rest of the app.
Text arguments are escaped for you; `body`/blocks are the HTML other `ui`
calls return. `go` values are `"<page>"` or `"<page>:<id>"`.

| call | draws |
|---|---|
| `ui.stack(...blocks)` / `ui.grid(...blocks)` | blocks one under another / side by side (responsive) |
| `ui.kpis([{label, value, icon, tone, hint, go}])` | a row of stat tiles (`icon`: a lucide name, `tone`: a spec colour) |
| `ui.bars(title, [{label, value, display, tone, go}], {icon, empty})` | a horizontal bar chart in a panel |
| `ui.list(title, rows, {primary, secondary, meta, badge, go, limit, empty, icon})` | a list of records; `primary`/`secondary`/`meta` are a field key or `row => text`, `badge` is `row => ({text, tone})`, `go` is `row => "page:id"` |
| `ui.table(title, rows, [{label, value, align, badge}], {go, limit, empty, icon})` | a table of records |
| `ui.board(title, [{title, tone, items: [{title, subtitle, go}]}])` | columns of cards |
| `ui.panel(title, body, {icon, note})`, `ui.progress(done, total, label)`, `ui.badge(text, tone)`, `ui.empty(text)` | the pieces |

`ctx.today` is today's date (`YYYY-MM-DD`) for overdue and "this month"
comparisons.

```js
const { ui } = ctx;
const open = ctx.rows('task').filter(t => t.status !== 'done');
return ui.stack(
  ui.kpis([{ label: 'Open tasks', value: open.length, icon: 'list-checks', go: 'tasks' },
           { label: 'Overdue', value: open.filter(t => t.due_date < ctx.today).length, icon: 'clock', tone: 'red' }]),
  ui.grid(
    ui.bars('Open by status', ctx.entity('task').wf.statuses.map(s => ({ label: s.label, value: open.filter(t => t.status === s.code).length }))),
    ui.list('Due soonest', open.sort((a, b) => String(a.due_date).localeCompare(String(b.due_date))),
      { primary: 'title', secondary: 'assignee', meta: 'due_date', go: t => `task_360:${t.id}` })));
```

Hand-written markup (with the `pv-*` classes: `pv-cols`, `pv-col`, `pv-card`,
`pv-grid`, `pv-muted`, `pv-badge`, `pv-bar`) is only for what the kit cannot
draw; `data-go="<page>[:<id>]"` makes any element navigate.

### Dashboards: `type: dashboard`

Before writing a custom page with a sketch, check whether it is a dashboard
the blocks can say: counts and sums with conditions, records grouped by a
status or choice, lists, tables and boards of one entity. Then declare it —
the build makes it without guessing, and you write no JavaScript.

```yaml
- code: finance_home
  type: dashboard
  route: /app/finance
  title: Finance overview
  roles: [Finance]
  blocks:
    - kpis:
        - { label: Invoices to pay, value: { count: invoice, where: "status == approved" }, icon: receipt, tone: amber, go: invoices }
        - { label: Amount to pay, value: { sum: invoice.amount, where: "status == approved" }, format: money }
    - grid:
        - bars: { title: Invoices by status, entity: invoice, group_by: status }
        - list: { title: Due soonest, entity: invoice, where: "status in [submitted, approved]",
                  sort: due_date, primary: invoice_no, secondary: purchase_order, meta: amount, badge: status, limit: 8 }
```

Each block is exactly one of:

| block | keys |
|---|---|
| `kpis` | a list of tiles: `label`, `value` (`count: <entity>`, or `sum`/`avg`/`min`/`max: <entity>.<field>`, with optional `where`), `format` (number, money, percent, days), `icon`, `tone`, `hint`, `go` (a page) |
| `bars` | `entity`, `group_by` (status, a choice or a link field), `value: {sum: field}` (default: count), `where`, `title`, `tone`, `format` |
| `list` | `entity`, `primary` (required), `secondary`, `meta`, `badge` (status or a choice), `where`, `sort` (`-field` for newest first), `limit`, `go`, `empty` |
| `table` | `entity`, `columns` (field paths), `where`, `sort`, `limit`, `go`, `empty` |
| `board` | `entity`, `group_by`, `card: {title, subtitle}`, `where`, `limit`, `go` |
| `grid` / `stack` | a list of blocks, side by side / one under another |
| `panel` | `title`, `icon`, `blocks` |

Every count, sum and list is scoped to the signed-in role's rows, as on list
pages. Rows open `go` (a 360 page gets the row's id) or else the record's own
360 page. What the blocks cannot say — "this month", trends by month, numbers
from two entities combined — is a `custom` page.

### Custom pages in open mode: `reason`

A free-design prototype makes every screen look custom; the build still
draws record screens with the runtime and themes them. So every prototype
screen that shows records maps to a crud page, a `detail_views` page or a
dashboard, however it looks. A `type: custom` page is for what none of those
can show, and says why:

```yaml
  - code: territory_map
    type: custom
    reason: A map of HCP visits by territory; no list, record page or dashboard block draws a map.
    acceptance: [...]
```

`spec_mark_ready` lists every custom page with its reason in open mode, and
refuses a custom page without one.

### Contracts for custom work

A custom page, custom tab or custom sidebar panel, and every
`custom_requirements` item, is written by hand in the build. Each carries a
contract, so the build knows what "done" means and its tests check it:

```yaml
  data:                                   # what it reads (each role's rows)
    - { entity: task, where: "status not_in [done]" }
    - { entity: vendor_document, via: vendor }        # on a 360 tab or panel
  interactions:                           # what the user does with it
    - { event: card_click, go: task_360 }
    - { event: drag_card, update: { entity: task, field: assignee }, roles: [Manager] }
  states: { empty: No open tasks. Everyone is clear. }
  acceptance:                             # required: testable, in the user's words
    - A manager sees one column per active team member.
    - Dragging a task to another column reassigns it.
  refs: ["doc:2#p3"]                      # the document page it follows, if any
```

A custom requirement says when it happens (required for `notification` and
`scheduled`) and how to tell it was done:

```yaml
custom_requirements:
  - area: notification
    title: Approval email
    text: Email the vendor contact their portal invite when the vendor is approved.
    trigger: { event: transition, transition: approve }   # create | update | delete | transition | tag | schedule (+ cron)
    acceptance:
      - Approving a vendor sends one email to the vendor contact, with the portal invite.
    preview: { toast: "Approval email to {legal_name}'s contact" }   # shown in the preview when it happens
```

Write `event`, never `on` (YAML reads `on` as true). `spec_mark_ready` is
refused while a custom part has no `acceptance` or a notification or
scheduled requirement has no `trigger`.

## `modules` and entities

A module is one backend folder: `code`, `name`, `description`, `entities`.

### Entity keys

| Key        | Meaning                                                                                 |
|------------|-----------------------------------------------------------------------------------------|
| `code`, `name`, `plural` | identity; `plural` defaults to name + "s"                                  |
| `kind`     | hero, transactional, child, master                                                      |
| `display`  | the field used as the record's label (and in link dropdowns)                            |
| `parent`   | children only: `{entity, field}` — the FK to the parent; managed from the parent's 360  |
| `app_user` | the record owns a login: `{role, name, email, mobile, create_on}`                       |
| `fields`   | list of `- key: {field}`                                                                 |
| `validation` | `rules` (cross-field) and `duplicate_check`                                           |
| `access`   | per role: `{actions, rows}`                                                             |
| `workflow` | `statuses`, `transitions`, `tags`                                                       |
| `form`     | `create`, `edit`                                                                        |
| `table`    | the list page                                                                           |
| `custom_requirements` | anything the spec cannot express, as `{area, title, text, trigger, acceptance}` |

### Fields

Every key except `type` is optional:

`label`, `required`, `readonly` (system-set, never on a form), `unique`,
`max_length`, `min`, `max`, `pattern` + `pattern_msg`, `help` (under the
input), `tooltip`, `placeholder`, `default` (`today` for dates),
`choices` (choice/multi_choice), `to` (link/multi_link: an entity code or
`app_user`), `display` (which attribute of the linked record to show),
`limit_choices` (expression filtering link options; `form.<field>` refers to
another field on the same form), `on_delete` (cascade | protect | set_null),
`auto: {sequence: "VEN-{00000}"}` (`{YY}`, `{YYYY}` allowed),
`computed` (plain-language formula, with `readonly: true`),
`accept: [pdf, jpg]` and `max_size_mb` (file/image).

### Validation

```yaml
validation:
  rules:
    - when: vendor_type == manufacturer
      require: [gstin]
      message: GSTIN is mandatory for manufacturers.
    - when: end_date is_set
      require_expr: end_date > start_date
      message: End date must be after the start date.
    - text: The PO must not exceed the vendor's credit limit.
      message: This PO exceeds the credit limit.
      on_fail: warn                    # block (default) | warn
  duplicate_check:
    scope: { where: "status not_in [rejected]" }
    rules:
      - { match: [gstin], compare: exact, on_match: block, message: ... }
      - { match: [legal_name, city], compare: fuzzy, threshold: 0.85, on_match: warn, message: ... }
```

`compare`: exact | normalised | fuzzy. `on_match`: block | warn.

### Access

Keyed by role name. A role not listed has no access to the entity.

```yaml
access:
  Procurement Executive: { actions: [view, add, edit, export, detail] }
  Finance:               { actions: [view, detail], rows: { where: "status == approved" } }
  Vendor User:           { actions: [view, detail], rows: { own: id } }
```

`rows`: `all` (default), `created_by_me`, `{own: <path>}` (the path resolves
to the record linked to the current user's login, e.g. `own: vendor` or
`own: purchase_order.vendor`), `{where: <expression>}`, or `{text: ...}`.
`detail` lets the role open the entity's 360 page.

### Workflow

```yaml
workflow:
  statuses:
    - { code: draft, label: Draft, color: gray, initial: true }
    - { code: approved, label: Approved, color: green }
    - { code: rejected, label: Rejected, color: red, final: true }
  transitions:
    - name: approve                    # code: approve_condition / approve_done
      label: Approve
      from: pending_approval           # one status or a list
      to: approved
      roles: [Procurement Manager]
      primary: true                    # main button on the 360 header
      tone: danger                     # destructive styling
      confirm: Approve this vendor?
      form:                            # fields collected in the transition modal
        - approval_note: { type: long_text }
      condition: { text: The approver is not the creator (maker-checker). }
      condition_msg: Another manager must approve a vendor you created.
      on_done: Set approved_on = today and approved_by = current user.
    - { name: expire, label: Expire, from: active, to: expired, trigger: system,
        text: Nightly when end_date < today. }   # system: run by code, no button
  tags:
    - code: preferred
      label: Preferred
      color: indigo
      enable:  { roles: [Procurement Manager], condition: status == approved }
      disable: { roles: [Procurement Manager] }
    - { code: overdue, label: Overdue, color: amber, system: true, text: Set when ... }
```

Exactly one status should be `initial`. Every user transition names its
`roles`; a transition without roles can be run by anyone.

### Forms

```yaml
form:
  create:
    roles: [Procurement Executive]     # who sees the Add button (with access `add`)
    title: Add Vendor
    sections:                          # or a flat `fields: [...]`
      - title: Company
        fields: [legal_name, vendor_type]
      - title: Commercials
        fields:
          - payment_terms
          - credit_limit: { show_when: vendor_type != service }   # per-form override
    on_create: Write "Vendor created" to the activity log.
    after_create: vendor_360           # where to land after saving
  edit:
    same_as: create
    roles: [Procurement Executive, Procurement Manager]
    readonly_when:
      - { when: "status in [approved]", fields: [legal_name, gstin] }
    editable_in: [draft, pending_approval]   # edit is hidden in other statuses
```

Form fields must be fields of the entity. A child's parent link is prefilled
from the parent's 360 tab, so leave it off the child's form.

### Table

```yaml
table:
  columns:
    - legal_name:  { label: Name, searchable: true, sortable: true, link_to: vendor_360 }
    - category:    { label: Category, display: name, filterable: true }
    - status:      { source: status, label: Status, filterable: true }
    - tags:        { source: tags, label: Tags }
    - open_value:  { source: computed, label: Open PO value, format: money, shows: "Sum of ..." }
    - vendor:      { source: computed, path: purchase_order.vendor.legal_name }
    - risk_rating: { label: Risk, roles: [Procurement Manager] }
  default_sort: -created_at
  page_size: 25
  quick_filters:
    - { label: Pending my approval, where: status == pending_approval, roles: [Procurement Manager], default: true }
  row_click: vendor_360              # a detail_view code | drawer | none
  add_button: Add Vendor
  row_actions:
    - { key: edit, label: Edit, type: edit, show_when: status == draft }
    - { key: open_360, label: Open 360, type: navigate, to: vendor_360 }
    - { key: resend, label: Resend Invite, type: confirm, confirm: Send again?, on_done: ... }
    - { key: update_bank, label: Update Bank, type: form, form: [ { ifsc: { type: text } } ], on_done: ... }
    - { key: pdf, label: Download PDF, type: download, text: The PO PDF with lines and terms. }
  footer_totals: [amount]
  group_by: doc_type
```

Column `source`: field (default), status, tags, computed (describe it in
`shows`) or a `path`. Workflow transitions and tag toggles are added to the
row menu automatically.

## `detail_views` (360 pages)

One per hero entity that needs a 360 page; a `detail` page points at it.

```yaml
- code: vendor_360
  hero: vendor
  title: "{legal_name}"
  back_to: vendors                     # page code
  layout: header_tabs_sidebar          # header_tabs | header_tabs_sidebar | header_sidebar_tabs_left
  roles: [...]
  header:
    avatar: { image: logo, fallback_initials: legal_name }
    title: legal_name
    subtitle: ["{vendor_ref}", "{city.name}"]
    badges: [ { source: status }, { source: tags }, { field: risk_rating, prefix: "Risk: " } ]
    facts:
      - { label: GSTIN, field: gstin, copyable: true }
      - { label: Primary contact, path: "vendor_contact[is_primary].name", fallback: "—" }
    actions:
      transitions: true
      tags: true
      buttons:
        - { key: new_po, label: New PO, type: create_related, entity: purchase_order, prefill: { vendor: hero } }
        - { key: edit, label: Edit, type: edit }
        - { key: resend_invite, row_action: resend_invite }
    banners:
      - { show_when: status == on_hold, tone: warning, text: "On hold: {hold_reason}" }
  stats:
    - { label: Open POs, value: { count: purchase_order, via: vendor, where: "status not_in [closed]" }, tone: blue, link_to_tab: purchase_orders }
    - { label: PO value, value: { sum: purchase_order.total_amount, via: vendor }, format: money }
  sidebar:
    - { type: fields, title: Company, fields: [legal_name, gstin] }
    - { type: custom, title: Checklist, text: ... }
  tabs:
    - { code: overview, label: Overview, type: summary, sections: [ { title: Commercials, columns: 2, fields: [...] } ] }
    - code: contacts
      label: Contacts
      type: related_table
      entity: vendor_contact
      via: vendor                      # FK path from the related entity to the hero
      columns: inherit                 # or a list of column keys
      add: { label: Add Contact, prefill: { vendor: hero } }
      row_actions: inherit
      row_click: drawer
      count_badge: true
      empty_state: { title: No contacts yet, text: ..., cta: add }
    - code: activity
      label: Activity
      type: timeline
      sources:
        - { entity: vendor, events: [created, updated, transition, tag] }
        - { entity: purchase_order, via: vendor, events: [created, transition] }
  states:
    not_found: { title: Vendor not found, back_to: vendors }
```

`via` must be a link path on the tab's entity that ends at the hero
(`purchase_order.vendor` for invoices under a vendor). Every block accepts
`roles` and `show_when`.

## What the checks enforce

Structural (a change is refused): unknown keys at the fixed levels (app,
role, page, module, entity, workflow, table, form), wrong types, values outside
the enums above.

Cross-references (errors until fixed): menu and landing pages exist; every
role named anywhere is declared; pages point at existing entities and detail
views; transitions and `editable_in` use statuses of their own workflow; form
fields and `display` are fields of the entity; `choices: <code>` names a
declared choice set; link fields have `to`; choice fields have `choices`;
codes, names and keys are unique in their scope.

Build checks (errors until fixed): the build skill's own checker runs with
every validation and reports what the build would stop on — prose cut at an
unquoted comma, unknown formats or expression operators, module link cycles,
navigate targets and row scoping as described under "Writing YAML the build
reads the same way". Its warnings are advice: transition conditions without a
`condition_msg`, required fields missing from the create form, tabs a role
cannot see.

Completeness (warnings while drafting, errors at approval): `app.code` and
`name`, at least one role with a menu, at least one page and module, and every
entity's `code`, `name`, `kind`, `fields` and `access`.
