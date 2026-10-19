# Design system: the Studio preview, as code

The app looks like the Zango App Studio's preview mode (`zango-app-studio.html`, "the generated
app" styles). Pages are not designed per app. The design is fixed in the runtime, and the spec
picks layout, order, tones and copy. This is enforced **by machine**, and no person approves a
screen ([testing](testing.md) §design).

## Where it lives (copied into the app, never edited there)

| File | What |
|---|---|
| `frontend/src/zas/tokens.css` | every colour, radius, shadow and type token, the nine tones, the `zas-*` component classes, and `--color-brand-*` / `--color-gray-*` so `@zango-core/crud` tables, drawers and forms follow the brand |
| `frontend/src/zas/ui.tsx` | `Button` (default · primary · danger · danger-primary · ghost; md/sm), `Badge`, `Chip`, `Panel`, `FieldGrid`, `Value`, `StatTile`, `Tabs`, `Timeline`, `Banner`, `EmptyState`, `StateBox`, `Skeleton`, `Menu`, `Modal`, `Drawer`, `CopyButton`, `Icon`, toasts; the sketch kit for custom screens: `Stack`, `Grid`, `Kpis`, `Bars`, `List`, `MiniTable`, `Board`, `Progress`, `KitEmpty`, `KitBadge` (the preview's `ctx.ui`, same arguments; [custom-code](custom-code.md) §Porting a sketch) |
| `frontend/src/zas/ZasTable.tsx` | `ZasTable` (list pages and 360 related tabs: page header, search, inline select filters for `filterable` columns, quick-filter chips, Export, server-side sort/paging, `group_by`, `footer_totals`, `highlight`, row kebab) and `RecordDrawer` (the row drawer for any entity) |
| `frontend/src/zas/icons.gen.ts` | only the lucide icons the spec uses (`scripts/lucide_icons.py`) |
| `frontend/src/zas/Gallery.tsx` | `/app/__zas`: every component in every state with fixture data (design tests) |

`config.ts applyTheme()` sets `--brand` from `app.theme.primary`. Brand tints (`--b50`, `--b100`,
`--b600`, `--color-brand-*`) derive from it with `color-mix`, so one colour themes everything.
It also sets `data-zas-radius` and `data-zas-density` on `<html>` from `app.ui`; `tokens.css`
redefines the radius (`--z-r-card`, `--z-r-head`, `--z-r-ctl`) and density (`--z-ctl-h`,
`--z-cell-y`, `--z-th-y`, `--z-page-pad`) tokens for them. Use these tokens, never a literal
radius or control height, in anything you add. The Gallery pins the defaults (rounded,
comfortable) so the goldens do not move.

## The grammar (from the preview)

- **Colour:** text `#101828`, sub `#475467`, muted `#667085`, border `#EAECF0`, ground `#F7F8FA`, card
  white. The brand is used for primary buttons, the active tab and nav item, links and focus rings,
  and nothing else.
- **Tones:** the spec's nine colour names (`gray blue green amber red purple teal indigo pink`), each a
  background/text/border triple (`.zt-<tone>`). Status, tag and choice badges, stat tiles and banners
  use the spec's colour for that item. Banner tones `info/warning/danger/success` map to
  blue/amber/red/green.
- **Type:** Inter for UI, JetBrains Mono for references and IDs (`.mono`), tabular numbers for every
  amount and count (`.num`). Page title 22/650, section 13.5/600, body 13.5, labels 12 muted.
- **Shape:** 8px controls, 12px cards, 14px for the 360 header, 999px for badges and chips. Hairline
  borders. Shadows only on popovers, modals and drawers.
- **Empty values** render as "—" (`Nil`), never `0`, `null` or blank.
- **States:** every data surface has loading (skeleton), empty (spec copy), error and no-access/not-found.

## Layouts (spec `detail_views[].layout`)

| Layout | Structure |
|---|---|
| `header_tabs` | header card (avatar, title, subtitle, badges, facts, actions) → banners → stat row → tabs |
| `header_tabs_sidebar` | as above, with a right rail (`sidebar[]` panels) beside the tab body |
| `header_sidebar_tabs_left` | header, then the rail on the left and the tabs on the right |

The sticky compact header on scroll is built in (`useStuck`). List pages are the crud table under the
page title with quick-filter chips on the left of the toolbar.

## Lists and drawers (match the preview, not crud's default UI)

| Preview | Runtime | Data |
|---|---|---|
| page header: title, "N records", primary **+ Add** | `ZasTable page=…` | `get_table_metadata` `has_add_perm`; the form is crud's `FormRenderer` in a modal |
| toolbar: search · `<Col>: All` selects · chips · Export | `ZasTable` | `search[value]`, `columns[i][search][value]` (i = metadata column index; links match the display value exactly), `?qf=`, `action=export_table` |
| link-column filter options | | `metadata.zas.filter_options` (display values among the role's own rows, never the linked entity's endpoint, which the role may not open) |
| sortable header (↕ / ↑ / ↓) | | `order[0][column]` / `order[0][dir]`, sorted by `ZasTableMixin.get_sorted_objects` (asc = ascending; a link sorts by its display attribute) |
| `link_to` cell → blue link | `Cell` | `row.zas.links[<col>]` (the linked record's uuid) |
| status / tags / choice-with-colour badges, `highlight` (`hl-red`/`hl-amber`) | `Cell` | `row.zas.status`, `row.zas.tags`, `row.zas.hl` |
| row drawer: title, "Entity · status", primary transitions first, ⋯ (row actions + tags), fields, Activity | `RecordDrawer` | `GET <endpoint>?action=zas_record&object_uuid=` (contracts §8b) |
| 360 related tab: same table inside the tab, + Add on the right, empty-state CTA | `ZasTable` (no `page`) | endpoint `?<hero>_uuid=` |

Two traps found in a live build, both fixed in the runtime; keep them fixed:

- **The `.zas` button reset must not reach crud's buttons.** `tokens.css` is unlayered, so a bare
  `:where(.zas) :where(button)` reset beats crud's layered Tailwind utilities (no padding, no brand
  background, `currentColor` borders = "black box"). The reset targets classless and `zas-*` buttons only.
- **crud 2.0.0 ships Tailwind class names, not CSS.** `src/index.css` (from `assets/templates/frontend/`)
  must `@source` the crud dist and declare the `brand`/`base`/`primary`/`error` colour names; tokens.css
  supplies the real values (including `--zango-border-color-default`).

## Rules for code you write (slots, custom pages)

`scripts/zas_test/design.py lint` enforces these, and a failure blocks the build:

1. Import UI only from `../../zas` (or `../zas`). No other component library, and no
   `@zango-core/components` in slots.
2. No hex/rgb/hsl colour literals in `.tsx` under `src/custom/`. Use tones (`tone="green"`) or classes.
   Exception: the slot of a screen approved in the preview (its hole says "Approved look") may use
   the colours its `sketch.js` uses, and inline styles (rule 3) to reproduce it
   ([custom-code](custom-code.md) §Porting a sketch).
3. No `style={{ color | background | border* | font* | boxShadow }}`. Layout-only inline styles
   (`display`, `gap`, `gridTemplateColumns`, `width`, margins and paddings) are allowed.
4. No new `.css` files under `src/custom/`, and no `<style>` tags.
5. Icons through `<Icon name="…"/>`, `icon="…"` or `icon: "…"` (lucide names), so `lucide_icons.py`
   picks them up. Run it again after adding one; in server mode the platform runs it after you
   finish and, if it added icons, sends you back to rebuild. A name lucide does not have renders as
   an empty circle and fails design lint.
6. Copy comes from the spec or the hole text. Never ship "Lorem", "TODO", "Coming soon" or "N/A".

If a slot needs something the components cannot express, add it to the **skill's**
`assets/frontend/zas/` (and the Gallery and goldens), not to the app. Report it as a runtime change.

## What the design tests compare against

| Check | Reference |
|---|---|
| lint | the rules above |
| component gallery screenshots | `assets/goldens/*.png` (pinned Chromium, default brand) |
| token conformance | computed styles vs `tokens.css` + the app's `theme.primary` |
| design tree per page and role | the spec (via `data-zas` attributes, contracts §11) |
| preview parity | each custom screen against the approval bundle (`.zas/bundle/`): the sketch kit's `data-zas-kit` blocks, titles, KPI labels and table columns per approved role. Declarative pages are drawn from the same spec and are not compared. Reported, not blocking ([custom-code](custom-code.md) §Porting a sketch) |
| layout sanity (1440 and 1280 px) | fixed rules: no horizontal overflow, clipped text, overlaps or blank tabs |
