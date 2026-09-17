# Entity-360 Detail Views

How to build the detail page for a **focus object** — the entity an app is really
about, and the one other records point at. Patient, Order, Case, Employee,
Customer, Program.

A focus object's detail page is **not** a field dump in a side drawer. It is a
full-page route showing identity, key facts, and the entity's **related records
as tables inside tabs** — orders, programs, documents, notes — all scoped to that
one record.

> Read this together with [crud.md](crud.md) (CrudHandler props, detail-view
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
snake_case. Some older examples in `crud.md` show the snake_case spelling — those
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
> - check `crud.md` for the `CrudHandler` props that list page relies on;
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
> [../packages/crud/tables.md](../packages/crud/tables.md) → *Custom Table Queryset*.

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
   status chip, primary actions, back link.
2. **Key-facts strip** — the 4–8 most-consulted fields from
   `generalDetails.fields`. Not all of them; the rest belong in Overview.
3. **Overview tab** — remaining fields grouped into titled sections (use
   `sections` when the backend supplies it).
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

const PatientDetail = ({ data, generalDetails, workflowDetails, objectUuid, onRefresh }) => {
  const navigate = useNavigate();
  const [tab, setTab] = useState('overview');

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
      </div>

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
- [ ] No component passed to `CrudHandler` is defined inline
- [ ] No child callback writes to parent React state
- [ ] Loading skeleton, per-tab empty state, error state all present
- [ ] **Each child tab opened and confirmed to render** — not assumed from a 200
- [ ] Page composed from `shared.tsx` primitives, not hand-rolled per page
- [ ] Tailwind classes, no inline `style` for static styling, no literal hex
- [ ] Export name matches the AppBuilder route's `component`
