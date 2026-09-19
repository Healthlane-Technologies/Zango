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
[design-system.md](design-system.md) §5b, "a custom detail page with no child tables."
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

The entity's own list page is then just that wrapper, mounted bare — **no
`PageShell`, no padding div, no surface of your own around it**:

```jsx
// bookings/BookingList.tsx — the whole page.
const BookingList = () => <BookingsTable headerProps={{ title: 'Bookings' }} />;
```

A `CrudHandler` already renders its own card, title bar, filter row and
padding. Wrapping it adds a grey gutter between the sidebar and the table and
costs ~48px of width, which clips the last column on a laptop. `PageShell` is
for detail and custom pages — see
[design-system.md](design-system.md) § "`PageShell` does not go around a list page".

To check, grep for every table of the entity and confirm the count matches the
number wired:

```bash
grep -rn "bookings/bookings/" src/custom/ | wc -l   # tables of this entity
grep -rn "customMainDetail" src/custom/ | wc -l     # tables wired to the page
```

### But only ONE of them may be mounted on any single page

The rule above is about *entities*, not about *instances*. `enableDetailViewRoute`
registers the `/detail-view/:object_uuid` route, and **that route is a singleton
per rendered page.** Mount the wrapper twice on one page and both instances claim
it: on navigation, each renders your detail component *in its own container*,
side by side.

This bites exactly the layout this skill encourages — a dashboard with one table
per workflow stage:

```jsx
// WRONG — four wrappers on one page, four detail views at once.
{STAGES.map((s) => (
  <RailCard key={s.key} title={s.label}>
    <BookingsTable api_endpoint={`/bookings/bookings/?stage=${s.key}`} />
  </RailCard>
))}
<BookingsTable api_endpoint="/bookings/bookings/?assigned_to_me=1" />
```

Clicking a row renders the detail page inside a ~340px dashboard column —
every label wrapping one letter per line — while the other three columns render
it again behind it. Nothing throws. The list page looks perfect, so this
survives every check that only opens the list.

On a multi-table page, let the tables **navigate to the canonical route** and
mount the detail-owning wrapper only on the entity's own list page:

```jsx
// RIGHT — dashboard tables navigate; they do not own the route.
<BookingsTable
  api_endpoint={`/bookings/bookings/?stage=${s.key}`}
  enableDetailViewRoute={false}
  customMainDetail={undefined}
  onRowClick={(row) => navigate(`/app/bookings/detail-view/${row.object_uuid}`)}
/>
```

Or give the wrapper a `detailRoute` prop that defaults on and is passed `false`
by every dashboard caller — whichever you choose, the invariant to hold is:

> **Exactly one mounted `CrudHandler` per page may set `enableDetailViewRoute`.**

Check it per page, not just per entity:

```bash
# For each page component, count wrappers that own the route. Must be 0 or 1.
grep -c "BookingsTable" src/custom/pages/Home.tsx
```

### A filtered `api_endpoint` breaks the detail fetch

`CrudHandler` carries the endpoint's **query string into the detail request**.
So a table scoped with a filter issues:

```
/bookings/bookings/?stage=done&object_uuid=<uuid>&action=fetch_item_details&view=detail
```

The server applies `stage=done` to the lookup as well. If the record you clicked
is not in that stage, `get_queryset()` cannot find it and `BaseDetail` raises an
unhandled `DoesNotExist` — **HTTP 500**, not a 404. On a stage-per-column
dashboard, every column except the matching one 500s on every row click.

The filter belongs on the *list* request only. Either drop it from the detail
route by having dashboard tables navigate (previous section), or scope the table
server-side — a dedicated view or a `get_queryset()` that reads the filter only
when `action=get_table_data` — rather than in the endpoint the detail fetch
inherits.

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
  rowActions,       // the table's row_actions, e.g. Edit — render these yourself (§4e)
  objectUuid,       // the record's UUID — what you scope child tables by
  pk,
  onRefresh,        // re-fetch after a mutation — refreshes THIS record only, not child tabs (§4b)
  apiUrl,
}) => { ... };
```

Each entry in `generalDetails.fields` is
`{ name, display_name, type, value, searchable, sortable }`.

### `workflowDetails.current_status_meta` has no `label` key

The status label is `status_label`. `current_status_meta` is the **transition**
metadata for the transition that produced the current state, with the status
fields merged in — see `packages/workflow/base/engine.py::get_current_status()`:

```json
"workflow_details": {
  "current_status": "in_progress",
  "current_status_meta": {
    "name": "to_do_to_in_progress",   // the TRANSITION's name, not the status
    "display_name": "Start",          // the TRANSITION's label — not the status label
    "from": "to_do",
    "to": "in_progress",
    "status_label": "In Progress",    // <- the status label lives HERE
    "status_color": "blue"
  },
  "next_transitions": [...],
  "tag_details": []
}
```

There is no `.label`, and no `.name` that means the status. Both spellings are
the ones you reach for, both are `undefined`, and both fail **silently into your
fallback** — so a stepper or badge written like this pins to the first stage for
every record, forever:

```jsx
// WRONG — .label is always undefined; every task reads "To Do".
const current = workflowDetails?.current_status_meta?.label || 'To Do';

// RIGHT — status_label, falling back to the raw status key.
const current = workflowDetails?.current_status_meta?.status_label
  || workflowDetails?.current_status;
```

Reading `display_name` is the same bug wearing a better disguise: it resolves,
so there is no fallback to notice, but it renders the *transition* name
("Start") where you wanted the *status* ("In Progress").

If you drive a `ProcessStepper` from this, assert the lookup actually hits —
`stages.indexOf(current)` returning `-1` means you read the wrong key, and
clamping it to `0` with `Math.max(0, ...)` is what converts the bug into a
confident wrong answer.

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

### The tab's Add button — don't make the user pick the parent

That add button (§4) opens the child module's **own** form — the same form its
standalone list page opens. Left alone, it asks the user to select the parent
they are already looking at: on the Vehicle page, "Add Service Job" shows a
Vehicle dropdown. That is a wrong question, and picking the wrong row files the
record against another parent.

The fix reuses the filter you just wired. The parent uuid is already on the
endpoint, so it reaches the form too — in the child form's `__init__`, preset
the FK from that param and hide it; when the param is absent (the module's own
list page, no parent in context) leave the field as a normal select. One form,
both contexts — no second form class, no view override.

```python
# backend/jobs/forms.py -- child module's form
request = getattr(self.crud_view_instance, "request", None)
parent_uuid = request.GET.get("vehicle_uuid") if request else None
```

Full pattern, and the shared-state trap that makes the naive version leak the
hidden field into the standalone form:
[../packages/crud/forms/core.md](../packages/crud/forms/core.md) → *The parent
FK on a child-tab form*.

The param is one string spelled in three places — this `api_endpoint`, the
table's `get_table_data_queryset`, and the child form. Keep them identical.

> Applies only to the FK **pointing at this page's entity**. Any other FK on
> the child form (a part, a technician) is a real question and stays a normal
> select — with no `autocomplete=` on it.

## 4b. Reading child rows yourself — the four traps

`CrudHandler` renders a child table for you. But a **lead card that
synthesises** (design-system.md §4) usually needs the rows themselves — the
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

**4. Nothing refetches them after a write.** A `useEffect` keyed on
`[objectUuid]` runs **once** — and `objectUuid` never changes while the user is
on the page. `CrudHandler` refreshes its *own* table after a save, so the tab
updates while every number you fetched yourself stays frozen at its page-load
value. The user adds a row, watches the table grow, and the tab badge and stat
cards beside it still show the old count. **Observed, not theoretical**: after
adding a rent payment the same page read "Rent Payments (4)" in the table, "3"
in the tab badge and "3" in the stat card, and only a full reload agreed.

**The page and the table do NOT share one `QueryClient` — do not reach for
`invalidateQueries` to fix this.** Every `CrudHandler` mounts its own private
`QueryClient` inside its own `TableProvider` (`@zango-core/crud`'s
`table.es.js` — `TableProvider` does `useMemo(() => createQueryClient(), [])`
unconditionally, with no check for an ancestor provider). Its `TableAddButton`
calls `useQueryClient()`, which React resolves to that **private** client, and
invalidates `['tableData']` **inside it only**. If your page also owns a
`QueryClient` (App-root, so `useQuery` even works on a custom page — see the
note below) and keys its own reads under `['tableData', ...]`, that is a
**third, separate cache**. Nothing you do with `invalidateQueries` from your
page ever reaches the table's private one, and nothing the table invalidates
ever reaches yours. Two different objects, same key prefix, no relationship —
a version of this doc claimed otherwise ("the page and the table share one
QueryClient"); that was wrong and never worked.

There is also no prop for this: `CrudHandler` does **not** forward an
`onSuccess`/`onFormSuccess` prop, and do not reach for one either —
`formProps` only reaches its own **Add-button** form (spread last over the
framework's own `onResponse`, so passing your own **replaces** the table's
save handler and silently drops its toast and its own cache invalidation).

**The only lever that actually crosses this boundary is a remount.** Own a
`reloadKey` counter on the page and bump it wherever a write could have
happened that this page needs to reflect elsewhere: the page's own row-actions
kebab (§4e) succeeding, and — cheapest and sufficient — every tab switch, since
a child tab's `CrudHandler` only needs to be fresh when it is actually shown:

```tsx
const [reloadKey, setReloadKey] = useState(0);
const bumpReload = () => setReloadKey((k) => k + 1);

// Rows you fetch yourself — reloadKey in the query key forces a refetch.
const payments = useQuery({
  queryKey: ['tableData', 'rent_payments', objectUuid, reloadKey],
  queryFn: () => fetchRows(endpoint, param, objectUuid),
  enabled: !!objectUuid,
});

<Tabs value={tab} onChange={(next) => { setTab(next); bumpReload(); }} items={...} />

{tab === 'payments' && (
  <CrudHandler key={reloadKey} api_endpoint={...} headerProps={{ title: 'Payments' }} />
)}
```

A child tab's own internal Add/edit/row-action still refreshes **itself**
correctly (that is what its private `QueryClient` is for) — the remount only
needs to catch what that private cache cannot reach: this page's own derived
numbers, and the *other* tab.

**A `useQuery` on a custom page needs an app-root `QueryClientProvider` to
exist at all**, or it crashes with `No QueryClient set, use QueryClientProvider
to set one` the first time a custom page (not a `CrudHandler`) calls it — none
of the skill's `App.tsx` templates create one by default. Wrap `ZangoApp` once:

```tsx
// App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ZApp ... />
  </QueryClientProvider>
);
```

Add `@tanstack/react-query` as an explicit `dependencies` entry in
`package.json` too — without it the import only resolves because
`@zango-core/appbuilder`/`@zango-core/crud` happen to bundle it as a
transitive dependency, which is not a contract to build on.

**This is not only about counts.** Anything the page derived from those rows
goes stale the same way: a "paid in full" percentage, an outstanding balance,
an open-complaints tile, a synthesised lead card. One row written by a child
tab can leave every number on the page stale until the counter bumps.

**Verify with the numbers, not the network tab.** All four return 200. The
only reliable check is that the count in your card matches the row count in
the table rendered beside it — if the card says 0 and the table shows rows,
you have hit one of the first three. **Then add a row from the child tab,
switch away and back**: if the table moved but your number did not update by
the time you return, that is trap 4.

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

## 4e. Row actions — the default drawer's kebab menu, again

**The default drawer's kebab menu also lists every entry in the table's
`row_actions`** (`packages/crud/tables/core.md`) — Edit, and anything else the
table declares. Same failure shape as Change Logs (§4c) and Record info (§4d):
switching an entity to a custom `customMainDetail` page drops this menu
entirely, and `customMainDetail` receives a `rowActions` prop (§3) for exactly
this reason — it is documented as existing but this doc had no example of
using it, so the natural next move is to hand-roll an Edit button against the
**wrong server contract**.

**There are two contracts, and they are not interchangeable.** `form.md`'s
plain `FormRenderer` example (`getParams: { action: "initialize_form",
form_type: "edit_form", object_uuid }`) is for a form with no row-action
declaration behind it. An entity whose edit behaviour is declared via
`row_actions` — the framework's default table pattern, and what
`tables/core.md` teaches — is dispatched server-side through a **different**
branch (`BaseCrudView` checks `action_type == "row"` before routing to
`get_row_action_form`, see `packages/crud/views/reference.md`). Calling the
plain edit-form params against a `row_actions`-only entity hits a code path
that was never wired for that model and fails. Match the framework's own
drawer kebab (`@zango-core/crud`'s `table.es.js`) instead:

```tsx
// GET  (open the form)
getParams: {
  action: 'initialize_form',
  action_type: 'row',
  action_key: action.key,   // 'edit', or whatever the table declared
  object_uuid: objectUuid,
}
// POST (submit it)
postParams: {
  form_type: 'row_action_form',
  action_type: 'row',
  action_key: action.key,
  object_uuid: objectUuid,
}
```

A `type: "simple"` action (no form, confirm-then-run) is a bare POST to the
same base endpoint, no `FormRenderer` involved:

```tsx
POST `${baseUrl}?action_type=row&action_key=${action.key}&object_uuid=${objectUuid}`
```

**Build one small reusable menu in `shared.tsx`, not a bespoke Edit button per
page.** A table can declare any number of `row_actions` (`tables/core.md`
covers role-restricted, multi-action tables), so the menu should read
`rowActions` and render all of them — a three-dot button in the page header
next to Change Logs, opening a dropdown, each entry driving whichever contract
above matches its `type`. On success, refetch — see §4b for why
`invalidateQueries` alone does not reach a sibling `CrudHandler`'s table, and
why a `reloadKey` bump (calling the page's `onRefresh` too, so the main detail
record itself is current) is the mechanism that actually works.

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
- [ ] **…but only ONE mounted table per page owns the route.** On a page with
      several tables of one entity (stage columns, worklists), the others
      navigate to the canonical detail route instead (§2). Two owners = the
      detail page renders inside a dashboard column
- [ ] **No filter in the `api_endpoint` of a detail-owning table** — the query
      string rides along into `fetch_item_details` and 500s on any record the
      filter excludes (§2)
- [ ] Detail component reads **camelCase** props (`generalDetails`, `workflowDetails`)
- [ ] **Status read as `current_status_meta.status_label`**, never `.label`
      (always `undefined`, fails silently into your fallback) or `.display_name`
      (the transition's name, not the status) (§3). If a stepper indexes stages
      by it, `indexOf` must not return `-1`
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
- [ ] **Row actions menu present** (§4e) — every entry in the `rowActions`
      prop, driven through `action_type=row`/`action_key`/`form_type=
      row_action_form` (form actions) or a bare POST with the same
      `action_type`/`action_key` (simple actions) — **not** `form.md`'s plain
      `form_type=edit_form` contract, which is for entities with no
      `row_actions` declaration behind them
- [ ] **App root has a `QueryClientProvider`** (§4b) if any custom page uses
      `useQuery` — `@tanstack/react-query` is also an explicit `package.json`
      dependency, not just a transitive one
- [ ] No component passed to `CrudHandler` is defined inline
- [ ] No child callback writes to parent React state
- [ ] Loading skeleton, per-tab empty state, error state all present
- [ ] **Each child tab opened and confirmed to render** — not assumed from a 200
- [ ] **A row added from a child tab updates the page's own numbers, and the
      other tab, once you switch back to them** (§4b trap 4) — tab badges,
      stat cards and any synthesised figure. `CrudHandler`'s own `QueryClient`
      is private to itself (confirmed in `@zango-core/crud` source) and does
      **not** reach your page's own queries or a sibling tab's table — a
      `reloadKey` bumped on tab switch and on the page's own row-actions
      success is what actually crosses that boundary, not `invalidateQueries`
- [ ] Page composed from `shared.tsx` primitives, not hand-rolled per page
- [ ] Tailwind classes, no inline `style` for static styling, no literal hex
- [ ] Export name matches the AppBuilder route's `component`
