# Spec extensions: list views and preview components

Two additions to the Zango App Spec v1 that let a requirement ask for custom
UI — "make the task list a kanban", "a workload board per person" — and see
it in the preview before anything is built. The preview (App Studio) renders
both. **The build skill (`zango-app-studio`) and its checker need to accept and
build them**: this file is the contract.

## 1. `views` on a crud page

A `crud` page may list the ways its records are shown. The first is the
default; with more than one, the page shows a switcher. Without `views` the
page is the usual table.

```yaml
pages:
  - code: tasks
    type: crud
    entity: task
    title: Tasks
    route: /app/tasks
    views:
      - type: kanban
        group_by: status              # status, or a choice field of the entity
        columns: [todo, in_progress, done]   # optional: order / subset of the group values
        card:
          title: title                # field path (dot paths across links allowed)
          subtitle: project.name      # optional
          fields: [assignee, due_date] # optional, shown as small rows
          badge: priority             # optional, a choice field shown as a coloured badge
        move: transitions             # transitions | update | none (default: transitions for status, update for a choice field)
      - type: table                   # the entity's table, as without `views`
```

| `type` | keys | notes |
|---|---|---|
| `table` | — | the entity's `table` (columns, filters, row actions) |
| `kanban` | `group_by` (required), `columns`, `card`, `move` | `move: transitions` moves a card only along a workflow transition the role may perform (and opens its form, if it has one); `update` sets the choice field; `none` is read-only |
| `cards` | `card` (`title` required, `subtitle`, `fields`, `badge`, `image`: an image field) | a responsive grid |
| `calendar` | `date_field` (required, date/datetime), `end_field`, `title`, `color_by` (status or choice field) | month grid; records without a date are listed aside |
| `timeline` | `date_field` (required), `title`, `group_by` (optional lanes) | records along time |

Every view respects the entity's `access` (row scoping) and the page's `roles`
exactly like the table does; row clicks open the same 360 page or drawer.

## 2. `preview` on custom pages, tabs and panels

Anything the spec cannot express stays a `custom` page / tab / sidebar
section, with its `component` name and prose `text` for the build — as today.
It may now also carry `preview`: the body of a JavaScript function, written by
the requirement agent, that draws the component in the preview from the demo
data. It is a **sketch for the user and a reference for the build**, never
shipped code.

```yaml
  - code: workload
    type: custom
    title: Team workload
    route: /app/workload
    component: WorkloadBoard
    roles: [Manager]
    text: >
      One column per team member with their open tasks, ordered by due date;
      overdue tasks highlighted. Drag a task to another person to reassign it.
    preview: |
      const people = ctx.rows('team_member');
      const tasks = ctx.rows('task').filter(t => t.status !== 'done');
      return `<div class="pv-cols">${people.map(p => `
        <div class="pv-col"><h4>${ctx.esc(p.name)}</h4>
          ${tasks.filter(t => t.assignee === p.id).map(t => `
            <div class="pv-card" data-go="task_360:${t.id}">${ctx.esc(t.title)}
              <span class="pv-muted">${ctx.fmt(t, 'due_date')}</span></div>`).join('')}
        </div>`).join('')}</div>`;
```

The function receives `ctx` and returns an HTML string. It runs synchronously
inside the preview's sandbox (no network, no storage, no timers).

`ctx`:

| member | what it is |
|---|---|
| `ctx.rows(entity)` | the demo records of an entity, scoped to the role being previewed |
| `ctx.entity(entity)` | the entity's normalised definition: `fields[]` (`key`, `type`, `label`, and `opts` — choice options `{id, label, color}`), plus `wf` when it has a workflow: `wf.statuses[]` and `wf.tags[]` (`code`, `label`, `color`), `wf.trs[]` |
| `ctx.record` | on a custom tab or panel: the record the 360 page is showing |
| `ctx.related(entity, via)` | on a tab or panel: rows of `entity` whose link field `via` points at `ctx.record` |
| `ctx.fmt(row, field)` | a field's display value (choices, links, money, dates) as plain text |
| `ctx.esc(text)` | HTML-escape |
| `ctx.icon(name)` | a lucide icon as inline SVG |
| `ctx.tone(color)` | `[background, foreground]` for a spec colour name |
| `ctx.role`, `ctx.user` | the role and demo user being previewed |
| `ctx.today` | today's date, `YYYY-MM-DD` |
| `ctx.ui` | the component kit below |

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

An error in the function is shown in place of
the component, with its message; it never breaks the rest of the preview.

## What the build should do with them

Until the skill's runtime ships a component for a view type, the platform has
the build agent write that view as a custom view for the app
(`references/views.md` in the `zango-app-studio` skill) and checks it is there (`views` in the build
report). A view counts as shipped by the skill once `spec_check.py` carries it
into `spec.ui.json` (`pages.<code>.views[].type`); the platform then leaves it
to the skill.

- `views`: build the declared views with the same access and row scoping as
  the table (the kanban's `move` maps onto the workflow transitions / field
  update it names).
- `preview`: treat it as a visual reference for the custom component named in
  `component`; `text` remains the requirement. The code itself is not built.

## 3. `type: dashboard` pages

A page of declared blocks (`kpis`, `bars`, `list`, `table`, `board`, `grid`, `stack`, `panel`;
SCHEMA.md, "Dashboards"). The preview draws it from the demo data with the role's row scoping;
`spec_check.py` checks every entity, field, page and expression in it.

Until the runtime ships a dashboard component, `spec_check` resolves a dashboard to a `custom`
page (component `Dashboard<PascalCode>`) whose hole text lists the blocks exactly; the blocks
themselves are in `spec.resolved.json` `pages.<code>.blocks`. The build agent writes it as a
custom page (slot plus data hook) and must build every block as declared: same counts and sums,
same conditions, same order, each scoped to the signed-in role — nothing added.

## 4. Contracts for custom work

Custom pages, tabs and panels may carry `data`, `interactions` (`event`, `go`, `update`,
`transition`, `row_action`, `does`, `roles`), `states` (`empty`, `error`, `no_access`),
`acceptance` and `refs`; custom requirements may carry `code`, `trigger` (`event`: create,
update, delete, transition, tag, schedule; with `transition`, `tag` or `cron`), `acceptance` and
`preview.toast`. `spec_check` appends them to the hole text ("Reads…", "Interactions…",
"Trigger…", "Acceptance (test each): (1)…"): each acceptance line is a test the build writes, and
a scheduled requirement's `cron` is its `# zas:schedule` line. The platform refuses to mark a spec
ready while a custom part has no `acceptance`.

## 5. `app.ui`

`radius` (sharp, rounded, soft) and `density` (compact, comfortable). `spec_check` validates them
and writes them to `spec.ui.json` `app.ui`; the runtime sets `data-zas-radius` and
`data-zas-density` on `<html>` and `tokens.css` redefines its radius and density tokens. The
preview applies the same choices.
