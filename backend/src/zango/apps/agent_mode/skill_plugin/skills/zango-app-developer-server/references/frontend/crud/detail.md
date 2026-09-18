# Zango CRUD — Detail Views

> Split from the generated CRUD reference. Shared basics (imports, API
> response formats, column types, CrudHandler) are in [core.md](core.md).

## Detail Views (Views)

**Sections:** Overview | Automatic Data Fetching | Data Props Provided | Drawer Detail View | Main Detail View (Route-based) | DetailViewProvider | StandaloneDetailView | Detail Hooks

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | object | - | Complete detail response from the API, containing all fields and nested data for the record. |
| `api_endpoint` | string | - | The API endpoint used to fetch the detail data. |
| `loading` | boolean | - | Whether the detail data is currently being fetched. |
| `error` | string | null | - | Error message if the data fetch failed, or null if successful. |
| `onRefresh` | function | - | Callback to re-fetch the detail data. Useful after performing mutations like status transitions or edits. |
| `objectUuid` | string | - | The unique object UUID of the current record. |
| `pk` | string | number | - | The primary key of the current record. |
| `title` | string | - | The display title for the detail view, derived from the record data. |
| `general_details` | object | - | General details section with a fields object. Each field is keyed by field_name and has { name, display_name, type, value, searchable, sortable }. |
| `workflow_details` | object | - | Workflow data including current_status (string key), current_status_meta ({ name, from, to, status_label, status_color, is_form_based, is_manual }), next_transitions (array), and tag_details (array). |
| `sections` | array | - | Array of section objects, each with key, name, title, data (object), optional extra_html, and optional form ({ is_multistep, form: { json_schema, ui_schema } }). |
| `row_actions` | array | - | Array of available row-level actions for the current record. |
| `configurations` | object | - | Additional configuration metadata for the detail view. |
| `useDetailView({ apiUrl })` | Hook | - | Fetches detail data for a specific record. Returns: data, loading, error, refresh, objectUuid, workflowDetails, rowActions. |
| `useDetailViewContext()` | Hook | - | Reads from the nearest DetailViewProvider context. Same return shape as useDetailView but from shared context. |

### Code Examples

```jsx
import React from 'react';

const CustomDrawerDetail = ({
  selectedRow,
  open,
  onClose,
  data,
  workflow_details,
  general_details,
  sections,
}) => {
  if (!open || !data) return null;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b">
        <h2 className="text-lg font-semibold">{data.title || 'Detail View'}</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-xl"
        >
          &times;
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* General Details — fields is an object keyed by field_name */}
        {general_details?.fields && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-3">
              General Information
            </h3>
            <div className="space-y-2">
              {Object.entries(general_details.fields).map(([key, field]) => (
                <div key={key} className="flex justify-between py-2 border-b">
                  <span className="text-sm text-gray-500">{field.display_name}</span>
                  <span className="text-sm font-medium">{field.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Workflow Status */}
        {workflow_details && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-3">
              Workflow
            </h3>
            <div
              className="inline-flex items-center px-3 py-1 rounded-full text-sm"
              style={{
                backgroundColor: workflow_details.current_status_meta?.status_color || '#eff6ff',
                color: '#1d4ed8',
              }}
            >
              {workflow_details.current_status_meta?.status_label || workflow_details.current_status || 'N/A'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomDrawerDetail;
```

```jsx
import CustomDrawerDetail from './CustomDrawerDetail';

<CrudHandler
  api_endpoint="/api/users"
  customDrawerDetail={CustomDrawerDetail}
/>
```

```jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';

const CustomMainDetail = ({
  data,
  workflow_details,
  general_details,
  sections,
  onRefresh,
}) => {
  const navigate = useNavigate();

  if (!data) return null;

  return (
    <div className="max-w-4xl mx-auto p-8">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        &larr; Back to list
      </button>

      {/* Title */}
      <h1 className="text-2xl font-bold mb-6">
        {data.title || 'Record Detail'}
      </h1>

      {/* General Details — fields is an object keyed by field_name */}
      {general_details?.fields && (
        <div className="bg-white rounded-lg border p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">General Information</h2>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(general_details.fields).map(([key, field]) => (
              <div key={key}>
                <span className="text-sm text-gray-500 block">{field.display_name}</span>
                <span className="text-sm font-medium">{field.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sections */}
      {sections?.map((section) => (
        <div key={section.key} className="bg-white rounded-lg border p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">{section.title}</h2>
          {section.data && (
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(section.data).map(([key, value]) => (
                <div key={key}>
                  <span className="text-sm text-gray-500 block">{key}</span>
                  <span className="text-sm font-medium">{String(value)}</span>
                </div>
              ))}
            </div>
          )}
          {section.extra_html && (
            <div dangerouslySetInnerHTML={{ __html: section.extra_html }} />
          )}
        </div>
      ))}

      {/* Workflow Section */}
      {workflow_details && (
        <div className="bg-white rounded-lg border p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Workflow</h2>
          <div>
            <p className="text-sm text-gray-500 mb-2">Current Status</p>
            <span
              className="inline-flex px-3 py-1 rounded-full text-sm"
              style={{
                backgroundColor: workflow_details.current_status_meta?.status_color || '#eff6ff',
                color: '#1d4ed8',
              }}
            >
              {workflow_details.current_status_meta?.status_label || workflow_details.current_status}
            </span>
          </div>
          {workflow_details.next_transitions?.length > 0 && (
            <div className="flex gap-2 mt-4">
              {workflow_details.next_transitions.map((t) => (
                <span key={t.name} className="text-sm text-gray-600">
                  {t.display_name} &rarr; {t.to_state_meta?.status_label}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Refresh */}
      <button
        onClick={onRefresh}
        className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
      >
        Refresh Data
      </button>
    </div>
  );
};

export default CustomMainDetail;
```

```jsx
import CustomMainDetail from './CustomMainDetail';

<CrudHandler
  api_endpoint="/api/users"
  customMainDetail={CustomMainDetail}
  customTableBody={
    <TableBody defaultDetailView="navigate" />
  }
/>
```

> **VERIFIED WORKING PATTERN** — all 3 props are required together:
> - `enableDetailViewRoute={true}` — registers the `/detail-view/:object_uuid` route
> - `customMainDetail={MyDetail}` — your component rendered at that route
> - `customTableBody={NavigateTableBody}` — makes rows navigate on click
>
> ⚠️ `customTableBody` must be a **component reference**, NOT a JSX element. Passing `<TableBody ... />` (an object) crashes with "Element type is invalid: got object". Wrap it in a named component.
>
> ⚠️ Props received by `customMainDetail` are **camelCase** (verified from source): `generalDetails` (not `general_details`), `workflowDetails` (not `workflow_details`).

```jsx
import { useNavigate } from 'react-router-dom';
import { CrudHandler, TableBody } from '@zango-core/crud/table';

// Must be a named component — NOT inline JSX passed to customTableBody
const NavigateTableBody = () => <TableBody defaultDetailView="navigate" />;

// Actual props: data, generalDetails, objectUuid, workflowDetails, sections, rowActions, pk, onRefresh, apiUrl
const MyDetail = ({ data, generalDetails, objectUuid }) => {
  const navigate = useNavigate();
  if (!data) return null;
  const fields = generalDetails?.fields || {};
  return (
    <div style={{ padding: 32 }}>
      <button onClick={() => navigate(-1)}>← Back</button>
      <h1>{data.title}</h1>
      {Object.entries(fields).map(([key, field]) => (
        <div key={key}>
          <div style={{ fontSize: 12, color: '#9CA3AF' }}>{field.display_name}</div>
          <div dangerouslySetInnerHTML={{ __html: field.value || '—' }} />
        </div>
      ))}
      {/* Embed related child records — requires get_table_data_queryset override on backend */}
      {objectUuid && (
        <CrudHandler api_endpoint={`/child/records/?parent_uuid=${objectUuid}`} showHeader={false} />
      )}
    </div>
  );
};

const MyPage = () => (
  <CrudHandler
    api_endpoint="/my/records/"
    headerProps={{ title: 'My Records' }}
    enableDetailViewRoute={true}
    customMainDetail={MyDetail}
    customTableBody={NavigateTableBody}
  />
);
```

```jsx
import { DetailViewProvider, WorkflowStatus, WorkflowTags } from "@zango-core/crud/table";

// Wrap components for shared context
<DetailViewProvider apiUrl="/api/users/?object_uuid=123">
  <WorkflowStatus />   {/* Automatically uses context */}
  <WorkflowTags />     {/* Automatically uses context */}
  <MyCustomComponent /> {/* Can call useDetailViewContext() */}
</DetailViewProvider>
```

```jsx
import { StandaloneDetailView } from "@zango-core/crud/table";

<StandaloneDetailView
  apiUrl="/api/users/"
  objectUuid="550e8400-e29b-41d4-a716-446655440000"
/>
```

```jsx
import { useDetailView, useDetailViewContext } from "@zango-core/crud/table";

// Standalone - fetches its own data
const { data, loading, workflowDetails } = useDetailView({
  apiUrl: "/api/users/?object_uuid=123"
});

// Context-based - reads from DetailViewProvider
const { data, refresh } = useDetailViewContext();
```

---
