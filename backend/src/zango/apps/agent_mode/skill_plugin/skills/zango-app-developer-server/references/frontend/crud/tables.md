# Zango CRUD — Tables

> Split from the generated CRUD reference. Shared basics (imports, API
> response formats, column types, CrudHandler) are in [core.md](core.md).

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
