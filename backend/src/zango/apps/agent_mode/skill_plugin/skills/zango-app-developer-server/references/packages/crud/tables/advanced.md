# Zango CRUD Tables — Advanced

> Advanced table patterns and troubleshooting. Start at [core.md](core.md).

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

> **Fetching these rows from a custom page?** The response shape has three
> traps that all fail silently with a 200 — the rows sit behind
> `action=get_table_data`, they are at `j.data` (a plain array), and any
> column with a `_getval` is serialized to an **HTML string**, so a boolean
> column is truthy whatever its value. See
> [../../../frontend/entity-360.md](../../../frontend/entity-360.md) §4b.


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
