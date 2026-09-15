# CRUD Tables Reference

Tables define how data is displayed in list views with search, sort, filtering, and action capabilities.

## Essential Imports

```python
from django.db.models import Q
from ...packages.crud.table.base import ModelTable
from ...packages.crud.table.column import ModelCol, StringCol, StatusCol, TagsCol, ActionsCol
from .models import MyModel
from .forms import MyModelForm
```

---

## Basic Table Structure

```python
class MyModelTable(ModelTable):
    # Define columns
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    name = ModelCol(display_as="Name", searchable=True, sortable=True)
    status = StringCol(display_as="Status", searchable=True, sortable=False)

    # Row actions
    row_actions = [
        {
            "name": "Edit",
            "key": "edit",
            "description": "Edit record",
            "type": "form",
            "form": MyModelForm
        }
    ]

    class Meta:
        model = MyModel
        fields = ['id', 'name', 'status']
        row_selector = {}
```

---

## Column Types

### ModelCol - Direct Model Field Display

Maps directly to a Django model field.

```python
id = ModelCol(
    display_as="ID",                    # Column header text
    searchable=True,                     # Enable search
    sortable=True,                       # Enable sorting
    exportable=True,                     # Include in exports (default: True)
    include_in_detail=True,              # Show in detail view (default: True)
    user_roles=[],                       # Restrict to specific roles
    related_object_attribute=None,       # For FK fields: field name on the related model to display (e.g., 'name' shows fk_field.name)
    choices=None                         # Override model field choices
)
```

**Parameters**:
- `display_as` - Column header label
- `searchable` - Enable/disable search for this column
- `sortable` - Enable/disable sorting
- `exportable` - Include in CSV/Excel exports
- `include_in_detail` - Show in detail view
- `user_roles` - List of role names that can see this column
- `related_object_attribute` - For ForeignKey fields: the field name on the **related model** to display (e.g., `related_object_attribute='name'` renders `instance.fk_field.name`)
- `choices` - Override field choices

**Example**:
```python
class PatientTable(ModelTable):
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    name = ModelCol(display_as="Patient Name", searchable=True, sortable=True)
    email = ModelCol(display_as="Email", searchable=True, sortable=False)
    created_at = ModelCol(display_as="Created", searchable=False, sortable=True)
```

### StringCol - Custom/Computed Values

For values not directly mapped to model fields or requiring custom display.

```python
full_name = StringCol(
    display_as="Full Name",
    searchable=False,                    # Usually not searchable
    sortable=False,                      # Usually not sortable
    exportable=True,
    include_in_detail=True,
    user_roles=[],
    choices=[]                           # Optional choices for filtering
)
```

**Use Cases**:
- Computed values (combining fields)
- Custom formatted output
- Badge/status displays
- Values requiring `_getval` method

**Example**:
```python
class PatientTable(ModelTable):
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    name = ModelCol(display_as="Name", searchable=True, sortable=True)
    is_active = StringCol(display_as="Status", searchable=True, sortable=False)

    def is_active_getval(self, obj):
        """Custom display for is_active column"""
        if obj.is_active:
            return '<span class="badge badge-success">Active</span>'
        return '<span class="badge badge-secondary">Inactive</span>'
```

### StatusCol - Workflow Status Display

Automatically displays workflow status with colors. Inherits from `StringCol`.

```python
from ...packages.crud.table.column import StatusCol

status = StatusCol(display_as="Status", searchable=True)
```

**Features**:
- Automatically pulls from workflow's `Meta.statuses`
- Displays status badge with configured color
- Auto-generates `_getval` method
- Auto-generates `_Q_obj` for search
- Auto-generates `_get_choices` for filtering

**Requires**: Workflow class defined in CRUD view

**Example**:
```python
from ...packages.crud.table.column import StatusCol

class PatientTable(ModelTable):
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    name = ModelCol(display_as="Name", searchable=True, sortable=True)
    status = StatusCol(display_as="Status", searchable=True)

    class Meta:
        model = Patient
        fields = ['id', 'name', 'status']
        row_selector = {}
```

### TagsCol - Workflow Tags Display

Displays workflow tags as comma-separated list. Inherits from `StringCol`.

```python
from ...packages.crud.table.column import TagsCol

tags = TagsCol(display_as="Tags", searchable=True)
```

**Features**:
- Automatically pulls from workflow's `Meta.tags`
- Displays tags as comma-separated string
- Auto-generates `_getval` method
- Auto-generates `_Q_obj` for search
- Auto-generates `_get_choices` for filtering

**Requires**: Workflow class with tags defined in Meta

**Example**:
```python
from ...packages.crud.table.column import TagsCol

class OrderTable(ModelTable):
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    order_number = ModelCol(display_as="Order #", searchable=True, sortable=True)
    tags = TagsCol(display_as="Tags", searchable=True)
```

### ActionsCol - Row Actions Column

Special column that displays row actions as buttons/dropdown.

```python
from ...packages.crud.table.column import ActionsCol

actions = ActionsCol(display_as="Actions")
```

**Features**:
- Non-searchable, non-sortable by default
- Excluded from exports (`exportable=False`)
- Not shown in detail view (`include_in_detail=False`)
- Auto-generates `_getval` returning row actions for each row

**Example**:
```python
from ...packages.crud.table.column import ActionsCol

class PatientTable(ModelTable):
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    name = ModelCol(display_as="Name", searchable=True, sortable=True)
    actions = ActionsCol(display_as="Actions")
```

### WorkflowTransitionsCol - Available Transitions Column

Displays available workflow transitions for each row.

```python
from ...packages.crud.table.column import WorkflowTransitionsCol

transitions = WorkflowTransitionsCol(display_as="Available Actions")
```

**Features**:
- Shows workflow transitions available for current status
- Non-searchable, non-sortable
- Excluded from exports and detail view
- Auto-generates `_getval` returning transitions list

---

## Custom Column Display

Override `<column_name>_getval` to customize how a column is displayed.

**IMPORTANT**: Use `self.user_role` (NOT `get_current_role()`) to access the current user's role. This ensures compatibility with export tasks that run in background without request context.

### Basic Custom Display

```python
def name_getval(self, obj):
    """Display name in bold"""
    return f"<strong>{obj.name}</strong>"

def email_getval(self, obj):
    """Display as mailto link"""
    if obj.email:
        return f'<a href="mailto:{obj.email}">{obj.email}</a>'
    return "-"
```

### Badge Display

```python
def is_active_getval(self, obj):
    """Display status as badge"""
    if obj.is_active:
        return '<span class="badge badge-success">Active</span>'
    return '<span class="badge badge-secondary">Inactive</span>'

def priority_getval(self, obj):
    """Display priority with color"""
    colors = {'high': 'danger', 'medium': 'warning', 'low': 'info'}
    color = colors.get(obj.priority, 'secondary')
    return f'<span class="badge badge-{color}">{obj.priority.title()}</span>'
```

### Related Field Display

```python
def country_getval(self, obj):
    """Display related field"""
    return obj.country.name if obj.country else "-"

def doctor_getval(self, obj):
    """Display FK with custom format"""
    if obj.doctor:
        return f"{obj.doctor.name} - {obj.doctor.specialty}"
    return "Not Assigned"
```

### Computed Values

```python
def full_name_getval(self, obj):
    """Combine first and last name"""
    return f"{obj.first_name} {obj.last_name}"

def days_until_expiry_getval(self, obj):
    """Calculate days remaining"""
    if obj.expiry_date:
        delta = obj.expiry_date - datetime.now().date()
        return f"{delta.days} days"
    return "No expiry"
```

### Role-Based Display

```python
def sensitive_data_getval(self, obj):
    """Show sensitive data only to admins - USE self.user_role"""
    if self.user_role and self.user_role.name == 'Admin':
        return obj.sensitive_field
    return "***REDACTED***"

def department_getval(self, obj):
    """Display department with role-based formatting"""
    if self.user_role and self.user_role.name in ['Admin', 'Manager']:
        return f"{obj.department.name} ({obj.department.code})"
    return obj.department.name
```

---

## Custom Column Search

Override `<column_name>_Q_obj` to customize search behavior. Must return a Django Q object.

### Numeric Search

```python
def id_Q_obj(self, search_term):
    """Search by ID - numeric only"""
    if search_term.isdigit():
        return Q(id=int(search_term))
    return Q()  # Return empty Q if not numeric
```

### Case-Insensitive Text Search

```python
def name_Q_obj(self, search_term):
    """Case-insensitive name search"""
    return Q(name__icontains=search_term)

def email_Q_obj(self, search_term):
    """Search email"""
    return Q(email__icontains=search_term)
```

### Status/Boolean Search

```python
def is_active_Q_obj(self, search_term):
    """Search by status text"""
    search_lower = search_term.lower()
    if search_lower in ['active', 'yes', 'true']:
        return Q(is_active=True)
    elif search_lower in ['inactive', 'no', 'false']:
        return Q(is_active=False)
    return Q()
```

### Related Field Search

```python
def country_Q_obj(self, search_term):
    """Search by related field - ID or name"""
    if search_term.isdigit():
        return Q(country__id=search_term)
    else:
        return Q(country__name__icontains=search_term)

def doctor_Q_obj(self, search_term):
    """Search doctor by name or specialty"""
    return Q(doctor__name__icontains=search_term) | Q(doctor__specialty__icontains=search_term)
```

### Choice Field Search

```python
def category_Q_obj(self, search_term):
    """Search by category"""
    return Q(category__icontains=search_term)
```

---

## Row Actions

Row actions appear as buttons/links for each row in the table.

### Action Types

**1. Form Action** - Opens a form:

```python
{
    "name": "Edit",
    "key": "edit",
    "description": "Edit this record",
    "type": "form",
    "form": MyModelForm
}
```

**2. Simple Action** - Executes immediately with confirmation:

```python
{
    "name": "Activate",
    "key": "activate",
    "description": "Activate this record",
    "type": "simple",
    "confirmation_message": "Are you sure you want to activate this record?"
}
```

### Row Action Attributes

**Common Attributes**:

| Attribute | Required | Type | Description |
|-----------|----------|------|-------------|
| `name` | Yes | str | Action button label |
| `key` | Yes | str | Unique action identifier |
| `description` | No | str | Tooltip/help text |
| `type` | Yes | str | `"form"` or `"simple"` |
| `user_roles` | No | list | List of role names allowed to see this action |
| `form` | Conditional | class | Form class (required if `type="form"`) |
| `confirmation_message` | No | str | Confirmation dialog message (for simple actions) |

**Restricting Actions by User Role**:

Use the `user_roles` key to control which user roles can see and use specific actions:

```python
{
    "name": "Delete",
    "key": "delete",
    "description": "Delete this record",
    "type": "simple",
    "confirmation_message": "Are you sure?",
    "user_roles": ["Admin", "Manager"]  # Only Admin and Manager can delete
}
```

**Example with Multiple Role-Restricted Actions**:

```python
row_actions = [
    {
        "name": "View",
        "key": "view",
        "type": "form",
        "form": ViewForm,
        # No user_roles - available to all roles
    },
    {
        "name": "Edit",
        "key": "edit",
        "type": "form",
        "form": EditForm,
        "user_roles": ["Admin", "Editor"]  # Only Admin and Editor can edit
    },
    {
        "name": "Approve",
        "key": "approve",
        "type": "simple",
        "confirmation_message": "Approve this record?",
        "user_roles": ["Admin"]  # Only Admin can approve
    },
    {
        "name": "Delete",
        "key": "delete",
        "type": "simple",
        "confirmation_message": "Delete permanently?",
        "user_roles": ["Admin"]  # Only Admin can delete
    }
]
```

**Note:** If `user_roles` is not specified, the action is available to all users who can access the table.

### Complete Row Actions Example

```python
row_actions = [
    {
        "name": "Edit",
        "key": "edit",
        "description": "Edit service type",
        "type": "form",
        "form": ServiceTypeForm
    },
    {
        "name": "Activate",
        "key": "activate",
        "description": "Activate this service type",
        "type": "simple",
        "confirmation_message": "Are you sure?"
    },
    {
        "name": "Deactivate",
        "key": "deactivate",
        "description": "Deactivate this service type",
        "type": "simple",
        "confirmation_message": "Are you sure?"
    },
    {
        "name": "Delete",
        "key": "delete",
        "description": "Delete this record",
        "type": "simple",
        "confirmation_message": "This action cannot be undone. Are you sure?"
    }
]
```

---

## Processing Row Actions

Implement `process_row_action_<action_key>` to handle simple actions.

**Method Signature**:
```python
def process_row_action_<action_key>(self, request, obj):
    # Perform action logic
    # Return (success: bool, response: dict)
    return success, response
```

### Basic Action Processing

```python
def process_row_action_activate(self, request, obj):
    """Handle activate action"""
    obj.is_active = True
    obj.save()
    return True, {"message": "Activated successfully"}

def process_row_action_deactivate(self, request, obj):
    """Handle deactivate action"""
    obj.is_active = False
    obj.save()
    return True, {"message": "Deactivated successfully"}
```

### Action with Validation

```python
def process_row_action_deactivate(self, request, obj):
    """Deactivate with dependency check"""
    # Check if can be deactivated
    if obj.has_active_dependencies():
        return False, {
            "message": "Cannot deactivate - has active dependencies"
        }

    obj.is_active = False
    obj.save()
    return True, {
        "message": "Deactivated successfully. Existing mappings preserved but cannot be used for new records."
    }
```

### Delete Action

```python
def process_row_action_delete(self, request, obj):
    """Handle delete with error handling"""
    try:
        obj_name = obj.name
        obj.delete()
        return True, {"message": f"{obj_name} deleted successfully"}
    except Exception as e:
        return False, {"message": f"Error deleting: {str(e)}"}
```

---

## Conditional Row Actions

Use `get_row_actions` to show different actions based on object state.

```python
def get_row_actions(self, request, obj):
    """Show different actions based on object state"""
    row_actions_list = super().get_row_actions(request, obj)
    new_actions = []

    for action in row_actions_list:
        if action['key'] == "activate":
            # Only show activate for inactive records
            if not obj.is_active:
                action['confirmation_message'] = f"Are you sure you want to activate {obj.name}?"
                new_actions.append(action)

        elif action['key'] == "deactivate":
            # Only show deactivate for active records
            if obj.is_active:
                action['confirmation_message'] = f"Are you sure you want to deactivate {obj.name}?"
                new_actions.append(action)

        elif action['key'] == "delete":
            # Only show delete for inactive records
            if not obj.is_active:
                new_actions.append(action)

        else:
            # Show all other actions
            new_actions.append(action)

    return new_actions
```

---

## Permission-Based Actions

Use `can_perform_row_action_<action_key>` to control access to specific actions.

**IMPORTANT**: Use `self.user_role` (NOT `get_current_role()`) to access the current user's role. This is critical for export tasks that run in background without request context.

```python
def can_perform_row_action_edit(self, request, obj):
    """Check if user can edit - USE self.user_role"""
    if self.user_role:
        allowed_roles = ['Admin', 'Manager', 'Editor']
        return self.user_role.name in allowed_roles
    return False

def can_perform_row_action_delete(self, request, obj):
    """Only admins can delete - USE self.user_role"""
    return self.user_role and self.user_role.name == 'Admin'

def can_perform_row_action_activate(self, request, obj):
    """Check activation permission - USE self.user_role"""
    if self.user_role:
        allowed_roles = ['Admin', 'Manager']
        return self.user_role.name in allowed_roles
    return False
```

**Why `self.user_role` instead of `get_current_role()`?**

- `self.user_role` is set in the table's `__init__` method and persists
- Export operations run as background Celery tasks without request context
- `get_current_role()` fails in task context (no active request)
- `self.user_role` works in both web requests AND background exports

---

## Custom Table Queryset

Override `get_table_data_queryset()` to customize the data shown in the table.

**Method Signature**:
```python
def get_table_data_queryset(self):
    """
    Get the queryset for the table data.

    Returns:
        QuerySet: The queryset containing objects from the model.
    """
    objects = self.model.objects.all()
    return objects
```

### Filter by Query Parameters

```python
def get_table_data_queryset(self):
    """Filter based on URL parameters"""
    queryset = super().get_table_data_queryset()

    # Filter by program_uuid if provided
    program_uuid = self.crud_view_instance.request.GET.get('program_uuid')
    if program_uuid:
        program_uuid = program_uuid.replace('/', '')
        queryset = queryset.filter(
            Q(is_other=False) | Q(is_other=True, program_uuid=program_uuid)
        )
    else:
        queryset = queryset.filter(is_other=False)

    # Show only active if documentUuid present
    if self.crud_view_instance.request.GET.get('documentUuid'):
        queryset = queryset.filter(is_active=True)

    return queryset
```

### Filter by User Role

```python
def get_table_data_queryset(self):
    """Show different data based on user role - USE self.user_role"""
    queryset = super().get_table_data_queryset()

    if self.user_role and self.user_role.name == 'Manager':
        # Managers see only their department
        queryset = queryset.filter(department=self.user_role.department)
    elif self.user_role and self.user_role.name == 'User':
        # Users see only their own records
        queryset = queryset.filter(created_by=self.request.user)

    return queryset
```

### Complex Filtering

```python
def get_table_data_queryset(self):
    """Advanced filtering logic"""
    queryset = super().get_table_data_queryset()

    # Apply filters from request
    status_filter = self.request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Exclude deleted
    queryset = queryset.exclude(is_deleted=True)

    # Prefetch related for performance
    queryset = queryset.select_related('country', 'created_by')

    return queryset
```

---

## Dynamic Choices for Filtering

Set choices dynamically in `__init__` for filter dropdowns.

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    # Set choices for is_active filter
    self.is_active.choices = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ]

    # Set choices for category filter
    self.category.choices = [
        ('Type A', 'Type A'),
        ('Type B', 'Type B'),
        ('Type C', 'Type C')
    ]
```

---

## Complete Table Example

```python
from django.db.models import Q
from ...packages.crud.table.base import ModelTable
from ...packages.crud.table.column import ModelCol, StringCol, StatusCol
from .models import ServiceType
from .forms import ServiceTypeForm

class ServiceTypeTable(ModelTable):
    # Define columns
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    name = ModelCol(display_as="Name", searchable=True, sortable=True)
    category = ModelCol(display_as="Category", searchable=True, sortable=True)
    is_active = StringCol(display_as="Status", searchable=True, sortable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set choices for status filter
        self.is_active.choices = [('Active', 'Active'), ('Inactive', 'Inactive')]

    # Custom queryset
    def get_table_data_queryset(self):
        queryset = super().get_table_data_queryset()

        # Filter by program if provided
        if self.crud_view_instance.request.GET.get('program_uuid'):
            program_uuid = self.crud_view_instance.request.GET.get('program_uuid').replace('/', '')
            queryset = queryset.filter(
                Q(is_other=False) | Q(is_other=True, program_uuid=program_uuid)
            )
        else:
            queryset = queryset.filter(is_other=False)

        return queryset

    # Custom display
    def is_active_getval(self, obj):
        """Display status badge"""
        if obj.is_active:
            return '<span class="badge badge-success">Active</span>'
        return '<span class="badge badge-secondary">Inactive</span>'

    # Custom search
    def is_active_Q_obj(self, search_term):
        """Search by status"""
        if search_term.lower() == 'active':
            return Q(is_active=True)
        elif search_term.lower() == 'inactive':
            return Q(is_active=False)
        return Q()

    def id_Q_obj(self, search_term):
        """Search by ID - numeric only"""
        if search_term.isdigit():
            return Q(id=int(search_term))
        return Q()

    def name_Q_obj(self, search_term):
        """Search by name"""
        return Q(name__icontains=search_term)

    def category_Q_obj(self, search_term):
        """Search by category"""
        return Q(category__icontains=search_term)

    # Row actions
    row_actions = [
        {
            "name": "Edit",
            "key": "edit",
            "description": "Edit service type",
            "type": "form",
            "form": ServiceTypeForm
        },
        {
            "name": "Activate",
            "key": "activate",
            "description": "Activate this service type",
            "type": "simple",
            "confirmation_message": "Are you sure?"
        },
        {
            "name": "Deactivate",
            "key": "deactivate",
            "description": "Deactivate this service type",
            "type": "simple",
            "confirmation_message": "Are you sure?"
        }
    ]

    # Conditional actions
    def get_row_actions(self, request, obj):
        """Show activate/deactivate based on current state"""
        row_actions_list = super().get_row_actions(request, obj)
        new_actions = []

        for action in row_actions_list:
            if action['key'] == "activate" and not obj.is_active:
                action['confirmation_message'] = f"Are you sure you want to activate {obj.name}?"
                new_actions.append(action)
            elif action['key'] == "deactivate" and obj.is_active:
                action['confirmation_message'] = f"Are you sure you want to deactivate {obj.name}?"
                new_actions.append(action)
            elif action['key'] == "edit":
                new_actions.append(action)

        return new_actions

    # Action processing
    def process_row_action_activate(self, request, obj):
        obj.is_active = True
        obj.save()
        return True, {"message": "Activated successfully"}

    def process_row_action_deactivate(self, request, obj):
        obj.is_active = False
        obj.save()
        return True, {
            "message": "Deactivated successfully. It is still mapped to existing programs, but can't be mapped with new programs from now on."
        }

    # Permissions - USE self.user_role
    def can_perform_row_action_edit(self, request, obj):
        """Check if user can edit - USE self.user_role"""
        if self.user_role:
            allowed_roles = ['Admin', 'Manager']
            return self.user_role.name in allowed_roles
        return False

    def can_perform_row_action_activate(self, request, obj):
        """Check if user can activate - USE self.user_role"""
        if self.user_role:
            return self.user_role.name in ['Admin', 'Manager']
        return False

    def can_perform_row_action_deactivate(self, request, obj):
        """Check if user can deactivate - USE self.user_role"""
        if self.user_role:
            return self.user_role.name in ['Admin', 'Manager']
        return False

    class Meta:
        model = ServiceType
        fields = ['id', 'name', 'category', 'is_active']
        row_selector = {}
```

---

## Meta Class Options

### Required Options

```python
class Meta:
    model = MyModel                      # REQUIRED: The model to display
    fields = ['id', 'name', 'status']    # REQUIRED: Model field names ONLY
```

**CRITICAL**: The `fields` list must **only contain model field names** (fields mapped to `ModelCol`). Do NOT include custom columns like `StringCol`, `StatusCol`, `TagsCol`, etc.

**⚠️ Reserved / Auto-injected Names — NEVER include in `Meta.fields`:**

The following names are automatically injected by the CRUD package at runtime. Including any of them in `Meta.fields` will raise a `rest_framework` serializer error:

| Name | Reason |
|------|--------|
| `actions` | Auto-injected row actions list |
| `row_actions` | Alias for row actions |
| `status` | Conflicts with workflow status injection |
| `workflow_status` | Auto-injected workflow status dict |
| `object_uuid` | Auto-injected object UUID |
| `detail_url` | Auto-injected detail URL |
| `field_title` | Auto-injected title field |
| `pk` | Auto-injected primary key |

If you need to display workflow status as a column, declare it as a `StatusCol` (a custom column) and **exclude** it from `Meta.fields`.

**Correct**:
```python
class PatientTable(ModelTable):
    # Model fields - include in Meta.fields
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    name = ModelCol(display_as="Name", searchable=True, sortable=True)

    # Custom columns - DO NOT include in Meta.fields
    is_active = StringCol(display_as="Status", searchable=True)
    workflow_status = StatusCol(display_as="Workflow Status", searchable=True)

    class Meta:
        model = Patient
        fields = ['id', 'name']  # ✅ Only model fields — no 'actions', 'status', 'workflow_status' etc.
        row_selector = {}
```

**Wrong**:
```python
class Meta:
    model = Patient
    fields = ['id', 'name', 'actions', 'status', 'workflow_status']  # ❌ Reserved names cause serializer errors
```

### Core Options

```python
class Meta:
    model = MyModel
    fields = ['id', 'name', 'email']

    page_title = "Custom Table Title"   # Override CRUD view's page title
    detail_class = MyDetailClass         # Custom detail view class
    row_selector = {}                    # Enable row selection
```

**page_title**: Overrides the page title from CRUD view.

**detail_class**: Custom detail view class. See `packages/crud/detail.md`.

**row_selector**: Enable row selection. Always use empty dict: `{}`.

### UI Visibility Controls

Control which table sections are visible (all default to `True`):

```python
class Meta:
    model = MyModel
    fields = ['id', 'name']

    show_header = True          # Show/hide table header with title
    show_utilities = True        # Show/hide search/filter/download bar
    show_body = True            # Show/hide table body
    show_pagination = True      # Show/hide pagination controls
```

**Use Cases**:
- `show_pagination = False` for small tables
- `show_utilities = False` for embedded tables
- `show_header = False` for dashboard widgets

### Utilities Configuration

Configure search bar, filters, and column options:

```python
class Meta:
    model = MyModel
    fields = ['id', 'name']

    utilities_config = {
        "show_search": True,              # Show search box (default: True)
        "show_filters_button": True,      # Show filters button (default: True)
        "show_column_options": True,      # Show column visibility (default: True)
        "search_placeholder": "Search...", # Search placeholder (default: "Search...")
    }
```

### Pagination Configuration

Configure pagination options:

```python
class Meta:
    model = MyModel
    fields = ['id', 'name']

    pagination_config = {
        "show_rows_per_page": True,                  # Show rows per page dropdown
        "rows_per_page_options": [10, 20, 50, 100], # Page size options
        "show_page_info": True,                      # Show "1-10 of 100" text
    }
```

### Table Features Configuration

Configure column interaction features:

```python
class Meta:
    model = MyModel
    fields = ['id', 'name']

    table_features_config = {
        "enable_column_pinning": True,    # Allow pinning columns
        "enable_sorting": True,            # Allow sorting
        "enable_hiding": True,             # Allow hiding columns
        "enable_column_ordering": True,    # Allow reordering
    }
```

### Form Configuration

Configure form display:

```python
class Meta:
    model = MyModel
    fields = ['id', 'name']

    form_config = {
        "show_confirm_alert": False,  # Show confirmation before submit
        "show_icon": False,            # Show icon in form
    }
```

### Complete Meta Example

```python
from .detail import PatientDetail

class PatientTable(ModelTable):
    # Model fields - INCLUDE in Meta.fields
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    name = ModelCol(display_as="Name", searchable=True, sortable=True)
    email = ModelCol(display_as="Email", searchable=True, sortable=False)

    # Custom columns - DO NOT INCLUDE in Meta.fields
    status = StatusCol(display_as="Status", searchable=True)

    class Meta:
        # Required - ONLY model fields
        model = Patient
        fields = ['id', 'name', 'email']  # NOT 'status'

        # Core
        page_title = "Patient Records"
        detail_class = PatientDetail
        row_selector = {}

        # UI visibility
        show_header = True
        show_utilities = True
        show_body = True
        show_pagination = True

        # Utilities
        utilities_config = {
            "show_search": True,
            "show_filters_button": True,
            "show_column_options": True,
            "search_placeholder": "Search patients...",
        }

        # Pagination
        pagination_config = {
            "show_rows_per_page": True,
            "rows_per_page_options": [10, 25, 50, 100],
            "show_page_info": True,
        }

        # Table features
        table_features_config = {
            "enable_column_pinning": True,
            "enable_sorting": True,
            "enable_hiding": True,
            "enable_column_ordering": True,
        }

        # Form
        form_config = {
            "show_confirm_alert": False,
            "show_icon": False,
        }
```

---

## Best Practices

1. **Use `self.user_role`**: Always use `self.user_role` instead of `get_current_role()` in table methods for export compatibility
2. **Column Types**: Use `ModelCol` for model fields, `StringCol` for computed values
3. **Custom Display**: Implement `_getval` for formatted output (badges, links, dates)
4. **Custom Search**: Implement `_Q_obj` for special search logic (booleans, FKs, numeric)
5. **Conditional Actions**: Use `get_row_actions` to show contextual actions
6. **Permissions**: Use `can_perform_row_action_*` with `self.user_role` for role-based access
7. **Clear Messages**: Provide helpful success/error messages in action responses
8. **Validation**: Check dependencies before destructive actions (delete, deactivate)
9. **Performance**: Use `select_related`/`prefetch_related` in `get_table_data_queryset`

---

## Troubleshooting

### Table Not Showing Data

**Problem**: Empty table or no data loading

**Solutions**:
- Check `Meta.model` is correct
- Check `Meta.fields` match column definitions
- Verify `get_table_data_queryset()` returns objects

### Search Not Working

**Problem**: Column search not working

**Solutions**:
- Ensure column has `searchable=True`
- Check `_Q_obj` method returns valid Q object
- Verify Q object field names match model

### Row Actions Not Appearing

**Problem**: Actions not showing for rows

**Solutions**:
- Check `can_perform_row_action_*` using `self.user_role` returning True
- Verify `get_row_actions` not filtering out all actions
- Ensure user has required role/permissions

### Action Not Processing

**Problem**: Simple action not executing

**Solutions**:
- Implement `process_row_action_<key>` method
- Return tuple: `(success: bool, response: dict)`
- Check for exceptions in action method

### StatusCol/TagsCol Not Working

**Problem**: Workflow columns not displaying

**Solutions**:
- Ensure workflow class defined in CRUD view
- Check workflow has `Meta.statuses` or `Meta.tags`
- Verify column name matches convention

### Export Failing with Role Errors

**Problem**: Export task fails with role-related errors

**Solutions**:
- Replace `get_current_role()` with `self.user_role` in all table methods
- Ensure `_getval` methods use `self.user_role`
- Check `can_perform_row_action_*` methods use `self.user_role`
