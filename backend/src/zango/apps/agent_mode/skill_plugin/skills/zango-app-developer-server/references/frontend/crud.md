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

## Table Styling (Styling)

**Sections:** Overview | Basic Usage | Customizable Elements | State-Aware Styling | Theme Examples | Advanced Techniques | Best Practices

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `container` | string | - | Main table container wrapper |
| `tableWrapper` | string | - | Table wrapper element |
| `table` | string | - | The actual table element |
| `headerRow` | string | - | Header row container |
| `headerCell` | string | - | Individual header cells |
| `headerCellPinned` | string | - | Pinned header cells |
| `sortButton` | string | - | Sortable column buttons |
| `sortIcon` | string | - | Sort direction icons |
| `bodyRow` | string | - | Data row containers |
| `bodyRowSelected` | string | - | Selected row state |
| `bodyCell` | string | - | Individual data cells |
| `bodyCellPinned` | string | - | Pinned data cells |
| `utilitiesContainer` | string | - | Action bar container |
| `filterButton` | string | - | Filter toggle buttons |
| `searchInput` | string | - | Search input field |
| `uploadButton` | string | - | File upload button |
| `downloadButton` | string | - | Download/export button |
| `paginationContainer` | string | - | Pagination wrapper |
| `paginationButton` | string | - | Page number buttons |
| `paginationNavButton` | string | - | Previous/next buttons |
| `paginationInfo` | string | - | Page info display |
| `paginationEllipsis` | string | - | Overflow indicators |
| `filterSidebar` | string | - | Filter panel container |
| `filterHeader` | string | - | Filter panel header |
| `filterTitle` | string | - | Filter title text |
| `filterClearAll` | string | - | Clear filters button |
| `filterContent` | string | - | Filter content area |
| `filterAccordion` | string | - | Filter accordion wrapper |
| `actionsContainer` | string | - | Row actions wrapper |
| `actionButton` | string | - | Individual action buttons |
| `actionMenuButton` | string | - | Action menu trigger |
| `actionDropdown` | string | - | Action dropdown menu |
| `actionDropdownItem` | string | - | Action menu items |
| `statusBadge` | string | - | Status display badges |
| `tagsContainer` | string | - | Tags wrapper |
| `workflowContainer` | string | - | Workflow elements wrapper |
| `workflowButton` | string | - | Workflow action buttons |
| `workflowDropdown` | string | - | Workflow dropdown menu |

### Code Examples

```jsx
<CrudHandler
  api_endpoint="/api/users"
  customClass={{
    headerCell: "bg-blue-100 text-blue-900 font-bold",
    bodyRow: "hover:bg-gray-50",
    filterButton: "border-blue-300 text-blue-600"
  }}
/>
```

```jsx
<CrudHandler
  api_endpoint="/api/users"
  customClass={{
    headerCell: "!bg-gray-800 !text-gray-200 !font-bold",
    bodyRow: "!bg-gray-900 hover:!bg-gray-800",
    filterButton: "!bg-gray-700 !text-gray-200"
  }}
/>
```

```jsx
<CrudHandler
  api_endpoint="/api/users"
  customStyle={{
    bodyRow: (baseStyles, state) => ({
      ...baseStyles,
      backgroundColor: state.isSelected ? '#fef3c7' : baseStyles.backgroundColor,
      borderLeft: state.rowIndex % 2 === 0 ? '4px solid #3b82f6' : 'none'
    }),
    headerCell: (baseStyles, state) => ({
      ...baseStyles,
      fontSize: state.columnId === 'name' ? '18px' : '14px',
      fontWeight: state.isPinned ? 'bold' : 'normal'
    })
  }}
/>
```

```tsx
bodyRow: (baseStyles, state) => {
  // Available state properties:
  // - rowIndex: number
  // - isSelected: boolean
  // - isHovered: boolean
  // - rowData: object

  return {
    ...baseStyles,
    backgroundColor: state.isSelected ? '#fef3c7' :
                    state.rowIndex % 2 === 0 ? '#f9fafb' : '#ffffff'
  };
}
```

```tsx
headerCell: (baseStyles, state) => {
  // Available state properties:
  // - isPinned: boolean
  // - canSort: boolean
  // - columnId: string
  // - pinnedOffset: number

  return {
    ...baseStyles,
    fontWeight: state.canSort ? 'bold' : 'normal',
    borderRight: state.isPinned ? '2px solid #374151' : '1px solid #e5e7eb'
  };
}
```

```tsx
actionButton: (baseStyles, state) => {
  // Available state properties:
  // - action: object (action data)
  // - isFirst: boolean
  // - isInDropdown: boolean

  return {
    ...baseStyles,
    backgroundColor: state.action.type === 'danger' ? '#fef2f2' : baseStyles.backgroundColor
  };
}
```

```jsx
const professionalTheme = {
  customClass: {
    container: 'bg-white border border-gray-200 rounded-lg shadow-sm',
    headerCell: 'bg-gray-50 text-gray-700 font-semibold border-b-2 border-gray-200',
    bodyRow: 'hover:bg-gray-25 border-b border-gray-100',
    utilitiesContainer: 'bg-gray-50 border-b border-gray-200',
    paginationContainer: 'bg-white border-t border-gray-200'
  },
  customStyle: {
    bodyRow: (baseStyles, state) => ({
      ...baseStyles,
      backgroundColor: state.isSelected ? '#e0f2fe' : baseStyles.backgroundColor,
      borderLeft: state.isSelected ? '4px solid #0ea5e9' : 'none'
    })
  }
};

<CrudHandler api_endpoint="/api/users" {...professionalTheme} />
```

```jsx
const darkTheme = {
  customClass: {
    container: '!bg-gray-900',
    tableWrapper: '!bg-gray-800 !border-gray-700',
    headerCell: '!bg-gray-800 !text-gray-200 !border-gray-700 !font-semibold',
    bodyRow: '!bg-gray-900 hover:!bg-gray-800 !border-gray-700',
    bodyCell: '!text-gray-200 !border-gray-700',
    utilitiesContainer: '!bg-gray-800 !border-gray-700',
    filterButton: '!bg-gray-700 !text-gray-200 hover:!bg-gray-600',
    searchInput: '!bg-gray-700 !text-gray-200 !border-gray-600',
    paginationContainer: '!bg-gray-800 !border-gray-700',
    filterSidebar: '!bg-gray-800 !border-gray-700'
  },
  customStyle: {
    container: (baseStyles) => ({
      backgroundColor: '#111827',
      color: '#e5e7eb',
    }),
    bodyRow: (baseStyles, state) => ({
      backgroundColor: state.isSelected ? '#1e3a8a' : '#111827',
      borderColor: '#374151',
    }),
    bodyCell: (baseStyles) => ({
      color: '#e5e7eb',
      borderColor: '#374151',
      backgroundColor: 'transparent',
    })
  }
};

<CrudHandler api_endpoint="/api/users" {...darkTheme} />
```

```jsx
const dataStyles = {
  customStyle: {
    bodyRow: (baseStyles, state) => {
      const { rowData } = state;
      let backgroundColor = baseStyles.backgroundColor;

      if (rowData?.status === 'active') backgroundColor = '#f0fdf4';
      else if (rowData?.status === 'inactive') backgroundColor = '#fef2f2';
      else if (rowData?.priority === 'high') backgroundColor = '#fef3c7';

      return {
        ...baseStyles,
        backgroundColor: state.isSelected ? '#dbeafe' : backgroundColor
      };
    }
  }
};

<CrudHandler api_endpoint="/api/tasks" {...dataStyles} />
```

```jsx
const backgroundStyles = {
  customClass: {
    container: 'bg-gradient-to-br from-indigo-50 via-white to-cyan-50',
    tableWrapper: 'bg-white/80 backdrop-blur-sm shadow-xl rounded-lg',
    headerCell: 'bg-gradient-to-r from-indigo-600 to-cyan-600 text-white'
  }
};
```

```jsx
const borderlessTheme = {
  customClass: {
    table: 'border-0',
    headerRow: 'border-0',
    headerCell: 'border-0 bg-gray-50 text-gray-700',
    bodyRow: 'border-0 hover:bg-gray-25',
    bodyCell: 'border-0 py-4',
    utilitiesContainer: 'border-0 bg-transparent',
    paginationContainer: 'border-0 bg-transparent'
  },
  customStyle: {
    bodyCell: (baseStyles, state) => ({
      ...baseStyles,
      border: 'none',
      borderBottom: state.rowIndex % 5 === 4 ? '1px solid #f3f4f6' : 'none'
    })
  }
};
```

```jsx
const animatedStyles = {
  customStyle: {
    bodyRow: (baseStyles, state) => ({
      ...baseStyles,
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      transform: state.isSelected ? 'translateX(4px)' : 'translateX(0)',
      boxShadow: state.isSelected
        ? '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
        : 'none'
    }),
    headerCell: (baseStyles, state) => ({
      ...baseStyles,
      transition: 'all 0.2s ease-in-out',
      transform: state.canSort ? 'scale(1)' : 'scale(0.98)'
    })
  }
};
```

```jsx
import { useTheme } from './ThemeProvider';

function ThemedTable() {
  const theme = useTheme();

  const themedStyles = {
    customStyle: {
      headerCell: (baseStyles) => ({
        ...baseStyles,
        backgroundColor: theme.colors.primary,
        color: theme.colors.primaryText
      }),
      bodyRow: (baseStyles, state) => ({
        ...baseStyles,
        backgroundColor: state.isSelected
          ? theme.colors.selected
          : theme.colors.background
      })
    }
  };

  return <CrudHandler api_endpoint="/api/users" {...themedStyles} />;
}
```

```jsx
// Bad - creates new object every render
customStyle={{
  bodyRow: () => ({ backgroundColor: 'red' })
}}

// Good - use customClass for static styles
customClass={{
  bodyRow: 'bg-red-100'
}}
```

```tsx
import type { TableCustomClasses, TableCustomStyles } from '@zango-core/crud/table';

const customClass: TableCustomClasses = {
  headerCell: 'bg-blue-100 text-blue-900',
  bodyRow: 'hover:bg-gray-50'
};

const customStyle: TableCustomStyles = {
  bodyRow: (baseStyles, state) => ({
    ...baseStyles,
    backgroundColor: state.isSelected ? '#fef3c7' : baseStyles.backgroundColor
  })
};

<CrudHandler
  api_endpoint="/api/users"
  customClass={customClass}
  customStyle={customStyle}
/>
```

```tsx
// Row state for bodyRow and bodyCell
interface RowState {
  rowIndex: number;
  isSelected: boolean;
  isHovered: boolean;
  rowData: any;
}

// Header state for headerCell and sortButton
interface HeaderCellState {
  isPinned: boolean;
  canSort: boolean;
  columnId: string;
  pinnedOffset: number;
}

// Action state for action buttons
interface ActionButtonState {
  action: any;
  isFirst: boolean;
  isInDropdown: boolean;
}
```

---

## useTable() (Hook)

**Sections:** Overview | Context Values | Full Signature | Usage Examples

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | array | - | Array of items currently rendered in the body. |
| `totalCount` | number | - | Total items across all pages. |
| `isLoading` | boolean | - | Loading state for list fetches. |
| `currentPage` | number | - | Current page number. |
| `rowsPerPage` | number | - | Items per page. |
| `totalPages` | number | - | Total number of pages. |
| `hasPreviousPage` | boolean | - | Whether a previous page exists. |
| `hasNextPage` | boolean | - | Whether a next page exists. |
| `setCurrentPage` | function | - | Function to change the current page. |
| `setRowsPerPage` | function | - | Function to change page size. |
| `selectedDetailRow` | object | null | - | Currently selected row for detail view. |
| `openDetailDrawer` | function | - | Function to open the detail drawer. |
| `closeDetailDrawer` | function | - | Function to close the detail drawer. |
| `navigateToNextEntry` | function | - | Navigate to next row in detail view. |
| `navigateToPreviousEntry` | function | - | Navigate to previous row in detail view. |
| `searchTerm` | string | - | Current search term. |
| `setSearchTerm` | function | - | Function to update the search term. |
| `activeFilterCount` | number | - | Number of currently active filters. |
| `handleRowClick` | function | - | Function to handle row clicks. |
| `refetch` | function | - | Manually refetch the table data. |
| `api_endpoint` | string | - | The API endpoint being used. |

### Code Examples

```tsx
const {
  // Data & State
  data,                    // array of items rendered in the body
  totalCount,             // total items across pages
  isLoading,              // loading state for list fetches

  // Pagination
  currentPage,            // current page number
  rowsPerPage,           // items per page
  totalPages,            // total number of pages
  hasPreviousPage,       // boolean for pagination
  hasNextPage,           // boolean for pagination
  setCurrentPage,        // function to change page
  setRowsPerPage,       // function to change page size

  // Selection & Navigation
  selectedDetailRow,     // currently selected row for detail view
  openDetailDrawer,      // function to open detail drawer
  closeDetailDrawer,     // function to close detail drawer
  navigateToNextEntry,   // navigate to next row in detail view
  navigateToPreviousEntry, // navigate to previous row in detail view

  // Search & Filters
  searchTerm,            // current search term
  setSearchTerm,         // function to update search
  activeFilterCount,     // number of active filters

  // Actions
  handleRowClick,        // function to handle row clicks
  refetch,              // manually refetch the table

  // API
  api_endpoint,         // the API endpoint being used
} = useTable();
```

```jsx
// A custom component that shows table stats
const TableStatsBar = () => {
  const { totalCount, currentPage, totalPages, isLoading } = useTable();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="flex items-center gap-4 p-3 bg-blue-50 rounded-lg">
      <span className="text-sm font-medium">
        {totalCount} total records
      </span>
      <span className="text-sm text-gray-500">
        Page {currentPage} of {totalPages}
      </span>
    </div>
  );
};

// Use inside CrudHandler
<CrudHandler
  api_endpoint="/api/users"
  customHeader={() => <TableStatsBar />}
/>
```

```jsx
const AdvancedSearch = () => {
  const { searchTerm, setSearchTerm, activeFilterCount, refetch } = useTable();

  return (
    <div className="flex items-center gap-3 p-4">
      <input
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        placeholder="Search..."
        className="flex-1 px-3 py-2 border rounded-lg"
      />
      <span className="text-xs text-gray-500">
        {activeFilterCount} filters active
      </span>
      <button onClick={refetch} className="px-3 py-2 bg-blue-500 text-white rounded-lg">
        Refresh
      </button>
    </div>
  );
};

<CrudHandler
  api_endpoint="/api/users"
  customUtilities={() => <AdvancedSearch />}
/>
```

```jsx
const SimplePagination = () => {
  const {
    currentPage, totalPages, setCurrentPage,
    hasPreviousPage, hasNextPage
  } = useTable();

  return (
    <div className="flex items-center justify-center gap-2 py-4">
      <button
        disabled={!hasPreviousPage}
        onClick={() => setCurrentPage(currentPage - 1)}
        className="px-3 py-1 border rounded disabled:opacity-50"
      >
        Previous
      </button>
      <span className="text-sm">
        {currentPage} / {totalPages}
      </span>
      <button
        disabled={!hasNextPage}
        onClick={() => setCurrentPage(currentPage + 1)}
        className="px-3 py-1 border rounded disabled:opacity-50"
      >
        Next
      </button>
    </div>
  );
};

<CrudHandler
  api_endpoint="/api/users"
  customPagination={() => <SimplePagination />}
/>
```

```jsx
const DetailNavigator = () => {
  const {
    selectedDetailRow,
    navigateToNextEntry,
    navigateToPreviousEntry,
    closeDetailDrawer
  } = useTable();

  if (!selectedDetailRow) return null;

  return (
    <div className="flex items-center gap-2 p-2 border-b">
      <button onClick={navigateToPreviousEntry}>Previous</button>
      <span className="text-sm text-gray-500">
        Viewing: {selectedDetailRow.original?.name}
      </span>
      <button onClick={navigateToNextEntry}>Next</button>
      <button onClick={closeDetailDrawer} className="ml-auto">Close</button>
    </div>
  );
};
```

---

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

## TableBody (Component)

**Sections:** Props | Row Click Behaviors

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `table` | TanstackTable<any> | drawer | TanStack table instance that provides row models, column definitions, and table state. |
| `defaultDetailView` | RowClickAction | RowClickConfig | drawer | Row click behavior configuration. Can be a string ( |
| `selectedRow` | Row | null | - | Currently selected row object. Used to highlight the active row in the table. |
| `drawerOpen` | boolean | - | Whether the detail drawer is currently open. Controls visual state of selected row. |
| `isLoading` | boolean | - | Loading state for initial data fetch. Displays skeleton placeholders when true. |
| `isFetching` | boolean | - | Loading state for subsequent data updates (e.g., pagination, filtering). Shows a subtle loading indicator without replacing content. |

### Code Examples

```jsx
// Default behavior - opens a detail drawer on row click
<TableBody />
```

```jsx
// Navigate to detail page on row click
<TableBody defaultDetailView="navigate" />
```

```jsx
// Navigate with a custom URL template
<TableBody
  defaultDetailView={{
    action: "navigate",
    navigateUrlTemplate: "/users/{object_uuid}/profile"
  }}
/>
```

```jsx
// Custom row click handler
<TableBody
  defaultDetailView={{
    action: "custom",
    customHandler: (row) => console.log(row.original)
  }}
/>
```

---

## TableHeader (Component)

**Sections:** Props | Usage Examples

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | string | ReactNode | true | Header title text or custom React element. Supports plain strings or JSX for rich formatting. |
| `totalCount` | number | true | Total number of items in the dataset. Displayed as a badge next to the title. |
| `showCount` | boolean | true | Show or hide the total count badge next to the title. |
| `showAddButton` | boolean | true | Show or hide the add/create button in the header actions area. |
| `addButtonTitle` | string | ReactNode | true | Custom text or element for the add button. Defaults to a standard  |
| `onAddClick` | function | true | Custom click handler for the add button. Overrides the default behavior of opening the built-in form drawer. |
| `extraActions` | ReactNode | true | Additional action elements rendered alongside the default add button. Useful for export, import, or bulk action buttons. |
| `children` | ReactNode | true | Content rendered between the title area and the action buttons. Commonly used for filters, status tabs, or date range selectors. |
| `api_endpoint` | string | true | API endpoint for the default add form. Used by the built-in form drawer to submit new records. |
| `enableDefaultAddForm` | boolean | true | Enable or disable the built-in form drawer that opens when the add button is clicked. Set to false when using a custom add flow. |

### Code Examples

```jsx
// Uses defaults from table context
<TableHeader />
```

```jsx
<TableHeader
  title="Products"
  totalCount={142}
  showAddButton={true}
  addButtonTitle="New Product"
  extraActions={
    <>
      <button className="btn-secondary">Export CSV</button>
      <button className="btn-secondary">Import</button>
    </>
  }
/>
```

```jsx
<TableHeader
  title={
    <div className="flex items-center gap-2">
      <span className="text-xl font-bold">Orders</span>
      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Live</span>
    </div>
  }
  onAddClick={() => {
    // Custom logic instead of default form
    openCustomOrderModal();
  }}
/>
```

```jsx
<TableHeader title="Inventory" totalCount={856}>
  <StatusFilter
    options={['All', 'In Stock', 'Low Stock', 'Out of Stock']}
    onChange={handleStatusChange}
  />
  <DateRangeFilter
    onRangeChange={handleDateChange}
  />
</TableHeader>
```

```jsx
<TableHeader
  enableDefaultAddForm={false}
  onAddClick={() => router.push('/products/new')}
/>
```

---

## TableUtilities (Component)

**Sections:** Props | Usage Examples

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `searchTerm` | string | Search | Current search input value. Use this for controlled search state. |
| `onSearchChange` | function | Search | Callback invoked when the search input value changes. Receives the new search string as an argument. |
| `onUploadClick` | function | Search | Custom handler for the upload button click. Overrides the default upload behavior. |
| `onDownloadClick` | function | Search | Custom handler for the download button click. Overrides the default download behavior. |
| `searchPlaceholder` | string | Search | Placeholder text for the search input field. |
| `showFiltersButton` | boolean | true | Show or hide the filter toggle button that opens the filters panel. |
| `showSearch` | boolean | true | Show or hide the search input field. |
| `showUpload` | boolean | true | Show or hide the upload button. |
| `showDownload` | boolean | true | Show or hide the download button. |
| `showColumnOptions` | boolean | true | Show or hide the column visibility toggle dropdown. |
| `children` | ReactNode | - | Custom content rendered between the left-side actions (search, filters) and right-side actions (upload, download, columns). Useful for dropdowns, date pickers, or custom filter controls. |

### Code Examples

```jsx
// All default controls visible
<TableUtilities />
```

```jsx
// Hide upload and filters
<TableUtilities
  showUpload={false}
  showFiltersButton={false}
/>
```

```jsx
<TableUtilities
  onUploadClick={() => {
    // Open a custom upload modal
    openUploadModal();
  }}
  onDownloadClick={() => {
    // Trigger a custom export
    exportToExcel(currentFilters);
  }}
/>
```

```jsx
<TableUtilities searchPlaceholder="Search orders...">
  <Select
    options={statusOptions}
    placeholder="Filter by status"
    onChange={handleStatusFilter}
  />
  <DateRangePicker
    onRangeChange={handleDateRange}
  />
</TableUtilities>
```

---

## TablePagination (Component)

**Sections:** Props | Usage Examples

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `showRowsPerPage` | boolean | true | Show or hide the rows-per-page selector dropdown. When hidden, the default page size is used. |
| `rowsPerPageOptions` | number[] | [10 | Array of available page size options displayed in the rows-per-page dropdown. |
| `className` | string | true | Additional CSS classes applied to the pagination container for custom styling. |
| `showPageInfo` | boolean | true | Show or hide the  |

### Code Examples

```jsx
// Default pagination with all controls
<TablePagination />
```

```jsx
<TablePagination
  rowsPerPageOptions={[5, 10, 25, 50]}
  showPageInfo={false}
/>
```

```jsx
<TablePagination showRowsPerPage={false} />
```

---

## TableSearch (Component)

**Sections:** Props | Usage Examples

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `placeholder` | string | Search... | Placeholder text displayed when the search input is empty. |
| `className` | string | - | Additional CSS classes applied to the search input element for custom styling. |
| `containerClassName` | string | - | Additional CSS classes applied to the outer container wrapping the search input and icons. |
| `leftIcon` | ReactNode | - | Custom left icon element. Defaults to a magnifying glass search icon. |
| `rightIcon` | ReactNode | - | Custom right icon element. Useful for adding a clear button or secondary action. |

### Code Examples

```jsx
// Default search with automatic table context sync
<TableSearch />
```

```jsx
<TableSearch
  placeholder="Search by name, email, or ID..."
  className="text-sm font-medium"
/>
```

```jsx
import { Filter, XCircle } from 'lucide-react';

<TableSearch
  placeholder="Filter results..."
  leftIcon={<Filter size={16} className="text-gray-400" />}
  rightIcon={
    <button
      onClick={handleClearSearch}
      className="text-gray-400 hover:text-gray-600"
    >
      <XCircle size={16} />
    </button>
  }
/>
```

---

## TableAddButton (Component)

**Sections:** Props | Usage Examples | Integration Patterns

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `buttonText` | string | ReactNode | primary | Button label text or custom React element. Supports plain strings or JSX for rich content. |
| `onClick` | function | primary | Custom click handler. When provided, the built-in drawer behavior is disabled and your handler is called instead. |
| `variant` | string | primary | Button style variant. Controls the visual appearance (color scheme) of the button. |
| `size` | string | md | Button size. Affects padding, font size, and overall dimensions. |
| `className` | string | false | Additional CSS classes for custom styling on the button element. |
| `showIcon` | boolean | false | Show or hide an icon alongside the button text. |
| `icon` | ReactNode | left | Custom icon element. Only displayed when showIcon is true. |
| `onFormSuccess` | function | md | Callback invoked after the built-in form is submitted successfully. Useful for triggering data refresh or showing notifications. |
| `drawerTitle` | string | md | Custom title for the form drawer. Overrides the default title derived from the table context. |
| `drawerSize` | string | md | Size of the form drawer panel. Supports standard drawer size values. |

### Code Examples

```jsx
// Default add button with built-in form drawer
<TableAddButton />
```

```jsx
<TableAddButton
  buttonText="New Product"
  variant="secondary"
  size="lg"
  showIcon={true}
  className="shadow-md"
/>
```

```jsx
<TableAddButton
  buttonText="Create Order"
  onClick={() => {
    // Navigate to a custom creation page
    router.push('/orders/create');
  }}
/>
```

```jsx
<TableAddButton
  buttonText="Add User"
  drawerTitle="Create New User"
  drawerSize="lg"
  onFormSuccess={() => {
    toast.success('User created successfully!');
    refetchData();
  }}
/>
```

```jsx
<TableAddButton
  buttonText={
    <span className="flex items-center gap-2">
      <PlusCircle size={16} />
      <span>Add Item</span>
    </span>
  }
/>
```

```jsx
<CrudHandler
  api_endpoint="/api/products"
  customHeader={
    <div className="flex items-center justify-between p-4 border-b">
      <div>
        <h1 className="text-lg font-bold">Products</h1>
        <p className="text-sm text-gray-500">Manage your product catalog</p>
      </div>
      <div className="flex items-center gap-3">
        <TableUtilities
          showSearch={true}
          showDownload={true}
          showUpload={false}
          showFiltersButton={false}
          showColumnOptions={false}
        />
        <TableAddButton
          buttonText="New Product"
          showIcon={true}
          variant="primary"
          drawerTitle="Add Product"
          onFormSuccess={() => toast.success('Product added!')}
        />
      </div>
    </div>
  }
/>
```

---

## Render Props (Advanced)

**Sections:** Overview | Actions Column | Status Column | Tags Column

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `actions` | any[] | - | Array of available action objects for the current row, each containing name, label, and configuration. |
| `row` | any | - | The full table row data object. Access fields via row.original for raw API data. |
| `onActionClick` | (action) => void | - | Trigger the action execution pipeline for a given action. Handles confirmations, API calls, and table refresh. |
| `menuOpen` | boolean | - | Current state of the dropdown menu. Use this to control visual state of custom menus. |
| `setMenuOpen` | (open) => void | - | Control the dropdown menu visibility. Call with true to open, false to close. |
| `value` | any | - | The raw status value from the API response. Can be a string, object, or HTML string. |
| `statusValue` | string | - | The resolved status string ready for display. Extracted from value regardless of its original format. |
| `isObject` | boolean | - | True if the raw value is an object (e.g., { status_label:  |
| `isString` | boolean | - | True if the raw value is a plain string. |
| `isHtml` | boolean | - | True if the raw value contains HTML markup that needs special rendering. |
| `tags` | any[] | - | The complete array of all tags assigned to the row. |
| `visibleTags` | any[] | - | Subset of tags displayed inline, sliced to fit within the maxVisible limit. |
| `remainingTags` | any[] | - | Tags that overflow beyond the visible limit. Display these in a popover or tooltip. |
| `hasMoreTags` | boolean | - | True if there are more tags than the maxVisible count allows. Use to conditionally render overflow UI. |
| `maxVisible` | number | - | The maximum number of tags shown inline before overflow. Determined by the table column configuration. |

### Code Examples

```jsx
import { Table } from "@zango-core/crud/table";

<Table
  apiUrl="/api/users"
  tableMetadataObj={metadata}
  renderActions={({ actions, row, onActionClick }) => (
    // Custom actions UI
  )}
  renderStatus={({ statusValue, isObject }) => (
    // Custom status badge
  )}
  renderTags={({ visibleTags, remainingTags, hasMoreTags }) => (
    // Custom tag layout
  )}
/>
```

```jsx
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal } from "lucide-react";

<Table
  apiUrl="/api/orders"
  tableMetadataObj={metadata}
  renderActions={({ actions, row, onActionClick, menuOpen, setMenuOpen }) => {
    const inlineActions = actions.slice(0, 3);
    const overflowActions = actions.slice(3);

    return (
      <div className="flex items-center gap-1">
        {/* Inline action buttons */}
        {inlineActions.map((action) => (
          <Button
            key={action.name}
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onActionClick(action);
            }}
          >
            {action.label}
          </Button>
        ))}

        {/* Overflow dropdown for remaining actions */}
        {overflowActions.length > 0 && (
          <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {overflowActions.map((action) => (
                <DropdownMenuItem
                  key={action.name}
                  onClick={() => onActionClick(action)}
                >
                  {action.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    );
  }}
/>
```

```jsx
<Table
  apiUrl="/api/orders"
  tableMetadataObj={metadata}
  renderStatus={({ value, statusValue, isObject, isString, isHtml }) => {
    // Define color mappings for known statuses
    const statusColors = {
      active: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500' },
      pending: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500' },
      inactive: { bg: 'bg-gray-50', text: 'text-gray-600', dot: 'bg-gray-400' },
      rejected: { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500' },
    };

    const key = statusValue?.toLowerCase() || 'inactive';
    const colors = statusColors[key] || statusColors.inactive;

    // Handle HTML status values
    if (isHtml) {
      return (
        <span
          className="text-sm"
          dangerouslySetInnerHTML={{ __html: value }}
        />
      );
    }

    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`} />
        {statusValue}
      </span>
    );
  }}
/>
```

```jsx
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

<Table
  apiUrl="/api/products"
  tableMetadataObj={metadata}
  renderTags={({ tags, visibleTags, remainingTags, hasMoreTags, maxVisible }) => {
    // Color palette for tags
    const tagColors = [
      'bg-blue-50 text-blue-700 border-blue-200',
      'bg-purple-50 text-purple-700 border-purple-200',
      'bg-teal-50 text-teal-700 border-teal-200',
      'bg-orange-50 text-orange-700 border-orange-200',
      'bg-pink-50 text-pink-700 border-pink-200',
    ];

    return (
      <div className="flex flex-wrap items-center gap-1">
        {/* Visible tags */}
        {visibleTags.map((tag, index) => (
          <span
            key={index}
            className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${tagColors[index % tagColors.length]}`}
          >
            {typeof tag === 'object' ? tag.label || tag.name : tag}
          </span>
        ))}

        {/* Overflow indicator with tooltip */}
        {hasMoreTags && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200 cursor-pointer hover:bg-gray-200">
                  +{remainingTags.length} more
                </span>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <div className="flex flex-wrap gap-1 p-1">
                  {remainingTags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-0.5 rounded-md text-xs bg-white border"
                    >
                      {typeof tag === 'object' ? tag.label || tag.name : tag}
                    </span>
                  ))}
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    );
  }}
/>
```

---

## Hooks Reference (Hooks)

**Sections:** useTable() | useTableData() | useTableSearch() | useTableFilters() | useTablePagination() | useTableSelection() | useTableColumns() | useTableActions() | useTableRowActions() | useDetailView() | useDetailViewContext() | useWorkflow()

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | array | - | Flat array of row objects for the current page. |
| `totalCount` | number | - | Total number of rows across all pages. |
| `isLoading` | boolean | - | True while data is being fetched. |
| `currentPage` | number | - | Zero-based index of the current page. |
| `rowsPerPage` | number | - | Number of rows displayed per page. |
| `totalPages` | number | - | Total number of pages. |
| `hasPreviousPage` | boolean | - | Whether a previous page exists. |
| `hasNextPage` | boolean | - | Whether a next page exists. |
| `setCurrentPage` | (page: number) => void | - | Navigate to a specific page. |
| `setRowsPerPage` | (size: number) => void | - | Change the page size. |
| `selectedDetailRow` | object | null | - | The row currently open in the detail drawer. |
| `openDetailDrawer` | (row) => void | - | Open the detail drawer for a row. |
| `closeDetailDrawer` | () => void | - | Close the detail drawer. |
| `navigateToNextEntry` | () => void | - | Move the detail drawer to the next row. |
| `navigateToPreviousEntry` | () => void | - | Move the detail drawer to the previous row. |
| `searchTerm` | string | - | Current search query. |
| `setSearchTerm` | (term: string) => void | - | Update the search query. |
| `activeFilterCount` | number | - | Number of currently active filters. |
| `handleRowClick` | (row) => void | - | Default row-click handler that opens the detail drawer. |
| `refetch` | () => void | - | Re-fetch data from the API. |
| `api_endpoint` | string | - | The resolved API endpoint URL. |
| `apiUrl` | string | - | API endpoint to fetch rows from. |
| `columns` | array | - | Column definitions. If omitted, derived from tableMetadata. |
| `tableMetadata` | object | - | Pre-fetched metadata object. If omitted, fetched from apiUrl. |
| `flatData` | array | - | Flat array of row objects for the current page. |
| `totalDBRowCount` | number | - | Total row count reported by the server. |
| `totalPages` | number | - | Computed total pages based on row count and page size. |
| `isLoading` | boolean | - | True during the initial data load. |
| `isFetching` | boolean | - | True during any fetch, including background refetches. |
| `error` | Error | null | - | Error object if the fetch failed. |
| `searchTerm` | string | - | Current search term sent to the server. |
| `setSearchTerm` | (term: string) => void | - | Update the search term. |
| `filterObj` | object | - | Current filter state sent to the server. |
| `setFilterObj` | (filters: object) => void | - | Replace all active filters. |
| `currentPage` | number | - | Zero-based current page index. |
| `setCurrentPage` | (page: number) => void | - | Navigate to a page. |
| `rowsPerPage` | number | - | Rows per page. |
| `setRowsPerPage` | (size: number) => void | - | Change page size. |
| `sorting` | array | - | Current sorting state array. |
| `setSorting` | (sorting: array) => void | - | Update sorting. |
| `tableMetadata` | object | - | Resolved table metadata (fetched or passed in). |
| `columns` | array | - | Effective column definitions used by the table. |
| `refetch` | () => void | - | Re-fetch the current page of data. |
| `searchTerm` | string | - | The raw search input value (updates on every keystroke). |
| `setSearchTerm` | (term: string) => void | - | Update the search input. |
| `debouncedSearchTerm` | string | - | The debounced value actually sent to the API. |
| `filterObj` | object | - | Current filter key-value map sent to the API. |
| `setFilterObj` | (filters: object) => void | - | Replace the entire filter state. |
| `activeFilterCount` | number | - | Number of non-empty filter entries. |
| `clearFilters` | () => void | - | Remove all active filters. |
| `hasActiveFilters` | boolean | - | True when at least one filter is active. |
| `currentPage` | number | - | Zero-based index of the current page. |
| `totalPages` | number | - | Total number of pages. |
| `rowsPerPage` | number | - | Rows displayed per page. |
| `setCurrentPage` | (page: number) => void | - | Jump to a specific page. |
| `setRowsPerPage` | (size: number) => void | - | Change the page size (resets to page 0). |
| `hasPreviousPage` | boolean | - | Whether navigating backward is possible. |
| `hasNextPage` | boolean | - | Whether navigating forward is possible. |
| `goToFirstPage` | () => void | - | Navigate to the first page. |
| `goToLastPage` | () => void | - | Navigate to the last page. |
| `selectedRows` | array | - | Array of currently selected row objects or IDs. |
| `setSelectedRows` | (rows: array) => void | - | Directly set the selected rows. |
| `isAllSelected` | boolean | - | True when every visible row is selected. |
| `toggleSelectAll` | () => void | - | Select all visible rows, or deselect all if already selected. |
| `toggleSelectRow` | (row) => void | - | Toggle selection for a single row. |
| `clearSelection` | () => void | - | Deselect all rows. |
| `visibleColumns` | array | - | Array of currently visible column definitions. |
| `hiddenColumns` | array | - | Array of currently hidden column definitions. |
| `toggleColumnVisibility` | (columnId: string) => void | - | Toggle a column between visible and hidden. |
| `showColumn` | (columnId: string) => void | - | Make a specific column visible. |
| `hideColumn` | (columnId: string) => void | - | Hide a specific column. |
| `showAllColumns` | () => void | - | Make all columns visible. |
| `hideAllColumns` | () => void | - | Hide all columns. |
| `isColumnVisible` | (columnId: string) => boolean | - | Check if a column is currently visible. |
| `moveColumn` | (columnId: string, newIndex: number) => void | - | Reorder a column to a new position. |
| `pinColumnLeft` | (columnId: string) => void | - | Pin a column to the left side of the table. |
| `pinColumnRight` | (columnId: string) => void | - | Pin a column to the right side of the table. |
| `refetch` | () => void | - | Re-fetch the table data from the server. |
| `exportTable` | () => void | - | Trigger an export of the current table data. |
| `handleRowClick` | (row) => void | - | Default handler that opens the detail drawer for the clicked row. |
| `selectedDetailRow` | object | null | - | The row currently displayed in the detail drawer. |
| `openDetailDrawer` | (row) => void | - | Programmatically open the detail drawer for a row. |
| `closeDetailDrawer` | () => void | - | Close the detail drawer. |
| `navigateToNextEntry` | () => void | - | Move the detail drawer to the next row in the list. |
| `navigateToPreviousEntry` | () => void | - | Move the detail drawer to the previous row in the list. |
| `apiUrl` | string | - | API endpoint for the detail record. Automatically resolved from context if inside a DetailViewProvider. |
| `data` | object | - | The fetched detail data for the current object. |
| `loading` | boolean | - | True while detail data is being fetched. |
| `error` | string | null | - | Error message if the detail fetch failed. |
| `refresh` | () => Promise<void> | - | Re-fetch the detail data from the API. |
| `objectUuid` | string | - | UUID of the current detail object. |
| `workflowDetails` | object | - | Workflow data for the object (current_status, current_status_meta, next_transitions, tag_details). |
| `rowActions` | array | - | Available row-level actions for the current object. |
| `data` | object | - | Detail data from the shared context. |
| `loading` | boolean | - | True while the shared detail fetch is in progress. |
| `error` | string | null | - | Error from the shared detail fetch. |
| `refresh` | () => Promise<void> | - | Re-fetch detail data for the entire context. |
| `objectUuid` | string | - | UUID of the current detail object. |
| `workflowDetails` | object | - | Workflow data from the shared context. |
| `rowActions` | array | - | Row-level actions from the shared context. |
| `apiUrl` | string | - | API endpoint for fetching workflow data. |
| `beforeTransition` | (transition) => Promise<void> | - | Async callback invoked before executing a transition. |
| `afterTransition` | (transition, success) => Promise<void> | - | Async callback invoked after a transition completes. |
| `workflowDetails` | object | - | Full workflow data: current_status, current_status_meta, next_transitions, and tag_details. |
| `loading` | boolean | - | True while workflow data is being fetched. |
| `error` | string | null | - | Error message if the workflow fetch or operation failed. |
| `refreshWorkflow` | () => Promise<void> | - | Re-fetch workflow data from the API. |
| `executeTransition` | (transition, formData?) => Promise<boolean> | - | Execute a status transition. Optionally pass form data. Returns success boolean. |
| `toggleTag` | (tag) => Promise<boolean> | - | Toggle a tag on or off. Returns success boolean. |

### Code Examples

```jsx
import { useTable } from "@zango-core/crud/table";

function OrdersPage() {
  const { data, isLoading, totalCount, refetch } = useTable();
  if (isLoading) return <p>Loading…</p>;
  return <p>{totalCount} orders loaded. <button onClick={refetch}>Refresh</button></p>;
}
```

```jsx
import { useTableData } from "@zango-core/crud/table";

function ProductList() {
  const { flatData, isLoading, totalDBRowCount, refetch } = useTableData({
    apiUrl: "/api/products/",
  });
  if (isLoading) return <p>Loading…</p>;
  return <p>{totalDBRowCount} products found. <button onClick={refetch}>Refresh</button></p>;
}
```

```jsx
import { useTableSearch } from "@zango-core/crud/table";

function SearchBar() {
  const { searchTerm, setSearchTerm, debouncedSearchTerm } = useTableSearch();
  return (
    <input value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
      placeholder="Search…" />
  );
}
```

```jsx
import { useTableFilters } from "@zango-core/crud/table";

function FilterBar() {
  const { filterObj, setFilterObj, activeFilterCount, clearFilters } = useTableFilters();
  return (
    <div>
      <span>{activeFilterCount} filters active</span>
      <button onClick={clearFilters}>Clear all</button>
    </div>
  );
}
```

```jsx
import { useTablePagination } from "@zango-core/crud/table";

function Pager() {
  const { currentPage, totalPages, hasPreviousPage, hasNextPage, setCurrentPage } = useTablePagination();
  return (
    <div>
      <button disabled={!hasPreviousPage} onClick={() => setCurrentPage(currentPage - 1)}>Prev</button>
      <span>Page {currentPage + 1} of {totalPages}</span>
      <button disabled={!hasNextPage} onClick={() => setCurrentPage(currentPage + 1)}>Next</button>
    </div>
  );
}
```

```jsx
import { useTableSelection } from "@zango-core/crud/table";

function BulkActions() {
  const { selectedRows, toggleSelectAll, isAllSelected, clearSelection } = useTableSelection();
  return (
    <div>
      <button onClick={toggleSelectAll}>{isAllSelected ? "Deselect All" : "Select All"}</button>
      <span>{selectedRows.length} selected</span>
      <button onClick={clearSelection}>Clear</button>
    </div>
  );
}
```

```jsx
import { useTableColumns } from "@zango-core/crud/table";

function ColumnPicker() {
  const { visibleColumns, hiddenColumns, toggleColumnVisibility } = useTableColumns();
  return (
    <ul>
      {[...visibleColumns, ...hiddenColumns].map((col) => (
        <li key={col.id}>
          <label>
            <input type="checkbox" checked={visibleColumns.includes(col)}
              onChange={() => toggleColumnVisibility(col.id)} /> {col.header}
          </label>
        </li>
      ))}
    </ul>
  );
}
```

```jsx
import { useTableActions } from "@zango-core/crud/table";

function Toolbar() {
  const { refetch, exportTable } = useTableActions();
  return (
    <div>
      <button onClick={refetch}>Refresh</button>
      <button onClick={exportTable}>Export CSV</button>
    </div>
  );
}
```

```jsx
import { useTableRowActions } from "@zango-core/crud/table";

function DetailDrawerNav() {
  const { selectedDetailRow, closeDetailDrawer, navigateToNextEntry, navigateToPreviousEntry } = useTableRowActions();
  if (!selectedDetailRow) return null;
  return (
    <div>
      <button onClick={navigateToPreviousEntry}>Prev</button>
      <button onClick={navigateToNextEntry}>Next</button>
      <button onClick={closeDetailDrawer}>Close</button>
    </div>
  );
}
```

```jsx
import { useDetailView } from "@zango-core/crud/table";

function UserProfile() {
  const { data, loading, error, refresh, objectUuid } = useDetailView({
    apiUrl: "/api/users/?object_uuid=abc-123",
  });
  if (loading) return <p>Loading…</p>;
  if (error) return <p>Error: {error}</p>;
  return <p>{data.name} ({objectUuid}) <button onClick={refresh}>Refresh</button></p>;
}
```

```jsx
import { useDetailViewContext } from "@zango-core/crud/table";

function StatusBadge() {
  const { workflowDetails, loading } = useDetailViewContext();
  if (loading || !workflowDetails) return null;
  return <span className="badge">{workflowDetails.current_status_meta?.status_label}</span>;
}
```

```jsx
import { useWorkflow } from "@zango-core/crud/table";

function ApproveButton({ objectUuid }) {
  const { workflowDetails, executeTransition, loading } = useWorkflow({
    apiUrl: `/api/orders/?object_uuid=${objectUuid}`,
  });
  if (loading || !workflowDetails) return null;
  const approveTransition = workflowDetails.next_transitions.find((t) => t.name === "approve");
  if (!approveTransition) return null;
  return <button onClick={() => executeTransition(approveTransition)}>Approve</button>;
}
```

---
