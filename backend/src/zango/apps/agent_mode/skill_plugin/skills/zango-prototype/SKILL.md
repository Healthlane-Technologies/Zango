---
name: zango-prototype
description: Open prototype mode of Agent Mode ("Free design"). How to write the app's working HTML prototype in parts with the mcp__spec__proto_* tools - the parts layout, the manifest, the ZAS runtime (router, personas, store, actions, helpers), the first-draft order, screen briefs for the screen-writer agent, and the design bar - and how to keep it in step with the YAML spec.
version: 1.0.0
---

# Open prototype

In open mode the preview the user sees is a working prototype **you write**, in any look.
It must feel like the real product a senior product designer would ship for this business:
personas with their own home, real-looking records, working actions, every state drawn.
The YAML spec still says what gets built; the prototype says how it looks and flows.

You never write the prototype as one file. You write **parts**; the server assembles them
into one page and the preview reloads after every write.

## Parts

| Part | Holds | Who writes it |
|---|---|---|
| `manifest.json` | title, screens, roles, personas, fonts, libraries | you, first |
| `tokens.css` | the palette, type, radii, shadows, spacing as CSS variables | you |
| `app.css` | layout and shared components (shell, cards, tables, forms, badges) | you |
| `data.js` | sample records: `ZAS.seed({collection: [...]})` | you |
| `shell.js` | nav, header, user menu: `ZAS.shell(...)` | you |
| `screens/<id>.js` | one screen: `ZAS.screen('<id>', ...)` and its actions | you or a screen writer |
| `screens/<id>.css` | rules only this screen needs (optional) | same as its screen |
| `lib/*.js` | shared helpers several screens use (optional) | you |

Limits: 150 KB per part, 2 MB in all. JS parts must parse and `manifest.json` must be valid JSON,
or the write is refused. Paths are lower-case: `screens/request.view.js`.

## manifest.json

```json
{
  "title": "Lab Sample Tracker",
  "currency": "USD",
  "fonts": ["https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap"],
  "libraries": ["https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"],
  "roles": {"tech": "Lab technician", "lead": "Lab lead", "qa": "Quality"},
  "personas": {"tech": {"name": "Priya Raman"}, "lead": {"name": "Tomás Ortega"}, "qa": {"name": "Hanna Berg"}},
  "default_role": "tech",
  "home": {"tech": "bench", "lead": "overview"},
  "screens": [
    {"id": "overview", "title": "Overview", "icon": "layout-dashboard", "roles": ["lead", "qa"]},
    {"id": "bench", "title": "My bench", "icon": "flask-conical", "roles": ["tech"]},
    {"id": "samples", "title": "Samples", "icon": "test-tubes", "group": "Work"},
    {"id": "sample", "title": "Sample", "record": "samples", "parent": "samples"},
    {"id": "signin", "title": "Sign in", "only": "prototype", "nav": false}
  ]
}
```

- `screens[]`: `id` (its part is `screens/<id>.js`), `title`, optional `icon` (a Lucide name),
  `group` (nav section), `roles` (who can open it; all when absent), `record` (a record page:
  opened with a record id, kept out of the nav; `sample` names the id of a typical record, which
  the build's snapshots open it with: required on imported pages, else the first row of the
  `record` collection is used), `parent` (highlights its list in the nav),
  `nav: false`, and `only: "prototype"` for screens the real app will not have (sign-in,
  onboarding tours, fake integrations).
- `fonts`: Google Fonts CSS URLs only. `libraries`: scripts from cdnjs, cdn.jsdelivr.net/npm or
  unpkg, with an exact version. Nothing else loads: no other hosts, no fetch to APIs, no images
  by URL (use inline SVG, CSS, or `data:` URIs).
- Lucide icons are already loaded: `ZAS.I('name', size)`.

## The ZAS runtime (already on every page)

```js
ZAS.seed({samples: [...], batches: [...]})          // data.js
ZAS.shell({render(ctx, body) { return `...${body}...` }, mount(root, ctx) {}})
ZAS.screen('samples', {
  render(ctx) { return `<h1>...</h1>` + ctx.table({...}) },   // returns HTML
  mount(el, ctx) {}                                          // optional: charts, focus
})
ZAS.on('approve', (data, el, event, ctx) => { ... })        // data-act="approve" data-id="S-12"
```

- **ctx**: `screen`, `role`, `roleLabel`, `persona` ({code, label, name…}), `roles`, `record` (id or
  null), `params`, `nav` ([{id, title, icon, group, on}] for this role), `meta` (this screen's
  manifest entry), `M` (manifest), `store`, `files`, `go`, `back`, `toast`, and helpers
  `h` (escape every value you interpolate), `I`, `fmt` (`num`, `money`, `date`, `rel`), `pill(text,
  tone)` (tones ok/warn/bad/info), `table({columns:[{label, key | render, align}], rows, rowAct,
  empty})`, `tabs(items, active, act)`, `field(label, inputHtml, hint)`, `initials(name)`.
- **Store** (in memory, reset on reload): `list(c, filterFn)`, `get(c, id)`, `put(c, doc)`,
  `patch(c, id, fields)`, `remove(c, id)`. Every change re-renders the page.
- **Files**: `ZAS.files.add(file)` → `{id, name, url…}` for uploads in the preview;
  `fetch('/_blob/<id>')` works.
- **Navigation**: `ZAS.go('sample', {record: 'S-12'})`, `ZAS.back()`; in markup
  `data-act="go" data-go="samples"` (plus `data-record`). Persona switch: `ZAS.go(home, {role})`;
  a "Viewing as" switcher is drawn for you (turn it off with `"persona_bar": false` when the shell
  draws its own).
- **Actions**: any element with `data-act` calls its `ZAS.on` handler with its `data-*` values;
  inputs and selects with `data-act` fire on change (`data.value`), and `<form data-act>` on
  submit (`data.form`). Overlays: `ZAS.drawer(html)`, `ZAS.modal(html)`, `false` closes;
  `data-act="zas-close"` closes too. `ZAS.toast('Approved', 'ok')`.
- Each screen's HTML is wrapped in `<div data-zas-screen="<id>">`. The runtime's `z-` classes are
  plain on purpose: restyle them in `app.css`.
- You may skip all of this and write your own app, as long as the manifest is right and the page
  calls `ZAS.ready({go(screen, {role, record}) {...}})` and reports `ZAS.at(screen, {role, record})`
  after each navigation.

## The first draft

1. **Direction.** From the subject, decide the look before writing: a palette of 5-7 tokens with
   a deliberate hue for the brand and tinted neutrals, a type pairing (display + text, plus mono
   for IDs and figures), radius, density, one signature treatment (a status rail, a stage stepper,
   a ledger-style table). Write it into `tokens.css`. Never a gray page with one blue accent.
2. **Write the frame yourself**, in this order: `manifest.json` → `tokens.css` → `app.css` →
   `data.js` → `shell.js` → the home screen of the main persona. The user should see their app
   within a few minutes.
3. **Hand out the other screens** to the screen-writer agent (Agent tool, `subagent_type:
   "screen-writer"`), several in ONE message so they run in parallel. Write each brief like this:

   ```
   Screen `samples` (screens/samples.js), title "Samples". Personas: tech, lead, qa.
   Purpose: every sample in the lab, filtered by stage; the queue for the tech.
   Records: store `samples` (id, label, matrix, batch, received, due, stage, assignee, flags).
   Show: stage chips with counts (Received, In prep, On instrument, Review, Released, Rejected),
   a table (ID mono, label, matrix, batch, due with overdue in red, stage pill, assignee avatar),
   rows open `sample`. Lead sees a "Reassign" action per row.
   Actions: data-act="stage-filter" (chip), "open" (row) → ZAS.go('sample', {record: id}).
   States: empty filter result; overdue; the tech sees only their own by default.
   Use: classes .page-head, .chips, .card, .tbl from app.css; tokens --brand, --ok, --warn, --bad.
   ```
4. **Review** what the writers report. Fix shared parts yourself (they must not edit them),
   check the manifest has every screen, then look at the result once.
5. **Write the YAML in the same turn** (spec tools): roles = personas, entities = the store's
   collections and their fields, pages = screens (record screens map to the entity's detail view),
   workflow = the stages and the actions that move them, custom requirements = automation the
   prototype only fakes (AI review, reminders, integrations).
6. **Record the look**: `proto_design` sets `app.design` (fonts + tokens) from `tokens.css`. Name
   tokens the canonical way where you can (`--brand`, `--accent`, `--page`, `--card`, `--text`,
   `--text-2`, `--border`, `--ok`/`--ok-bg`…, `--radius`, `--shadow`; full list in SCHEMA.md,
   app.design) so the build maps them without guessing.
7. **Record the mapping** in the YAML's `prototype.screens`, one entry per manifest screen:
   `{id: requests, maps: /pages/@requests}`, `{id: request, maps: /detail_views/@request_360}`, or
   `{id: signin, only: prototype, why: "…"}`. The build themes standard pages and rebuilds custom pages
   from their screen. `rebuild: true` with a `why` rebuilds a standard page too: when it shows what
   the YAML can't say.
8. **Cover every screen** (below, "The YAML covers the prototype"). `spec_mark_ready` renders the
   prototype for every persona and refuses while the YAML leaves anything out.

## Runtime first: how screens map

The prototype may look like anything, but the build draws record screens with the standard
runtime (crud lists, boards, forms; detail/360 record pages; dashboards) and themes them with
your tokens. So, however custom a screen looks:

- a list, queue, board or table of records → a **crud page** on that entity (views for kanban,
  filters, chips);
- a record page, with tabs or side panels → a **`detail_views`** page;
- a home with KPIs, charts and "your work" lists → a **dashboard** page;
- a create/edit form → the entity's form on its crud page.

Only what none of these can show (a map, a planner, a drag-and-drop canvas) becomes a
`type: custom` page, with a `reason` naming what the declared pages can't do, and its contract.
`spec_mark_ready` refuses a custom page without a reason and lists the others for the user.

## The YAML covers the prototype

The build follows the YAML, never the prototype's code, so whatever the YAML leaves out is lost.
For every screen, say in the YAML, with the prototype's own words:

| The prototype shows | The YAML says it in |
|---|---|
| menu items, their labels, groups and order | `roles[].menu` (each role's, in the prototype's order) |
| a menu item for a screen not built | that screen's `prototype.screens` entry: `menu: {group, label, icon}` (shown greyed out) |
| a page heading | `pages[].title` |
| list columns, status tabs or filter chips | `table.columns`, `table.quick_filters` |
| where a list row opens (its record, a parent record on a tab, a drawer) | `table.row_click`: the 360, `<view>#<tab>`, or `drawer` |
| 360 tabs, sections, side panels, header buttons, banners | `detail_views[]`: `tabs`, summary `sections`, `sidebar`, `header.actions.buttons`, `banners` |
| home cards, "your work" lists, charts | dashboard `blocks`: `kpis`, `table`, `bars` |
| buttons | `add_button`, `row_actions`, `header.actions.buttons`, or the transition's label |
| field labels | the field's `label` |

Where the YAML can't say it (a stage tracker, a custom list row), mark the screen `rebuild: true`
with a `why` naming it; the build ports it from the screen. Only what the first version won't have
goes in that entry's `not_built: [{text, why}]`: the user sees the list before approving.

## Later turns

- `proto_outline` first, then `proto_find` the text the user means (a `[Preview: …]` note names
  the screen and persona), `proto_read` around it, and `proto_patch` the smallest change.
- A new screen: add it to `manifest.json` (patch), then write `screens/<id>.js` (yourself, or a
  writer when there are several).
- Rewrite a whole part only when most of it changes.
- Change the YAML with it whenever the change is not purely visual.

## The bar

- **Personas, not a menu.** Each role lands on its own home: "your work" first, counts that
  matter to that role, what is waiting on them.
- **Real content.** Names, places, amounts, dates and IDs in the business's own conventions,
  10-30 records per main collection, spread across every stage, some overdue, one or two odd
  cases. Dates relative to today (`new Date(Date.now() - 3*864e5)`). Never lorem ipsum, "Test 1",
  or round numbers everywhere.
- **Every state.** Empty lists with a next step, pending/approved/rejected/sent back, overdue,
  read-only for roles that cannot act, a confirmation for destructive actions, a toast after each
  action.
- **Working flows.** Every button the brief names does something in the store, so the user can
  walk the process end to end as each persona.
- **Information design.** Summary before detail; state shown as pills, rails and steppers, not
  only words; mono and tabular figures for IDs and amounts; one primary action per screen.
- **Craft.** Consistent spacing scale, aligned edges, hover and focus states, no horizontal page
  scroll at 1280 px, readable at 390 px.
- **Copy** in the user's words: "Send back to requester", not "Update status".

## Importing an uploaded HTML page

When the user uploaded their app as an `.html` file, it is the prototype. Do not redraw it.

1. `proto_import("<file name>")`. The page's styles, scripts and markup become `imported/styles.css`,
   `imported/script-NN.js` and `body.html`, unchanged, plus a starter `manifest.json` with
   `"source": "imported"`. Fonts and allowed libraries move to the manifest.
2. Read how the page navigates (`proto_find` for its nav items, its render function, its persona
   or role state). Fill `manifest.json`: `screens` (ids and titles from its nav sections; record pages
   with `record` and a `sample` id of a real record in its data; sign-in, tours and fake integrations with `"only": "prototype"`), `roles` from its
   personas.
3. Write one small part, `zas-bridge.js`, that connects the page to the preview:

   ```js
   ZAS.ready({go(screen, {role, record}) {
     // use the page's own state and render function, e.g.:
     if (role) S.who = role; secn = screen; render();
   }});
   // after the page's own navigation, report where the user is:
   // ZAS.at(secn, {role: S.who})
   ```

   Patch the page only where needed to call `ZAS.at` after it navigates (one line in its router).
4. Write the YAML from what the page shows: personas → roles, its records → entities and fields,
   its stages and approve/send back/decline → workflow transitions with role policies, uploads →
   file fields, automation it fakes → custom requirements. Map its screens the runtime-first way
   (above) and record them in `prototype.screens`, then call `proto_design`: it reads the page's own
   `:root` variables. Then cover every screen ("The YAML covers the prototype"): its menu, columns,
   tabs, sections and buttons, in the page's own words.

The page keeps its own look. Imported parts may be up to 1 MB each.

See `references/example/` for a complete small prototype in this format (a fictional lab).
