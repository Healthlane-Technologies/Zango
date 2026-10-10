# Entity-360 pages: the pitfalls, and how the runtime handles them

Read this when a 360 page misbehaves, or before you touch `zas_core/detail.py`, `zas/Detail360.tsx`,
`zas/ListPage.tsx` or write a slot. Every lookup uses **`object_uuid`** (`DynamicModelBase` has no `uuid` field).

A 360 page is generated from `detail_views[]` in the spec. You do not write one by
hand. You write (a) the hero's `<Model>Detail(ZasDetail, BaseDetail)` with
`Meta.fields`, (b) hooks for `stats[].value.text` and custom panels/tabs, and
(c) slots for custom panels/tabs. Everything below is what those must not break.

## 1. Pitfall → where it is handled → what you must not break

| # | Pitfall | Handled by | You must not |
|---|---|---|---|
| 1 | **Full page, never a drawer.** The hero's 360 is a route, `<list route>/detail-view/<uuid>` | `zas/ListPage.tsx` renders `getDetailComponent(view)` for that path (AppBuilder matches `<route>/*`) when the entity has a `detail_view` and this page is its `list_page`; otherwise `ZasTable` | open a hero's 360 in a drawer; export the list page as anything but `makeListPage(code)` |
| 2 | **One route owner per page.** Two mounted `CrudHandler`s with `enableDetailViewRoute` render the detail twice | only the hero's own list page owns it (`E.list_page === pageCode`); mini tables, tabs and dashboards navigate via `config.detailUrl()` / `viewUrl()` | add a second route-owning table of the same entity on a dashboard slot: use `api.useTableRows` + `detailUrl()` instead |
| 3 | **A filtered `api_endpoint` breaks the detail fetch**: the query string rides into `fetch_item_details` and `get_object()` 500s | `ZasTableMixin.get_table_data_queryset` applies the parent filter and `?qf=` **only** when `action` is `get_table_data` / `export_table`; `ZasDetail.get_object()` returns `zas.access = "not_found"` (HTTP 200) instead of raising | override `get_table_data_queryset` again without `super()`; filter in the detail path |
| 4 | **`customMainDetail` props are camelCase** (`data`, `objectUuid`, `onRefresh`), not snake_case | `Detail360.getDetailComponent(view)` reads `objectUuid` (falls back to route params) and `data`, then fetches its own payload with `api.fetchDetail` | read `general_details` etc. from props in a slot; slots get `SlotProps` (`record`, `zas`, `data`, `refresh`, `api`) |
| 5 | **Status label is `current_status_meta.status_label`**; `.label` is undefined, `.display_name` is the transition | `ZasDetail.zas_payload` sends `zas.record.status`, `status_label`, `status_tone` from the spec | read status from `workflow_details` in a slot: use `props.record.status_label` |
| 6 | **`BaseDetail` without `Meta.fields` returns the TABLE's columns**: amounts render 0 | rule in `map/detail-views.md`; example `references/examples/vendors/detail.py` | ship a `<Model>Detail` without `Meta.fields` listing every field the header, facts and panels read |
| 7 | **`get_sections(self, obj)` is never called**; the base calls it with `Meta.sections` and passes `pk` into an `object_uuid` lookup | `ZasDetail` builds panels itself (`_zas_tabs`, `_fields_panel`); `Meta.sections` is unused | declare `Meta.sections` or `get_sections` on a `ZasDetail` subclass |
| 8 | **Missing value must not read as 0** | `records.field_value()` returns `display: None` for empty; `ui.Value` and `StatTile` render "—"; stats use `None` when a hook returns nothing | coerce `undefined → 0` in a slot; return `0` from a stat hook when the answer is "unknown" (return `None`) |
| 9 | **Child tab must not reuse another entity's route-owning page**: nested `detail-view/` never matches | `Detail360.RelatedTab` is a `ZasTable` on `<child endpoint>?<param>=<uuid>`; a row opens the child's own top-level 360 (`viewUrl`) when it has one, else `RecordDrawer` | use `makeListPage(...)` output inside a tab |
| 10 | **The backend half is not optional**: the query string is only a display filter | `ZasTableMixin` + `access.parent_filter()` (see `child-tables.md`) | hand-filter child rows in React |
| 11 | **Add from a tab must not ask for the parent** | `RelatedTab.onAdd` opens `FormDialog` kind `create` with `params: {[param]: uuid}`; `ZasFormMixin.__init__` presets + hides the FK on a **copied** `ModelField` | mutate `self.declared_fields[x].properties` in place in a hand-written form (leaks to every request) |
| 12 | **`useTable`/`useTableData` outside a `CrudHandler` crash** ("No QueryClient set") | `zas/api.ts` `useTableRows()` (plain `fetch`, `action=get_table_data&view=table`, reads `data` or `response.table_data`) | import `useTable`/`useTableData` in a slot or custom page |
| 13 | **`_getval` columns arrive as HTML strings**; a boolean is truthy either way | `useTableRows` strips tags (`stripHtml`); `renderers.statusRenderer` strips HTML from status values | compare raw row values from a non-`useTableRows` fetch |
| 14 | **Numbers freeze after a child write** | every write path calls `refresh()` (re-runs `fetch_item_details`): header actions, `ZasTable.onChanged` (Add, row actions, drawer transitions), confirm dialogs | keep derived numbers in slot state without re-reading on `props.refresh` / `props.zas` change |
| 15 | **No prop forwards success from a `CrudHandler` form** (`formProps` replaces its handler), and crud 2.0.0 does not render `headerProps.customLeftActions/customRightActions` | lists and tabs are `ZasTable`, whose Add button opens `FormDialog` (crud `FormRenderer`) → `onDone` → refetch + `refresh()` | put an Add button in a CrudHandler header slot |
| 16 | **Change Logs lost** when the drawer is replaced | `timeline` tabs/sections → `ZasDetail.zas_timeline()` (audit `LogEntry` + workflow transactions, `changes` as `{label: [old, new]}`) rendered by `ui.Timeline` (iterates entries) | render `changes` as a React child; add a centred modal for history |
| 17 | **Row actions lost** with the drawer; wrong contract (`form_type=edit_form`) | header kebab in `Detail360.Header` lists `zas.actions.row_actions`; forms go through `dialogs.FormDialog` kind `row` (`action_type=row`, `action_key`, `form_type=row_action_form`), simple ones `api.runRowAction` | call the plain edit-form contract for an entity whose edit is a row action |
| 18 | **Stability rule**: components passed to crud (`FormRenderer`, any remaining `CrudHandler`) must be module-scope, or the subtree remounts in a loop | `getDetailComponent()` / `makeListPage()` cache one component per code; `ZasTable` keys its tab instance by endpoint | define components inline in props; write parent state from a child table callback |
| 19 | **Four states on every data surface** | `Page`: skeleton, `not_found` / `no_access` (`StateBox` with the spec's `states` copy), error; tabs: `EmptyState` with `empty_state` copy | ship a slot without loading/empty/error handling |

## 2. What the payload carries (so slots never refetch it)

`GET <hero endpoint>?view=detail&action=fetch_item_details&object_uuid=<uuid>` returns
the package payload plus `zas` (contracts §8): `record`, `header` (title, subtitle,
avatar, badges, facts, banners), `stats`, `tabs` (visible ones, with counts), `panels`
(per tab code and `sidebar`), `mini_tables`, `actions` (transitions with
`allowed`/`blocked_reason`, tags, buttons, row_actions), `custom`, `formats`.
Roles and `show_when` are already applied server-side.

Data that is not a field (an aggregate, a checklist) goes in a hook whose result
lands in `data.zas.custom.<key>` (contracts §6 `<view>__custom__<key>`), in the same
request: no extra endpoint, and no need to override `get_general_details()`.

## 3. Known gaps

- **Record info**: `general_details` carries `created_by/at`, `modified_by/at`,
  but `Detail360` does not render a "Record info" panel unless the spec's `fields`
  sections list `created_at`, `created_by`, `modified_at`, `modified_by`. Add them to
  a sidebar `fields` section in the spec when the page needs them.
- **Change Logs button**: there is no separate history action; a view gets history
  only through a `type: timeline` tab or section. Specs for heroes should have one.
- **Row-action forms** open in the runtime `Modal` (`dialogs.FormDialog`), not a
  `@zango-core/components` `Drawer`.

## 4. Verify (Phase 7, per 360 × role)

1. Open one record; compare the facts and stat tiles with the database values.
2. Open every tab: rows or the spec's `empty_state` copy, never blank.
3. Add a child from a tab: the parent FK is not shown, the tab badge and stats change without reload.
4. Click a child row: the URL is the child's own `<list route>/detail-view/<uuid>`.
5. Edit the URL to another record the role may not see: "not found" state, no 500.
6. Run a blocked transition: the button is disabled with `blocked_reason` as its title.
