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

That gives the tab a full table for free: search, filters, row actions,
pagination and the add button, governed by the child module's own policies.

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

## 7. Skeleton to copy

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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4">
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
- [ ] Detail component reads **camelCase** props (`generalDetails`, `workflowDetails`)
- [ ] Every child table is a scoped `CrudHandler` on the child's own endpoint
- [ ] **Every child endpoint filters its queryset server-side**
- [ ] No component passed to `CrudHandler` is defined inline
- [ ] No child callback writes to parent React state
- [ ] Loading skeleton, per-tab empty state, error state all present
- [ ] Export name matches the AppBuilder route's `component`
