# Declared list views (`pages[].views`)

A `crud` page may declare how its records are shown: `views: [{type: kanban, …}, {type: table}]`.
The first is the default; with more than one the page shows a switcher. The user saw exactly this
in the App Studio preview and approved it, so **every declared view must be in the built app**.

`table` is the entity's table (`makeListPage`). For every other type, this runtime may or may not
ship a ready component. The platform works that out before you start and lists what is left in
**`.zas/views.md`**: each row there is a view **you write as a custom view**. No `.zas/views.md`,
or an empty one, means there is nothing to do here.

## What you write, per row of `.zas/views.md`

1. `frontend/src/custom/views/<page>_<type>.tsx` — default-export a component taking `ViewProps`
   (from `./ViewsPage`). Start the file with `// zas:view <page>.<type>`.
2. In `src/custom/pages/index.ts`, export the page through `makeViewsPage` instead of
   `makeListPage`, passing every custom view of that page:

   ```ts
   import { makeViewsPage } from "../views/ViewsPage";
   import TasksKanban from "../views/tasks_kanban";
   export const Page_tasks = makeViewsPage("tasks", { kanban: TasksKanban });
   ```

`ViewsPage.tsx` and `views.json` in that folder are the platform's: read them, never edit them.
`makeViewsPage` renders the switcher, remembers the user's choice, keeps the table as it is and
leaves the record's 360 route to the table page. Your component renders everything inside the
page for its view.

## Matching the approved page

The user approved this page in the preview, switcher included. `.zas/bundle/index.md` lists it
under "Standard screens" with a screenshot per view (`screens/pages.<page>.views.<i>/shot.*.png`)
and where the switcher sits (`layout.json`). **Read every one of them before writing the view.**

- **Switcher in the toolbar** (the preview's place: a segmented control at the toolbar's right,
  before Export): pass `{ switcher: "toolbar" }` as `makeViewsPage`'s third argument. The table
  view then shows it in its own toolbar; your view gets `props.placement === "toolbar"` and renders
  `props.switcher` in its `zas-tb` toolbar row, after the `zas-sp` spacer and before Export.
- **Switcher above the page**: leave the third argument out (tabs above the page).
- Lay your view out as its screenshot shows it: the same header, toolbar (search, filters, the
  switcher, Export), columns or cards, and what each card shows. Compose it from the zas kit; this
  is arranging, not new design.

The parity check compares the built page with each screenshot (switcher placement, and the pair
of screenshots goes to the look round).

## The component

`props`: `pageCode`, `title`, `entity`, `endpoint`, `view` (the declared view from the spec plus
`label`, `icon` and, for a kanban on status, the workflow's `transitions`), `switcher` and
`placement` (`"toolbar"` or `"header"`: where `switcher` goes, see above).

- **Header.** A `zas-ph` row like the table's: the page `title`, the record count, then
  `props.switcher` when `placement` is `"header"`, then the Add button when the role may add.
  With `"toolbar"`, the switcher goes in your `zas-tb` row (search, filters, spacer, switcher, Export). Read `src/zas/ZasTable.tsx` and
  reuse how it decides and opens Add (the same `FormDialog`), search and filters where they make
  sense for the view. Do not rebuild the table.
- **Data.** The same endpoint as the table, so access and row scoping are the server's and
  identical: `api.useTableRows(endpoint, { length: 500 })` (rows keyed by the entity's column
  keys, `object_uuid` for the record; `status` holds the status). Labels and tones come from
  `SPEC.entities[entity].statuses` / `.choices`. Call `refetch()` after any change.
- **Opening a record.** As the table does (`SPEC.entities[entity].row_click`): navigate to
  `detailUrl(entity, uuid)` when the entity has a 360 page, otherwise open `RecordDrawer`.
- **Design.** Only `zas` components and classes (`Panel`, `Badge`, `Chip`, `Button`,
  `EmptyState`, `Skeleton`, …): no colour literals, no inline colour or font styles, no
  stylesheet. The design lint covers `src/custom/views/` too. Loading, empty and error states
  are required.

### `kanban`

One column per value of `view.group_by`, in `view.columns` order when given (otherwise every
status / choice in spec order), each with its label, tone dot and count. Cards show
`view.card.title`, `subtitle`, `fields` (label + value) and `badge` (a tinted `Badge`).

`view.move`:
- `transitions` (grouped by status): a card may be dragged only to a column some transition in
  `view.transitions` leads to from the card's current status. On drop, load the record's live
  actions (`api.get(endpoint, { action: "zas_record", object_uuid })` → `actions.transitions`,
  as `RecordDrawer` does) and find that transition by `engine_name`. Not `allowed` → toast its
  `blocked_reason` and leave the card. `has_form` → open its form the way `RecordDrawer` does.
  Otherwise `api.runTransition(endpoint, uuid, engine_name)`, then `refetch()`. Columns that are
  not a legal target must look and behave as not droppable while dragging. Keep a keyboard and
  touch path: a "Move to…" menu on the card listing the same legal targets.
- `update` (grouped by a choice field): on drop, save the field through the entity's edit form
  endpoint as the table's edit does.
- `none`: read-only, no drag.

### `cards`, `calendar`, `timeline`

- `cards`: a responsive grid of `view.card` (`title`, `subtitle`, `fields`, `badge`, `image`).
- `calendar`: a month grid on `view.date_field` (spanning to `end_field` when given), entry text
  `view.title`, tinted by `view.color_by`; previous / next / today; records without a date listed
  beside it.
- `timeline`: records along `view.date_field`, newest first, in `view.group_by` lanes when given.

## What the platform checks afterwards (`views`)

For every row of `.zas/views.md`: the file exists and is a real component (it loads the entity's
data and has no placeholder text), `pages/index.ts` exports the page with `makeViewsPage` and
passes that view. Anything missing comes back to you in a fix round. Record each custom view in
your summary.
