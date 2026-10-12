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
| `ctx.entity(entity)` | the entity's normalised definition: `fields[]` (`key`, `type`, `label`, and `opts` — choice options `{id, label, color}`), plus its workflow (statuses, transitions, tags) |
| `ctx.record` | on a custom tab or panel: the record the 360 page is showing |
| `ctx.related(entity, via)` | on a tab or panel: rows of `entity` whose link field `via` points at `ctx.record` |
| `ctx.fmt(row, field)` | a field's display value (choices, links, money, dates) as plain text |
| `ctx.esc(text)` | HTML-escape |
| `ctx.icon(name)` | a lucide icon as inline SVG |
| `ctx.tone(color)` | `[background, foreground]` for a spec colour name |
| `ctx.role`, `ctx.user` | the role and demo user being previewed |

Markup may use the preview's classes: `pv-cols`, `pv-col`, `pv-card`,
`pv-grid`, `pv-muted`, `pv-badge`, `pv-kpis`, `pv-kpi`, `pv-bar`, and the App
Studio `z-*` classes. `data-go="<page>[:<id>]"` on any element navigates to that
page (and record) when clicked. An error in the function is shown in place of
the component, with its message; it never breaks the rest of the preview.

## What the build should do with them

- `views`: build the declared views with the same access and row scoping as
  the table (the kanban's `move` maps onto the workflow transitions / field
  update it names).
- `preview`: treat it as a visual reference for the custom component named in
  `component`; `text` remains the requirement. The code itself is not built.
