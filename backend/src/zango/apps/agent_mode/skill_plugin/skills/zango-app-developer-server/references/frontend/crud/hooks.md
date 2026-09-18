# Zango CRUD — Hooks Reference

> Split from the generated CRUD reference. Shared basics are in [core.md](core.md).

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
