# Entity-360 Detail Views

How to build the detail page for a **focus object** — the entity an app is really
about, and the one other records point at. Patient, Order, Case, Employee,
Customer, Program.

A focus object's detail page is **not** a field dump in a side drawer. It is a
full-page route showing identity, key facts, and the entity's **related records
as tables inside tabs** — orders, programs, documents, notes — all scoped to that
one record.

> Read this together with [crud/core.md](crud/core.md) and
> [crud/detail.md](crud/detail.md) (CrudHandler props, detail-view
> payload shapes) and [design-system.md](design-system.md) (tokens, states).

---

## 1. Which entities get one

Read the FK graph. An entity qualifies when **both** are true:

1. **Other models point at it** — one or more models declare a `ZForeignKey` to it.
2. **A user works on it directly** — it appears in a role's daily flow, it is
   something you open and act on, not something you pick from a dropdown.

| Entity | Inbound FKs | Worked on directly | Verdict |
|---|---|---|---|
| `Patient` (Orders, Programs, Documents → Patient) | yes | yes | **Entity-360** |
| `Order` (OrderLines, Shipments → Order) | yes | yes | **Entity-360** |
| `Employee`, no child models yet | no | yes | Custom detail, no tabs |
| `DocumentType`, `Category`, `City`, `Status` | yes | no — only referenced | Default CRUD |

**There is no fixed limit.** Decide from the app's own shape how many entities
qualify, and **justify the selection in your summary**: which entities got an
entity-360 page, and why each remaining model did not. The two tests above are a
*filter*, not an invitation — a lookup table never passes them, however many
FKs point at it.

**"Custom detail, no tabs" is not a lesser bar.** An entity that fails test 1
(nothing points at it) but passes test 2 (a user works on it directly) still
gets identity block, synthesis lead card, rail and one anchor — everything in
this file except the tab strip and child tables, because it has none. See
[design-system.md](design-system.md) §6, "Custom detail page, no child tables."
The failure mode for this tier is a plain field dump, on the theory that "no
tabs" means "no design effort" — it does not.

## 2. Full page, never a drawer

An entity-360 is a **routed page of its own** (`/app/patients/<uuid>`).

The default side drawer cannot hold tabs, child tables and a timeline — it is
the wrong container. Rows **navigate**; they do not open a drawer.

```jsx
import { CrudHandler, TableBody } from '@zango-core/crud/table';
import PatientDetail from './PatientDetail';

// Module scope. See the stability rule in §5 — this must NOT be inline.
const NavigateTableBody = () => <TableBody defaultDetailView="navigate" />;

<CrudHandler
  api_endpoint="/patients/"
  enableDetailViewRoute={true}      // registers /detail-view/:object_uuid
  customMainDetail={PatientDetail}  // your page, rendered at that route
  customTableBody={NavigateTableBody} // makes rows navigate on click
/>
```

All three props are required **together**. Omit `enableDetailViewRoute` and the
route never exists; omit `customTableBody` and rows still open the drawer.

### Every table of that entity gets the same three props — not just its list page

Once an entity has a custom detail page, **every `CrudHandler` anywhere in the
app that lists that entity must pass the same three props.** The wiring travels
with the entity, not with the page it happens to be on.

This is easy to miss because the list page is the one you build while writing
the detail page, so it always gets wired. The other tables — the dashboard
worklist, the role landing page, a child tab on a *different* entity's detail
page, a "recent items" panel — get added at another time and silently fall back
to the framework's default drawer.

The result is the same record opening two different ways depending on where the
user clicked it. Nothing errors, both routes return 200, and the default drawer
looks plausible on its own — so this survives every check that only ever opens
the list page.

```jsx
// WRONG — same entity, same app, two different detail experiences.
// Home:
<CrudHandler api_endpoint="/bookings/bookings/?created_today=1" showHeader={false} />
// Bookings list:
<CrudHandler api_endpoint="/bookings/bookings/" enableDetailViewRoute={true}
             customMainDetail={BookingDetail} customTableBody={NavigateTableBody} />
```

Give the entity **one wrapper** and use it everywhere, so the wiring cannot
drift apart:

```jsx
// bookings/BookingsTable.tsx — the only place these props are written.
export const BookingsTable = (props) => (
  <CrudHandler
    enableDetailViewRoute={true}
    customMainDetail={BookingDetail}
    customTableBody={NavigateTableBody}
    api_endpoint="/bookings/bookings/"
    {...props}                      // callers override endpoint/filters/header
  />
);
```

Then the dashboard is `<BookingsTable api_endpoint="/bookings/bookings/?created_today=1"
showHeader={false} />` and cannot lose the detail view.

To check, grep for every table of the entity and confirm the count matches the
number wired:

```bash
grep -rn "bookings/bookings/" src/custom/ | wc -l   # tables of this entity
grep -rn "customMainDetail" src/custom/ | wc -l     # tables wired to the page
```

## 3. Props your detail component receives — camelCase

> **This is the single most common way an entity-360 page ships blank.**

`customMainDetail` receives **camelCase** props, while the raw API payload uses
snake_case. Some older examples in `crud/detail.md` show the snake_case spelling — those
are for `customDrawerDetail`, and copying them into `customMainDetail` renders an
empty page with no error.

```jsx
const PatientDetail = ({
  data,             // full detail response; data.title is the record title
  generalDetails,   // NOT general_details — { fields: { <field_name>: {...} } }
  workflowDetails,  // NOT workflow_details — current_status_meta, next_transitions, tag_details
  sections,         // array of { key, name, title, data, extra_html, form }
  rowActions,
  objectUuid,       // the record's UUID — what you scope child tables by
  pk,
  onRefresh,        // re-fetch after a mutation
  apiUrl,
}) => { ... };
```

Each entry in `generalDetails.fields` is
`{ name, display_name, type, value, searchable, sortable }`.

## 3b. `generalDetails.fields` carries the TABLE's columns — not your model's

**The trap that renders a confident, wrong number.** `fields` is keyed by field
name, so `fields.amount_billed?.value` *looks* right. But which keys exist is
decided server-side, and the default is not what you expect:

```python
# packages/crud/detail/base.py — get_general_details()
if hasattr(self, "Meta") and hasattr(self.Meta, "fields"):
    table_metadata = self.get_table_metadata()      # your detail's fields
else:
    table_metadata = self.table_obj.get_table_metadata()   # the TABLE's columns
```

**A `BaseDetail` subclass with no `Meta.fields` falls back to the table's
columns.** A table normally lists what belongs in a *grid* — a few identifying
columns plus computed display columns — not the model's monetary or date
fields. So the keys your page wants are simply absent.

This shipped on a real run. `ClaimTable` declared `id, patient, tpa_name,
policy_number, status, outstanding_amount, documents_count, transitions`, and
`ClaimDetail` declared no `Meta`. The page read:

```ts
const billed = toNum(fields.amount_billed?.value);     // undefined
const approved = toNum(fields.amount_approved?.value); // undefined
```

The record held ₹1000.00 billed and ₹100.00 approved. The page rendered
**₹0.00 for both, and ₹0.00 outstanding** — the one number the design plan
called "the single number billing staff open the page to check". No error, no
warning, HTTP 200. The "Amounts" section rendered empty and the meters showed
as flat grey lines, which read as a styling problem and hid the data bug.

### Two rules

**1. Every `BaseDetail` subclass declares `Meta.fields`.** List every field the
page reads, including ones absent from the table:

```python
class ClaimDetail(BaseDetail):
    class Meta:
        fields = ["id", "patient", "tpa_name", "policy_number", "doctor",
                  "admission_date", "discharge_date",
                  "amount_billed", "amount_approved"]
```

**2. `get_sections(self, obj)` is not a hook — defining it does nothing.** The
framework calls `self.get_sections(self.Meta.sections)`, passing a
`SectionSchema` list, and only `if hasattr(self.Meta, "sections")`. A
zero-`Meta` class that defines `get_sections(self, obj)` has an incompatible
signature and is **never called**; the sections silently do not exist. Declare
`Meta.sections` or lay sections out in the React page, not both.

### Never let a missing field read as zero

A `toNum` helper that maps `undefined → 0` converts "the server never sent
this" into "the value is zero" — indistinguishable on screen, and the reason
this survived to production:

```ts
// WRONG: undefined and a real 0 are now the same thing
const toNum = (v: any) => {
  const n = Number(String(v ?? '').replace(/[^0-9.\-]/g, ''));
  return Number.isNaN(n) ? 0 : n;
};

// RIGHT: absent stays absent, and renders as "—"
const toNum = (v: any): number | null => {
  if (v === null || v === undefined || v === '') return null;
  const n = Number(String(v).replace(/[^0-9.\-]/g, ''));
  return Number.isNaN(n) ? null : n;
};
```

Then a missing field shows `—`, which is visibly wrong and gets fixed, rather
than `₹0.00`, which looks deliberate.

### Verify it — one record, against the source

Before calling a detail page done, take **one real record** and compare what it
renders against the stored values:

```sql
select amount_billed, amount_approved, admission_date
from <schema>."dynamic_models_claim" limit 1;
```

Then confirm those exact values appear on the page. Checking the page against
itself cannot catch this class of bug: when every derived number is 0, the page
is internally consistent and uniformly wrong.

## 4. Child tables — the mechanic

**There is no `childTables` prop. Stop looking for one.**

A child table is simply **another `CrudHandler`**, pointed at the *child module's
own* CRUD endpoint, with a parent filter appended to the query string. The parent
module holds no reference to the child beyond that endpoint string — no shared
row state, no takeover.

```jsx
<CrudHandler
  api_endpoint={`/orders/?patient_uuid=${objectUuid}`}
  headerProps={{ title: 'Orders' }}
/>
```

That should give the tab a full table: search, filters, row actions,
pagination and the add button, governed by the child module's own policies.

> **Verify the child tab actually renders — do not assume it.** This is the
> single most common way an entity-360 page ships broken. In an observed run
> both child API calls returned `200` with correctly filtered data and the tab
> still painted **nothing at all** — no table, no header, no empty state — so
> the network tab looks healthy while the page is blank.
>
> After wiring a child tab, open it and confirm rows (or a designed empty
> state) are visible. If it is blank:
>
> - compare your props against a working `page_type: "crud"` list page for the
>   same module — the list page is the reference implementation, and whatever
>   it passes that you do not is the likely cause;
> - check `crud/core.md` for the `CrudHandler` props that list page relies on;
> - confirm the endpoint you passed is the child module's own CRUD endpoint,
>   spelled exactly as in `settings.json` `app_routes`.
>
> A tab that renders blank is not "an empty state" — it is a broken tab. Ship
> an `EmptyState` for genuinely-empty data, and fix the blank.

### The backend half is not optional

The query string is a **display** filter. The child's `BaseCrudView` must narrow
its own queryset from that parameter, server-side:

The override lives on the **table class**, not the view, and is called
`get_table_data_queryset()`. Read the request through
`self.crud_view_instance.request`:

```python
# backend/orders/tables.py
class OrderTable(ModelTable):
    class Meta:
        model = Order
        ...

    def get_table_data_queryset(self):
        """Scope this table to one patient when the detail page asks for it."""
        queryset = super().get_table_data_queryset()
        patient_uuid = self.crud_view_instance.request.GET.get("patient_uuid")
        if patient_uuid:
            # the value can arrive with a trailing slash from the router
            patient_uuid = patient_uuid.replace("/", "")
            queryset = queryset.filter(patient__uuid=patient_uuid)
        return queryset
```

> There is **no** `get_queryset()` on `BaseCrudView` — overriding that name does
> nothing at all and leaves the child table unfiltered. See
> [../packages/crud/tables/advanced.md](../packages/crud/tables/advanced.md) → *Custom Table Queryset*.

Without this, any user can edit the URL and read another parent's children.
In a healthcare or finance app that is a data breach, not a UI bug. **Never
rely on the frontend to scope a child table.**

## 4b. Reading child rows yourself — the three traps

`CrudHandler` renders a child table for you. But a **lead card that
synthesises** (design-system.md §6.2) usually needs the rows themselves — the
lowest quote, the unpaid total, how many are approved — not just a table. When
you fetch them yourself, all three of these will bite, and each fails
*silently* with a 200:

**1. The rows are behind `action=get_table_data`.** The bare endpoint returns
200 with table *metadata*, not records, so a naive fetch yields an empty list
and the card renders "0" next to a table visibly showing rows.

```ts
// WRONG -- 200, but no records
fetch(`/vendor-quotes/vendor-quotes/?tender_uuid=${objectUuid}`)

// RIGHT
fetch(
  `/vendor-quotes/vendor-quotes/?tender_uuid=${objectUuid}` +
    `&action=get_table_data&view=table&start=0&length=100`,
)
```

**2. The rows are at `j.data` — a plain array.** `ModelTable.get_table_data()`
returns `{draw, recordsTotal, recordsFiltered, data}` where `data` **is** the
row array (packages/crud/table/base.py). A chain like
`j?.data?.records ?? j?.records ?? []` silently falls through to `[]`.

```ts
const rows = Array.isArray(j?.data) ? j.data : [];
```

**3. Serialized columns are HTML strings, not values.** Any column with a
`<field>_getval` on the table class is rendered server-side. A boolean column
arrives as `'<span class="badge badge-success">Picked</span>'` — which is
**truthy either way**, so `rows.filter((r) => r.is_selected)` counts every row.
Decimals may arrive formatted too.

```ts
const stripTags = (v: any) => String(v ?? '').replace(/<[^>]*>/g, '').trim();
const toNum = (v: any) => Number(String(v ?? '').replace(/[^0-9.\-]/g, ''));
const isPicked = (r: any) =>
  r?.is_selected === true || /(^|>)\s*Picked\s*(<|$)/i.test(String(r?.is_selected ?? ''));
```

**Verify with the numbers, not the network tab.** All three return 200. The
only reliable check is that the count in your card matches the row count in
the table rendered beside it — if the card says 0 and the table shows rows,
you have hit one of these.

## 4c. Change Logs — the default drawer has this; your page must too

**The default drawer's kebab menu has a "Change Logs" action next to Edit.**
Switching an entity to a custom `customMainDetail` page removes that menu
entirely, and nothing else on the page replaces it — the page silently loses
a capability every other entity in the app still has, the same failure shape
as §2 (rows opening two different ways), but for one page instead of one
table.

The action calls the module's own CRUD endpoint with `action=fetch_audit_logs`
— the same audit-log data the drawer's "Change Logs" view reads, so building
this is not new backend work, just wiring it into your page:

```ts
const url = `${apiUrl.split('?')[0]}?object_uuid=${objectUuid}` +
  `&action=fetch_audit_logs&view=detail`;
const res = await fetch(url, { credentials: 'include' });
const { success, response } = await res.json();
// response: { audit_logs: [...], workflow_transactions: { statuses, tags } }
```

`audit_logs` entries are `{ id, actor, actor_type, action, object_id,
object_uuid, object_type, timestamp, changes }` — `action` is `"Create"`,
`"Update"` or `"Delete"`. Render newest first (the endpoint already sorts
`-id`); skip rendering `changes` for `Create` rows (there is nothing to diff
yet, and `Create` rows don't reliably omit `changes` either — check `action`,
not just presence of the field).

**`changes` is an object keyed by field name, each value a `[old, new]`
pair — never a string.** An earlier version of this doc called it "a
serialized diff string"; that was wrong and shipped a crash on a real run:

```json
"changes": {
  "id": ["N/A", "2"],
  "booking": ["N/A", "a5068f76-..."],
  "result_notes": ["N/A", "N/A"]
}
```

Rendering `{log.changes}` directly (as the string-shaped example above would
suggest) throws **React error #31 — "Objects are not valid as a React
child"** — the whole panel crashes to an error boundary, not just that one
row. Iterate the entries instead:

```jsx
{log.changes && log.action !== 'Create' && typeof log.changes === 'object' && (
  <ul>
    {Object.entries(log.changes).map(([field, diff]) => {
      const [oldVal, newVal] = Array.isArray(diff) ? diff : ['—', '—'];
      return <li key={field}>{field}: {String(oldVal)} → {String(newVal)}</li>;
    })}
  </ul>
)}
```

Verify against one real `Update` log entry (edit a field, then read
`fetch_audit_logs` back) — a `Create`-only test booking never exercises the
`changes` rendering path at all, so it looks fine right up until the first
edit.

### Change Logs trigger — a styled button, not a bare text link

The header action that opens the panel is a small but real UI element other
header actions (`WorkflowStatus`, Edit) already look like buttons — a plain
`<button>` with only text-color classes reads as a stray link, not a control
at the same level as the rest of the header:

```jsx
// WRONG — no border, no padding, reads as a link
<button onClick={openChangeLogs} className="text-[13px] text-gray-500">
  Change Logs
</button>

// RIGHT — matches the app's secondary Button treatment, plus an icon
<button
  onClick={openChangeLogs}
  className="inline-flex items-center gap-1.5 rounded-lg border border-[color:var(--color-gray-300)]
             bg-white px-3 py-1.5 text-[12.5px] font-medium text-[color:var(--color-gray-700)]
             shadow-[var(--shadow-xs)] hover:bg-[color:var(--surface-sunken)]"
>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
       strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4 text-[color:var(--color-gray-500)]">
    <path d="M3 12a9 9 0 1 0 2.64-6.36" /><path d="M3 4v5h5" /><path d="M12 7v5l3.5 2" />
  </svg>
  Change Logs
</button>
```

A history/clock glyph (arc + backtick tail) reads clearly as "past activity"
next to a workflow status chip. Give the panel's close control the same
treatment — a bordered icon button (`h-7 w-7`, an X glyph), not a bare `×`
character — so the panel matches the rest of the app's chrome instead of
looking like an unfinished placeholder.

**This page has no drawer — it is a full routed page (§2).** The drawer's own
"Change Logs" works by swapping the drawer's body in place; there is no
drawer here to swap. Do not add a new route for it and do not use a centered
modal — either fights with the tabs and content already on the page. The
equivalent is a **slide-over panel anchored to the right edge of the
viewport**, layered on top of the full page (`fixed inset-y-0 right-0`, a
width like `w-[420px]`, an overlay behind it), opened by a header action next
to `WorkflowStatus`/Edit and closed by its own back/X control — the same
gesture users already know from every entity that still uses the drawer:

```jsx
// module scope — see the stability rule in §5. Panel body renders `changes`
// as field entries (see above) — never `{log.changes}` directly, and the
// trigger/close controls use the styled-button treatment above, not bare
// text or a `&times;` character.
const ChangeLogPanel = ({ apiUrl, objectUuid, onClose }) => (
  <>
    <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />
    <div className="fixed inset-y-0 right-0 w-[420px] bg-white shadow-xl z-50 flex flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3.5">
        <h2 className="text-sm font-semibold">Change Logs</h2>
        <button onClick={onClose} aria-label="Close" className="grid h-7 w-7 place-items-center rounded-md text-gray-500 hover:bg-gray-100">
          <CloseIcon className="h-4 w-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {/* fetch + render the timeline, as above */}
      </div>
    </div>
  </>
);

const PatientDetail = ({ data, generalDetails, workflowDetails, objectUuid, apiUrl, onRefresh }) => {
  const [showChangeLogs, setShowChangeLogs] = useState(false);
  // ...header actions...
  <button onClick={() => setShowChangeLogs(true)} className={CHANGE_LOGS_BUTTON_CLASS}>
    <HistoryIcon className="h-4 w-4" /> Change Logs
  </button>
  {showChangeLogs && (
    <ChangeLogPanel apiUrl={apiUrl} objectUuid={objectUuid} onClose={() => setShowChangeLogs(false)} />
  )}
};
```

Do not reach for `useDetailViewContext`/`DetailViewProvider` here — those
exist for the framework's own drawer internals and assume that provider is
mounted above you, which a standalone routed page is not guaranteed to have.
`customMainDetail` already receives `apiUrl` and `objectUuid` as props (§3);
build the fetch from those directly.

## 4d. Record info — created/modified fields are already in the payload, just render them

**`BaseDetail.get_general_details()` merges `created_at`, `created_by`,
`modified_at` and `modified_by` into `generalDetails.fields` automatically,
for every entity, with no backend work required** — see
`packages/crud/detail/base.py` → `get_auditlog_details()`. This is easy to
miss because they are not in the table's own columns and nothing has to be
added to `Meta.fields` to get them; they show up in the API response whether
or not the page reads them, so a page that only maps a hand-picked list of
"business" fields into its sections silently drops them, and nothing errors.

**The default drawer shows these** (as part of its own generic field list),
so — same failure shape as Change Logs in §4c — switching an entity to a
custom `customMainDetail` page loses this information unless the page adds
it back deliberately. A record with no visible "who created this, when, who
last touched it" reads as unfinished the moment anyone opens the page to
audit a change.

Add one more `Section`/`FieldGrid` pair near the end of the Overview
content — same pattern as every other field group on the page:

```jsx
<Section title="Record info">
  <FieldGrid
    fields={fields}
    keys={['created_by', 'created_at', 'modified_by', 'modified_at']}
  />
</Section>
```

No `render` overrides are needed: `created_at`/`modified_at` arrive
pre-formatted as display strings (`get_datetime_str_in_current_timezone`),
`created_by`/`modified_by` arrive as the actor's name (or `"System"`/`"NA"`
when absent) — unlike most date/FK fields elsewhere on the page, these are
already presentation-ready.

This applies to **every** `BaseDetail`-backed page — a full routed page
(§2) and a custom drawer detail alike — provided the page reads from
`generalDetails.fields` (or the drawer's equivalent `data.general_details`).
It does **not** apply to a drawer built by hand from a raw table row (no
`BaseDetail`, no `fetch_item_details`) — a table row only carries the
columns the table itself declared, and `created_by`/`created_at` are not
among them unless added as explicit table columns, which changes the list
view too. For that shape, treat the audit fields as out of scope rather than
forcing them onto the table.

## 5. The stability rule — read this before writing the page

`customTableBody`, `customMainDetail` and any component passed to `CrudHandler`
**must be a stable module-scope reference**.

`CrudHandler` mounts what it is given as a *component type*. An arrow function
defined inside a render creates a **new identity on every render**, so React
unmounts and remounts the entire CRUD subtree each pass:

> remount → refetch → a total is reported → parent re-renders → remount → …

an infinite refetch loop that looks like a hanging page and hammers the backend.

```jsx
// WRONG — new identity every render, remount loop
<CrudHandler customTableBody={() => <TableBody defaultDetailView="navigate" />} />

// RIGHT — declared once, at module scope
const NavigateTableBody = () => <TableBody defaultDetailView="navigate" />;
<CrudHandler customTableBody={NavigateTableBody} />
```

Two corollaries:

- `customTableBody` takes a **component reference, not a JSX element**. Passing
  `<TableBody />` crashes with *"Element type is invalid: got object"*.
- Any count/`onTotal`-style callback from a child table must write to a **store**
  (or a ref), **never to parent React state** — setting parent state from a
  child's fetch result re-renders the parent, which remounts the child, which
  refetches. Same loop, different door.

## 6. Required page anatomy

1. **Header / identity** — title, unique reference, avatar or icon, workflow
   status chip, primary actions, back link, and a **Change Logs** action
   (§4c) — the default drawer has one and a custom page must not lose it.
2. **Key-facts strip** — the 4–8 most-consulted fields from
   `generalDetails.fields`. Not all of them; the rest belong in Overview.
3. **Overview tab** — remaining fields grouped into titled sections (use
   `sections` when the backend supplies it), ending with a **Record info**
   section for `created_by`/`created_at`/`modified_by`/`modified_at` (§4d) —
   already in the payload, the default drawer shows them, a custom page must
   not lose them.
4. **One tab per child relation** — a scoped `CrudHandler`, labelled with a
   count badge.
5. **Timeline / activity** — where the entity has a lifecycle.
6. **States** — a skeleton while loading, an empty state per tab, an error
   state. Not optional; see [design-system.md](design-system.md).

```
┌─────────────────────────────────────────────────────────┐
│ ← Patients                                              │
│ ◉  Jane Doe · PT-10482            [Active]   [Edit] [⋯] │
│    Enrolled 12 Mar · Dr. Smith · Sydney · Program PSP-A │
├─────────────────────────────────────────────────────────┤
│ Overview │ Orders 7 │ Programs 2 │ Documents 5 │ Timeline│
├─────────────────────────────────────────────────────────┤
│ ▤ CrudHandler → /orders/?patient_uuid=<uuid>            │
│   search · filters · row actions · pagination · add     │
└─────────────────────────────────────────────────────────┘
```

## 7. Reference skeleton — a floor, not a template

**Read this for the mechanics, then write your page from
[shared-primitives.md](shared-primitives.md) instead.**

This skeleton exists to show *how the props and the child-table wiring work*,
so it is deliberately bare. It is **not** the quality bar, and transcribing it
is the known failure mode: an observed run shipped four detail pages that were
this skeleton with the Tailwind classes mechanically converted to inline
`style` objects — no shared primitives, no loading state, no empty state,
literal hexes throughout, and a hard-coded `$` on a non-US app. Every file
existed; nothing errored; the app looked unfinished.

So when you write the real page:

- compose `PageShell` / `PageHeader` / `KeyFacts` / `Tabs` from
  [shared-primitives.md](shared-primitives.md) rather than repeating this
  markup per page;
- keep the classes as **classes** — the scaffold ships Tailwind v4;
- add the states this skeleton omits: a shape-matched skeleton while loading,
  an empty state *per child tab*, an error state;
- take colours from `var(--color-*)` tokens, never a literal hex;
- adapt the anatomy to the entity — a sales order wants its line-items table
  and total; a retailer wants a balance and payment history.

The mechanics below (camelCase props, module-scope constants, the scoped
`CrudHandler`) are what to carry across verbatim. The styling is not.

```jsx
// src/custom/pages/PatientDetail.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CrudHandler } from '@zango-core/crud/table';
import { WorkflowStatus } from '@zango-core/crud/table';

// --- module scope: stable references only (see §5) ---
const CHILD_TABS = [
  { key: 'orders',    label: 'Orders',    endpoint: '/orders/',    param: 'patient_uuid' },
  { key: 'programs',  label: 'Programs',  endpoint: '/programs/',  param: 'patient_uuid' },
  { key: 'documents', label: 'Documents', endpoint: '/documents/', param: 'patient_uuid' },
];

const KEY_FACTS = ['patient_id', 'enrolled_on', 'primary_physician', 'city'];

const PatientDetail = ({ data, generalDetails, workflowDetails, objectUuid, apiUrl, onRefresh }) => {
  const navigate = useNavigate();
  const [tab, setTab] = useState('overview');
  const [showChangeLogs, setShowChangeLogs] = useState(false); // see §4c

  // Loading: a skeleton, never a bare spinner or an empty div.
  if (!data) return <div className="h-40 rounded-xl bg-gray-100 animate-pulse" />;

  const fields = generalDetails?.fields || {};

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* 1. header / identity */}
      <button onClick={() => navigate(-1)} className="text-sm text-gray-500 mb-4">
        &larr; Back
      </button>
      <div className="flex items-center gap-3 pb-4 border-b">
        <h1 className="text-xl font-semibold">{data.title}</h1>
        {workflowDetails && (
          <WorkflowStatus
            apiUrl={`/patients/?object_uuid=${objectUuid}`}
            onStatusChange={onRefresh}
          />
        )}
        {/* §4c — the default drawer has this action; a custom page must keep it */}
        <button onClick={() => setShowChangeLogs(true)} className="ml-auto text-sm text-gray-500">
          Change Logs
        </button>
      </div>
      {showChangeLogs && (
        <ChangeLogPanel
          apiUrl={apiUrl || `/patients/?object_uuid=${objectUuid}`}
          objectUuid={objectUuid}
          onClose={() => setShowChangeLogs(false)}
        />
      )}

      {/* 2. key facts */}
      <div className="grid max-md:grid-cols-2 md:grid-cols-4 gap-4 py-4">
        {KEY_FACTS.map((k) => fields[k] && (
          <div key={k}>
            <span className="block text-xs text-gray-500">{fields[k].display_name}</span>
            <span className="text-sm font-medium">{fields[k].value ?? '—'}</span>
          </div>
        ))}
      </div>

      {/* 3. tabs */}
      <div className="flex gap-4 border-b text-sm">
        {['overview', ...CHILD_TABS.map((t) => t.key)].map((k) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={tab === k ? 'py-2 border-b-2 border-brand-500 font-semibold' : 'py-2 text-gray-500'}
          >
            {k === 'overview' ? 'Overview' : CHILD_TABS.find((t) => t.key === k).label}
          </button>
        ))}
      </div>

      <div className="pt-5">
        {tab === 'overview' ? (
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(fields).map(([k, f]) => (
              <div key={k}>
                <span className="block text-xs text-gray-500">{f.display_name}</span>
                <span className="text-sm">{f.value ?? '—'}</span>
              </div>
            ))}
          </div>
        ) : (
          // 4. child table — scoped, and filtered again server-side (§4)
          (() => {
            const t = CHILD_TABS.find((x) => x.key === tab);
            return (
              <CrudHandler
                api_endpoint={`${t.endpoint}?${t.param}=${objectUuid}`}
                headerProps={{ title: t.label }}
              />
            );
          })()
        )}
      </div>
    </div>
  );
};

export default PatientDetail;
```

Export it from `src/custom/pages/index.js`, and remember the route's `component`
value must match the export name **exactly**:

```js
export { default as PatientDetail } from './PatientDetail';
```

## 8. Checklist

- [ ] Focus objects chosen from the FK graph; selection justified in the summary
- [ ] `enableDetailViewRoute` + `customMainDetail` + `customTableBody` all three set
- [ ] **Set on EVERY table of that entity**, not just its list page — dashboard
      worklists, role landing pages and child tabs included (§2). One shared
      wrapper component per entity is the reliable way
- [ ] Detail component reads **camelCase** props (`generalDetails`, `workflowDetails`)
- [ ] **Every `BaseDetail` subclass declares `Meta.fields`** listing every field
      the page reads — without it the payload falls back to the *table's*
      columns and the missing ones read as `undefined` (§3b)
- [ ] **No `undefined → 0` coercion.** A missing field renders `—`, never a
      number that looks deliberate
- [ ] **One real record checked against its stored values** — the page's numbers
      match the database, not just each other
- [ ] Every child table is a scoped `CrudHandler` on the child's own endpoint
- [ ] **Every child endpoint filters its queryset server-side**
- [ ] **Change Logs action present** (§4c) — wired to `action=fetch_audit_logs`
      on the entity's own endpoint, not lost along with the default drawer
- [ ] **`changes` rendered as `Object.entries`, never `{log.changes}` directly**
      (§4c) — it is an object of `[old, new]` pairs, not a string; rendering
      it as a plain child throws React error #31 and crashes the whole panel.
      Verified against a real `Update` log entry, not just a `Create`-only one
- [ ] **Change Logs trigger and close control are styled buttons** (§4c) — a
      bordered pill with an icon for the trigger, a bordered icon button for
      close; not bare text or a literal `&times;`
- [ ] **Record info section present** (§4d) — `created_by`, `created_at`,
      `modified_by`, `modified_at`, already in `generalDetails.fields` with
      no backend change needed; the default drawer shows them and a custom
      page must not lose them
- [ ] No component passed to `CrudHandler` is defined inline
- [ ] No child callback writes to parent React state
- [ ] Loading skeleton, per-tab empty state, error state all present
- [ ] **Each child tab opened and confirmed to render** — not assumed from a 200
- [ ] Page composed from `shared.tsx` primitives, not hand-rolled per page
- [ ] Tailwind classes, no inline `style` for static styling, no literal hex
- [ ] Export name matches the AppBuilder route's `component`
