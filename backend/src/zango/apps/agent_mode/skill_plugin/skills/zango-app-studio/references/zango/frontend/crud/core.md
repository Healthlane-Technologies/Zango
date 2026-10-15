# Zango CRUD Reference

> Auto-generated from documentation pages. Regenerate with: `node scripts/generate-reference.js`

## Quick Import Reference
```js
import { CrudHandler, useTable, TableBody, TableHeader, TableUtilities, TablePagination, TableSearch, TableAddButton } from '@zango-core/crud/table';
import { WorkflowStatus, WorkflowTags, DetailViewProvider } from '@zango-core/crud/table';
import { useTableSearch, useTableFilters, useTablePagination, useTableSelection, useTableColumns, useTableActions } from '@zango-core/crud/table';
import type { TableCustomClasses, TableCustomStyles } from '@zango-core/crud/table';
```

## API Response Formats

### Table Metadata (GET ?action=get_table_metadata)
```json
{ "success": true, "response": { "table_metadata": { "columns": [{ "name": "field", "display_name": "Field", "type": "string", "sortable": true }], "filters": [...], "page_title": "Title", "has_add_perm": true, "has_upload_perm": false, "has_download_perm": true, "utilities_config": { "show_search": true, "show_filters_button": true, "show_column_options": true }, "form_config": { "drawer_size": "md" }, "actions": [{ "name": "Edit", "key": "edit", "type": "form" }] } } }
```

### Table Data (GET ?action=get_table_data&view=table)

> **⚠️ `&view=table` is required.** Calling `?action=get_table_data` without `&view=table` returns a partial or incorrect response. Always include it when fetching table data directly.

The raw endpoint returns **DataTables format** (not a `response.table_data` wrapper):
```json
{ "draw": 0, "recordsTotal": 25, "recordsFiltered": 25, "data": [{ "id": 1, "object_uuid": "uuid", "workflow_status": { "status_label": "Active", "status_color": "#12B76A" }, "row_actions": [{ "name": "Edit", "key": "edit", "type": "form" }] }] }
```

> **Note:** `CrudHandler` internally normalizes this — the DataTables format only matters when calling the endpoint directly (e.g. in a custom `fetch` inside `customTableBody`). Read from `data.data` (the array), not `data.response.table_data`.

### Detail View (GET ?action=fetch_item_details&object_uuid=UUID)
```json
{ "success": true, "response": { "pk": 1, "object_uuid": "uuid", "title": "Title", "general_details": { "fields": { "name": { "name": "name", "display_name": "Name", "type": "string", "value": "val" } } }, "workflow_details": { "current_status": "active", "current_status_meta": { "status_label": "Active", "status_color": "#12B76A" }, "next_transitions": [{ "name": "approve", "display_name": "Approve", "is_form_based": false, "to_state_meta": { "status_label": "Approved" } }], "tag_details": [{ "name": "urgent", "state": "enabled", "tag_label": "Urgent" }] }, "sections": [{ "key": "overview", "title": "Overview", "data": {} }] } }
```

## Column Types
- `string`, `integer`, `float`, `boolean`, `date`, `datetime`, `email`, `file`, `url`, `uuid`, `json`
- `StatusCol` - data: `{ status_label, status_color }`
- `TagsCol` - workflow tags
- `ActionsCol` - row actions: `[{ name, key, type: "form"|"simple", confirmation_message }]`
- `WorkflowTransitionsCol` - available transitions

---


## CrudHandler (Core Component)

**Sections:** Import | Quick Start | Required Props | Section Visibility Controls | Route Controls | Drawer Configuration | Custom Component Overrides | Additional Configuration | Header Configuration (headerProps) | Utilities Configuration | Examples

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `api_endpoint` | string | - | The API endpoint to fetch table data from. Example: /api/crud/ |
| `showHeader` | boolean | true | Show or hide the header section. |
| `showUtilities` | boolean | true | Show or hide the utilities panel (search, filters, actions). |
| `showBody` | boolean | true | Show or hide the table body. |
| `showPagination` | boolean | true | Show or hide pagination controls. |
| `enableDetailViewRoute` | boolean | false | Enable /detail-view/:object_uuid route and  |
| `customHeader` | ReactNode | string | - | Replace the default header. Can be a component or HTML string. |
| `customUtilities` | ReactNode | - | Replace the utilities/action bar section. |
| `customTableBody` | ReactNode | - | Replace the default table body. |
| `customPagination` | ReactNode | - | Replace the default pagination. |
| `customDrawerDetail` | ReactNode | - | Provide a custom drawer-style detail view. Automatically receives fetched detail data. |
| `customMainDetail` | ReactNode | - | Provide a custom main detail view for route-based navigation. Automatically receives fetched detail data. |
| `tableId` | string | - | Unique identifier for the table, used for state management. Auto-generated from api_endpoint if not provided. |
| `columns` | any[] | - | Array of column definitions for client-side column configuration. |
| `className` | string | - | Custom CSS class for the main container. |
| `style` | React.CSSProperties | - | Custom inline styles for the main container. |
| `customClass` | TableCustomClasses | - | Object with CSS class overrides for table elements. |
| `customStyle` | TableCustomStyles | - | Object with dynamic style functions for table elements. |
| `headerProps.showSearch` | boolean | - | Show/hide search in header. |
| `headerProps.showFilters` | boolean | - | Show/hide filter controls. |
| `headerProps.showActions` | boolean | - | Show/hide action buttons. |
| `headerProps.searchPlaceholder` | string | - | Custom search placeholder text. |
| `headerProps.title` | string | - | Header title text. |
| `headerProps.customLeftActions` | ReactNode | - | Custom actions on the left side. |
| `headerProps.customRightActions` | ReactNode | - | Custom actions on the right side. |
| `has_add_perm` | boolean | true | Show/hide the  |
| `has_upload_perm` | boolean | false | Show/hide the upload button in utilities. |
| `has_download_perm` | boolean | true | Show/hide the download button in utilities. |
| `show_search` | boolean | true | Show/hide search input in utilities bar. |
| `show_filters_button` | boolean | true | Show/hide filters toggle button. |
| `show_column_options` | boolean | true | Show/hide column visibility options. |
| `utilityProps.showSearch` | boolean | true | Override: show/hide search input. |
| `utilityProps.showUpload` | boolean | false | Override: show/hide upload button. |
| `utilityProps.showDownload` | boolean | true | Override: show/hide download button. |
| `utilityProps.showFiltersButton` | boolean | true | Override: show/hide filters toggle button. |
| `utilityProps.showColumnOptions` | boolean | true | Override: show/hide column visibility options. |
| `utilityProps.searchPlaceholder` | string | - | Custom search placeholder text. |
| `utilityProps.extraLeftActions` | ReactNode | - | Additional actions on the left. |
| `utilityProps.extraRightActions` | ReactNode | - | Additional actions on the right. |

### Code Examples

```jsx
import { CrudHandler } from "@zango-core/crud/table";
```

```jsx
<CrudHandler api_endpoint="/api/users" />
```

```jsx
// Hide specific sections
<CrudHandler
  api_endpoint="/api/users"
  showHeader={false}
  showUtilities={false}
  showPagination={false}
/>
```

```jsx
// Replace entire sections with custom components
<CrudHandler
  api_endpoint="/api/products"
  customHeader={<MyCustomHeader />}
  customUtilities={<MyCustomUtilities />}
  customTableBody={<MyCustomBody />}
  customPagination={<MyCustomPagination />}
/>
```

```json
// GET /api/users/?action=get_table_metadata
{
  "response": {
    "table_metadata": {
      "columns": [...],
      "filters": [...],
      "has_add_perm": true,
      "has_upload_perm": false,
      "has_download_perm": true,
      "utilities_config": {
        "show_search": true,
        "show_filters_button": true,
        "show_column_options": true
      }
    }
  }
}
```

```jsx
<CrudHandler
  api_endpoint="/api/users"
  enableDetailViewRoute={true}
  utilityProps={{
    showUpload: true
  }}
/>
```

```jsx
<CrudHandler
  api_endpoint="/api/crud"
  headerProps={{
    title: "User Management",
    showSearch: true,
    showFilters: true,
    showActions: true,
    searchPlaceholder: "Search users...",
    customLeftActions: <Button>Import</Button>,
    customRightActions: <Button>Export</Button>
  }}
  utilityProps={{
    showSearch: false,
    showUpload: true,
    showDownload: true,
    showFiltersButton: true,
    showColumnOptions: true,
    searchPlaceholder: "Quick search...",
    extraLeftActions: <Button>Bulk Actions</Button>,
    extraRightActions: <Button>Settings</Button>
  }}
  className="custom-table-wrapper"
  style={{ height: '600px' }}
/>
```

```jsx
<CrudHandler
  api_endpoint="/api/orders"
  customHeader="Order Management"
  customUtilities={<MyAdvancedFilters />}
  headerProps={{
    showSearch: false,
    customRightActions: <RefreshButton />
  }}
  utilityProps={{
    showSearch: true,
    showColumnOptions: false
  }}
/>
```

```jsx
<CrudHandler
  api_endpoint="/api/users"
  customDrawerDetail={({ selectedRow, open, onClose, data, workflowDetails }) => (
    <UserDetailDrawer
      user={data}
      workflowDetails={workflowDetails}
      isOpen={open}
      onClose={onClose}
    />
  )}
  customMainDetail={({ data, workflowDetails, onRefresh }) => (
    <UserDetailPage
      userData={data}
      workflowDetails={workflowDetails}
      onRefresh={onRefresh}
    />
  )}
/>
```

---
