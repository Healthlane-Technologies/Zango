# Custom code: turning plain-language spec items into hooks and slots

Everything in the spec written as prose (`text:`, `on_done:`, `shows:`, `condition: {text}`,
`custom_requirements`, custom pages, tabs and panels) becomes a **hole**: one function with
a fixed name and signature, listed in `.zas/holes.md` (contracts §6, §10). Generated code
calls the hole and never contains the logic. This is Phase 4. Do it after the generated
backend imports cleanly, and before testing.

## Where each kind goes

| Kind | File | Signature |
|---|---|---|
| `condition`, `tag_condition` | `backend/<module>/hooks.py` | `(request, obj) -> bool` |
| `on_done` | hooks.py | `(request, obj, form_data) -> None` |
| `on_create` | hooks.py | `(request, obj) -> None` |
| `validation` | hooks.py | `(form, cleaned) -> bool` (True = passes) |
| `rows` | hooks.py | `(request, qs) -> qs` |
| `computed` | hooks.py | `(obj) -> value` (called on every save) |
| `column` | hooks.py | `(obj) -> value` (called per row: keep it to one query) |
| `row_action` | hooks.py | `(request, obj, form_data) -> dict` (`{"message"}`, `{"url"}` for downloads) |
| `stat` | hooks.py of the hero | `(request, obj) -> number \| None` |
| `custom_panel`, `custom_tab` | hooks.py of the hero **and** `frontend/src/custom/slots/<Export>.tsx` | hook `(request, obj) -> dict` → slot `data` |
| `custom_page` | `frontend/src/custom/slots/<Component>.tsx` (+ a backend view if it needs data) | React component |
| `system_transition`, `system_tag`, `requirement` (`area: scheduled`) | `backend/<module>/tasks.py` | `@shared_task () -> int`, with a `# zas:schedule <cron>` line above it ([workflow](map/workflow.md)) |
| `requirement` (other areas) | where the text says: hooks.py, a new view, a slot | free. Record what you built in the hole row |

The `Target` column of holes.md gives the file and function. Copy the name and signature
exactly, because the runtime looks hooks up by name (`zs.hook(module, fn)`). A typo is
not an import error. It shows up as "not implemented yet" in the log and the UI.

## The rules

1. **Marker + docstring.** Put `# zas:hole H-NN` on the line above the `def`, and quote the
   spec text in the docstring. `spec_check` finds holes by spec path and keeps the IDs stable
   across re-runs. The marker lets anyone go from code to spec.
2. **Start from the templates.** Use `assets/templates/hooks.py.tmpl` for the module header and
   `assets/templates/frontend/slots/Slot.tsx.tmpl` for a slot. Export every slot from
   `slots/index.ts`, under the name in `spec.ui.json` `slots`.
3. **Re-runs append, never delete.** When the spec changes, add missing functions at the end.
   Leave written ones alone, even if their hole disappeared. Report them as orphans.
4. **Use the runtime, not new plumbing:**
   - expressions: `zx.to_q(zx.parse("status not_in [closed, cancelled]"), Model)`, `zx.current_status(obj)`, `zx.current_tags(obj)`
   - values: `zr.value_of(obj, "vendor_contact[is_primary].email")`, `zr.display(v, "money")`
   - logins: `app_user.provision(obj, "<entity>", request)`, `app_user.set_active(obj, "<entity>", bool)`
   - messages: `notify.notify("<entity>.<event>", to, subject=…, body=…)`. This is the **only**
     way to send mail or SMS. Without a provider it logs and records the message, so the hole is still `done`
   - system moves: `run_system_transition(...)`, `set_system_tag(...)`
5. **Same-name form fields are already saved.** `ZasActionFormMixin` writes transition and row-action
   form fields that match entity fields before the hook runs (`risk_rating` on approve). The hook
   only does the rest (dates, the current user, side effects).
6. **"Activity log" / "record who and when"** is already covered: the 360 timeline shows creates,
   field changes (audit log) and every transition and tag with actor, time and form data. Mark such
   holes `covered` (no code; the audit accepts it) and append "covered by the timeline" to the row's text. Do not build a second log. Only write code
   when the text asks for something the timeline lacks (a field such as `approved_by`).
7. **Hooks never raise for a business "no".** Conditions return False (the UI shows
   `condition_msg`). Validations return False (the spec `message` is shown). Row actions return
   `{"message": "…"}`. Raise only on programming errors.
8. **External systems** (GST portal, payment gateway, ERP): write a typed client function that
   raises `NotImplementedError("GST lookup: credentials and endpoint needed")`. Call it from the hook
   inside `try/except NotImplementedError`, so the record flow still works. Mark the hole `blocked`
   with what is missing. Never invent an endpoint or credentials. Secrets: `references/zango/core/secrets.md`. <!-- pragma: allowlist secret -->
9. **Imports.** Inside a module, use `from .models import …`. For another module, import inside the
   function (`from ..procurement.models import PurchaseOrder`) to avoid import cycles. hooks.py
   never imports `views`, `tables` or `forms`.
10. **Performance.** `column` hooks run per row and `computed` hooks run on every save: one aggregate
    query each, no loops over related rows. If a value is expensive, store it in a field and update it
    from the child's save/transition hook, then say so in the hole row.

## Slots (custom panels, tabs and pages)

- **Data comes from the hook.** The slot renders `props.data` (= `data.zas.custom.<key>`) and never
  fetches the record again. Lists of other entities: `api.useTableRows(endpoint, {params})`. Never
  `useTable`/`useTableData` outside a CrudHandler (entity-360 rule 12).
- **Four states:** `data === undefined` → `<Skeleton/>`. Empty → `<EmptyState/>` with real copy.
  `data.error` → `<Banner tone="danger">`. Then content.
- **Design system only:** `Panel`, `FieldGrid`, `StatTile`, `Badge`, `Chip`, `Button`, `Tabs`,
  `Timeline`, `EmptyState`, the sketch kit (`Stack`, `Grid`, `Kpis`, `Bars`, `List`, `MiniTable`, `Board`,
  `Progress`, `KitEmpty`, `KitBadge`; see "Porting a sketch") and the `zas-*` classes from `tokens.css`. No hex colours, no inline colour
  styles, no new CSS files. `design.py lint` fails the build on them ([design-system](design-system.md)).
  **Exception: a screen the user approved in the preview** (its hole says "Approved look") is built
  to look like its screenshot. Its slot may use inline styles and any colour its `sketch.js` uses.
- **Writes** go through `api.runTransition / runTag / runRowAction` or `FormDialog`, then
  `props.refresh()` so header and stats update.
- **Custom pages** (`type: custom`) are full slots rendered by `makeCustomPage`. A page that needs
  backend data gets a hook-backed view: add `def <page code>__data(request) -> dict` in the
  closest module's hooks.py, expose it with a small `View` returning `get_api_response(True, data, 200)`,
  give it a URL and a policy for the page's roles, and call it with `api.get`. Record that in the hole row.
- Mark each slot with `// zas:hole H-NN · <spec path>` at the top (the template does this).

## Porting a sketch (custom screens the user approved)

A custom page, tab or panel whose hole says **"Approved look: `.zas/bundle/screens/<screen>/`"** was
drawn in the App Studio preview, and the user approved that screen. **The built screen has to look
like the approved screenshot**: same blocks, same visual treatment (banners, gradients, charts,
avatars, coloured accents, icons), same density. Build that screen, not your own idea of the text,
and never simplify it to what the kit happens to have.

Read `.zas/bundle/index.md` first. It lists every custom screen with its kit outline. Then, **before
writing each slot, Read its `shot.<role>.png` and its `sketch.js`.** The outline only lists the kit
blocks; hand-drawn parts (a gradient banner, a donut, avatars) are only in the sketch and the
screenshot. Each screen's folder has:

| File | Use |
|---|---|
| `sketch.js` | The preview code. Port it call for call, markup included (below). Never run or import it. |
| `contract.json` | `data`, `interactions`, `states`, `acceptance`: the real behaviour and your tests |
| `view.<role>.json` | The kit tree that role saw (blocks, titles, KPI labels, table columns) |
| `shot.<role>.png` | The screen as that role saw it. Values are demo data |
| `in_page.<role>.png` | A tab or panel in its 360 page |

**Map each `ctx.ui` call to the kit component with the same arguments** (all in `zas/ui.tsx`):

| Sketch | Slot |
|---|---|
| `ui.stack(a, b)`, `ui.grid(a, b)` | `<Stack>{a}{b}</Stack>`, `<Grid>{a}{b}</Grid>` |
| `ui.kpis([{label, value, icon, tone, hint, go}])` | `<Kpis items={[…]} />` (`format: "money" \| "percent"` for numbers) |
| `ui.bars(title, items, {tone, empty, icon, note})` | `<Bars title={…} items={…} … />` |
| `ui.list(title, rows, {primary, secondary, meta, badge, go, limit, empty})` | `<List title rows primary … />`. Cells take a field key or a function |
| `ui.table(title, rows, columns, {go, limit, empty})` | `<MiniTable title rows columns … />` |
| `ui.board(title, columns)` | `<Board title columns />` |
| `ui.progress(done, total, label)` | `<Progress done total label />` |
| `ui.panel(title, body, {icon, note})` | `<Panel kit="panel" title icon note>{body}</Panel>` |
| `ui.empty(text)`, `ui.badge(text, tone)` | `<KitEmpty text />`, `<KitBadge text tone />` |
| `go: 'po_360:' + id`, `go: 'vendors'` | the same string: `go` opens that page (a detail page opens the record) |

**Keep exactly:**
- the blocks and their order;
- titles, KPI labels, table column labels;
- icons, tones, limits and `go` targets.

The parity check (`zas_test parity`) compares them with `view.<role>.json`.

**Change only where the data comes from:**
- **Move the sketch's data logic to the server.** For a custom page that is the `<page>__data` view; for a panel or tab, its hook. The sketch reads demo rows (`ctx.rows`, `ctx.related`, `ctx.record`). Put its counting, grouping and sorting there, and return what the kit needs, e.g. `{"rejected": 10, "top_reasons": [{"label", "value"}]}`. Keep that math off the client: real tables are large.
- `ctx.fmt(row, field)`: the hook returns display strings, or the slot uses the runtime's formatters.
- `ctx.today`: the server date. `ctx.role`: the requesting user's role (the hook knows it).
- **Add what a sketch never shows:** the four states (Skeleton, Empty, `data.error`, content). Then `contract.json` `states`, `interactions` and `acceptance` become tests.

**Hand-drawn markup.** Many sketches mix `ui.*` calls with HTML strings (index.md says "hand-drawn
parts"), and some are all markup (`view.*.json` says `"hand_written": true`). Port that markup to JSX
faithfully, keeping its structure and its inline styles (`style="background:linear-gradient(…)"` becomes
`style={{ background: "linear-gradient(…)" }}`). Rules for it:
- Use the sketch's colours; where the sketch uses the brand colour (`#4f46e5` in the default preview
  brand), write `var(--brand)` so the app's brand applies. Design lint rejects any colour the
  sketch does not use.
- A part the kit already draws the same way stays a kit component (`ui.kpis` → `<Kpis>`).
- Icons go through `<Icon name="…"/>`; values come from the hook, never the sketch's demo rows.
- Check the result against the screenshot: the platform shows you both after the build, and again
  after each change, until they match.

**Roles.** When `index.md` lists several variants of one screen, each role sees a different structure. Build every variant; the kit outline tells you which blocks belong to which role.

## The app shell (sidebar header, user card, top bar)

Open mode (`.zas/bundle/prototype/`) builds the shell differently: `src/custom/Shell.tsx` on `makeShell`,
see `references/open-mode.md` §The shell. This section is for the kit preview's `/shell` screen.

The shell comes from `@zango-core/appbuilder`'s `ZangoApp`; the preview draws its own. When
`.zas/bundle/index.md` has a `/shell` screen, **Read its screenshot first**, then make the shell
look like it through `ZangoApp`'s props in `src/App.tsx` (`references/zango/frontend/appbuilder.md`,
"Navbar & Topbar"). Never edit the appbuilder package or replace the whole navbar or topbar
(`customNavbar`, `customTopbar`): the menu, routing and profile stay the platform's.

| What the screenshot shows | Prop | Component in `src/custom/shell/`, root marked |
|---|---|---|
| Sidebar header: initials avatar, app name, the role | `navbarConfig.customLogo` | `data-zas="shell-brand"` |
| User card at the sidebar's bottom: avatar, name, role | `navbarConfig.customBottomContent`, and `topbarConfig.showProfile: false` | `data-zas="shell-user"` |
| Top bar: page title (breadcrumb on a 360), icon buttons | `topbarConfig.customLeftContent` / `customRightContent` | `data-zas="shell-top"` |

- Compose them from the zas kit and classes (`Avatar`-like initials with `zas` classes, `Icon`,
  `Button`): `src/custom/shell/` is under the design lint like the rest of `src/custom/`.
- Data: the user and role from `useAppContext()` (appbuilder), the app name from `SPEC.app.name`,
  the page title from `SPEC.pages` by the current route (`useLocation()`).
- Icon buttons with nothing behind them in the spec (the preview's search and bell) are decoration:
  draw them only if the screenshot has them, and give them no fake behaviour.
- The parity check opens the landing page and looks for each marker the screenshot calls for.

## Notes on an item (`zas:note`)

Put what a reader needs to know about an implementation (the guess behind a `needs-review`, where a
rule is actually wired, why something is `covered`) on `# zas:note …` lines (`// zas:note …` in TS)
directly under the `# zas:hole H-NN` marker:

```python
# zas:hole H-10
# zas:note needs-review: "no enrollment for 60 days" read as: newest entry created >60 days ago.
@shared_task
def site__tag_at_risk__sync(): ...
```

A note never drops something the approved screen or the spec asks for. "Out of scope", "left out",
"not built", "instead of …" or "falls back to the plain form" on a note fails the build's parity check
unless the item is in that screen's `not_built` (which the user saw and agreed to). If the spec can't
express it, build it in the slot.

The build report shows them on the item. Never put notes in `holes.md`: `spec_check` regenerates that file
and keeps only each row's status.

## Done means

- The function exists with the exact name and signature, and has the marker.
- holes.md row status: `done`, `needs-review` (logic guessed from vague text, with the guess stated in
  the row), `blocked` (external dependency, with what is missing), or `covered` (the runtime already does it).
- The test harness covers it: API tests call every condition/on_done path and row action, and the
  UI tests open every slot ([testing](testing.md)).
- `python <skill>/scripts/spec_check.py <spec> --workspace <ws> --audit-holes` exits 0: no `todo`, every
  `done`/`needs-review` function exists with its marker.
