# CRUD Detail Views Reference

Detail views provide a dedicated page for viewing a single record with custom layout and data.

## Essential Imports

```python
from ...packages.crud.detail.base import BaseDetail
from ...packages.crud.table.column import ModelCol, StringCol
from zango.core.utils import get_current_role
```

---

## Table of Contents

1. [BaseDetail - Main Detail Class](#basedetail---main-detail-class)
2. [Configuration](#configuration)
3. [Custom Fields](#custom-fields)
4. [Overridable Methods](#overridable-methods)
5. [Activity Timeline](#activity-timeline)
6. [Workflow Integration](#workflow-integration)
7. [Audit Logs](#audit-logs)
8. [Complete Examples](#complete-examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## BaseDetail - Main Detail Class

`BaseDetail` provides the detail view functionality for viewing individual CRUD records.

### Basic Structure

```python
from ...packages.crud.detail.base import BaseDetail

class MyModelDetail(BaseDetail):
    title = "name"  # Optional - field to use as detail title

    class Meta:
        fields = ['id', 'name', 'email', 'phone']  # Optional - override table fields
        show_activity_timeline = True  # Optional - show audit log timeline (default: True)
```

---

## Configuration

### Detail Class Registration

Detail classes are configured in the **table's Meta class**, not the view:

```python
# In tables.py
from .detail import MyModelDetail

class MyModelTable(ModelTable):
    id = ModelCol(display_as="ID")
    name = ModelCol(display_as="Name")
    # ... other columns ...

    class Meta:
        model = MyModel
        fields = ['id', 'name', 'email', 'phone']
        detail_class = MyModelDetail  # Register detail class here
```

```python
# In views.py - No detail configuration needed
class MyModelCrudView(BaseCrudView):
    page_title = "My Model"
    add_btn_title = "Add My Model"
    model = MyModel
    form = MyModelForm
    table = MyModelTable
```

### Meta Class Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `fields` | list | Table's `Meta.fields` | List of **model fields only** (`ModelCol`) — do NOT include `StringCol`, `StatusCol`, or other custom columns |
| `show_activity_timeline` | bool | `True` | Whether to show audit log timeline |

---

## Custom Fields

### Using Table Fields (Default)

By default, detail view uses the same fields as the table:

```python
# In tables.py
class PatientTable(ModelTable):
    id = ModelCol(display_as="ID")
    name = ModelCol(display_as="Name")
    email = ModelCol(display_as="Email")

    class Meta:
        model = Patient
        fields = ['id', 'name', 'email']  # Detail will use these
        detail_class = PatientDetail
```

```python
# In detail.py - No Meta.fields needed
class PatientDetail(BaseDetail):
    pass  # Uses table's fields
```

### Custom Fields in Detail

Override `Meta.fields` to show different fields in detail view:

```python
# In detail.py
class PatientDetail(BaseDetail):
    class Meta:
        fields = ['id', 'name', 'email', 'phone', 'address', 'date_of_birth']
        # Shows MORE fields than table
```

### Adding Custom Columns

Define custom columns in the detail class:

```python
from ...packages.crud.detail.base import BaseDetail
from ...packages.crud.table.column import ModelCol, StringCol

class PatientDetail(BaseDetail):
    id = ModelCol(display_as="Patient ID")
    name = ModelCol(display_as="Full Name")
    age = StringCol(display_as="Age")  # Custom computed field

    def age_getval(self, obj):
        """Calculate age from date_of_birth"""
        from datetime import date
        if obj.date_of_birth:
            today = date.today()
            age = today.year - obj.date_of_birth.year
            return f"{age} years"
        return "N/A"

    class Meta:
        fields = ['id', 'name', 'email']  # Only ModelCol fields — do NOT include 'age' (StringCol)
```

### Role-Based Field Visibility

Control field visibility by role using `user_roles` parameter:

```python
class ProgramDetail(BaseDetail):
    id = ModelCol(display_as="ID")
    name = ModelCol(display_as="Name")
    budget = ModelCol(
        display_as="Budget",
        user_roles=["Admin", "Finance Manager"]  # Only visible to these roles
    )
    internal_notes = ModelCol(
        display_as="Internal Notes",
        user_roles=["Admin"]  # Only visible to Admin
    )

    class Meta:
        fields = ['id', 'name', 'budget', 'internal_notes']
```

---

## Overridable Methods

BaseDetail provides several methods you can override for custom behavior.

### fetch_item_details()

Main method to add custom data to the detail view response.

**Default Behavior**: Returns object data with general_details, workflow_details, and configurations.

**Override to Add Custom Data**:

```python
class AuditDetail(BaseDetail):
    def fetch_item_details(self):
        """Add custom stats to detail view"""
        # Call parent to get default data
        data = super().fetch_item_details()

        # Get the object
        obj_uuid = self.get_object_uuid()
        obj = self.get_object(object_uuid=obj_uuid)

        # Add custom data
        from ..audit_findings.models import AuditFinding
        all_findings = AuditFinding.objects.filter(audit=obj)

        data["stats"] = {
            "total_findings": all_findings.count(),
            "open_findings": all_findings.filter(status='open').count(),
            "closed_findings": all_findings.filter(status='closed').count(),
        }

        # Add custom flags
        data["show_export_button"] = self._should_show_export_button(obj)

        return data
```

**Response Structure**:

```python
{
    "pk": 123,
    "object_uuid": "abc-def-...",
    "title": "Object Title",
    "general_details": {
        "fields": {
            "field_name": {
                "display_name": "Field Display Name",
                "value": "Field Value",
                "type": "string",
                ...
            },
            ...
        }
    },
    "workflow_details": {
        "current_status": "in_progress",
        "current_status_meta": {...},
        "next_transitions": [...],
        "tag_details": {...}
    },
    "configurations": {
        "show_activity_timeline": True
    },
    "row_actions": [...],
    "stats": {  # Custom data added
        "total_findings": 10,
        "open_findings": 5,
        "closed_findings": 5
    }
}
```

### get_title(obj, object_data)

Customize the detail view title.

**Default Behavior**: Uses `self.title` field value, or `str(obj)` if not set.

**Override for Custom Title**:

```python
class ProgramDetail(BaseDetail):
    def get_title(self, obj, object_data):
        """Custom title with program code and name"""
        return f"{obj.code} - {obj.name}"
```

**Using title Attribute**:

```python
class PatientDetail(BaseDetail):
    title = "name"  # Use 'name' field as title

    # OR for computed field:
    title = "full_name"  # Where full_name is in object_data

    def full_name_getval(self, obj):
        return f"{obj.first_name} {obj.last_name}"
```

### is_activity_timeline_visible(obj)

Control whether the audit log timeline is displayed.

**Default Behavior**: Returns `True` (timeline is visible).

**Override for Custom Logic**:

```python
class ProgramDetail(BaseDetail):
    def is_activity_timeline_visible(self, obj):
        """Only show timeline for programs in certain statuses"""
        from zango.core.utils import get_current_role

        role = get_current_role()

        # Only show timeline to Admin and Manager roles
        if role and role.name in ["Admin", "Manager"]:
            return True

        return False
```

**Using Meta Option**:

```python
class ProgramDetail(BaseDetail):
    class Meta:
        fields = ['id', 'name', 'code']
        show_activity_timeline = False  # Disable timeline
```

### get_detail_view_config(obj)

Provide configuration options for the detail view.

**Default Behavior**: Returns `{"show_activity_timeline": True/False}`.

**Override to Add Config**:

```python
class ProgramDetail(BaseDetail):
    def get_detail_view_config(self, obj):
        """Add custom configuration options"""
        config = super().get_detail_view_config(obj)

        # Add custom config
        config["show_export_button"] = self._can_export(obj)
        config["show_edit_button"] = self._can_edit(obj)
        config["readonly_mode"] = obj.status == 'archived'

        return config
```

### get_context_data(context, **kwargs)

Add additional context for template rendering.

**Default Behavior**: Returns the context unchanged.

**Override to Add Context**:

```python
class ProgramDetail(BaseDetail):
    def get_context_data(self, context, **kwargs):
        """Add custom context for template"""
        context = super().get_context_data(context, **kwargs)

        # Add custom context
        context['organization_name'] = self.request.user.organization.name
        context['show_reports'] = self.request.user.has_perm('view_reports')

        return context
```

### get_field_display_name_mapping()

Get mapping of field names to display names for audit logs.

**Default Behavior**: Returns mapping from table/detail column `display_as` attributes.

**Override for Custom Mapping**:

```python
class ProgramDetail(BaseDetail):
    def get_field_display_name_mapping(self):
        """Custom field name mapping for audit logs"""
        mapping = super().get_field_display_name_mapping()

        # Add custom mappings
        mapping['json_field_data'] = "Configuration Data"
        mapping['internal_code'] = "Internal Reference"

        return mapping
```

---

## Activity Timeline

The activity timeline shows audit logs and workflow transitions for the record.

### Default Behavior

By default, the timeline is visible and shows:
- All audit log entries (create, update, delete)
- All workflow transitions (status changes, tag changes)
- Formatted field changes with display names
- User who made the change
- Timestamp

### Controlling Timeline Visibility

**Method 1: Meta Option**

```python
class ProgramDetail(BaseDetail):
    class Meta:
        fields = ['id', 'name']
        show_activity_timeline = False  # Hide timeline
```

**Method 2: Override Method**

```python
class ProgramDetail(BaseDetail):
    def is_activity_timeline_visible(self, obj):
        """Custom logic for timeline visibility"""
        from zango.core.utils import get_current_role

        role = get_current_role()

        # Only show for certain roles
        if role and role.name in ["Admin", "Auditor"]:
            return True

        # Or based on object state
        if obj.status in ["completed", "archived"]:
            return True

        return False
```

### Customizing Audit Log Display

Override `get_custom_changes_display()` to customize how field changes are displayed:

```python
class ProgramDetail(BaseDetail):
    def get_custom_changes_display(self, obj, changes, field_mapping):
        """Custom audit log change display"""
        # Call parent for default formatting
        transformed_changes = super().get_custom_changes_display(
            obj, changes, field_mapping
        )

        # Add custom formatting for specific fields
        if 'budget' in transformed_changes:
            old_val, new_val = transformed_changes['budget']
            transformed_changes['Budget'] = [
                f"${old_val:,.2f}",
                f"${new_val:,.2f}"
            ]
            del transformed_changes['budget']

        return transformed_changes
```

### Customizing Field Display Names in Audit Logs

The audit log uses display names from table/detail columns. Override for custom mapping:

```python
class ProgramDetail(BaseDetail):
    def get_field_display_name_mapping(self):
        """Custom display names for audit logs"""
        mapping = super().get_field_display_name_mapping()

        # Add custom mappings
        mapping['created_by_id'] = "Created By"
        mapping['modified_by_id'] = "Last Modified By"
        mapping['json_config'] = "Configuration"

        return mapping
```

---

## Workflow Integration

Detail views automatically integrate with workflows when configured.

### Workflow Data in Detail View

When a workflow is configured on the CRUD view, the detail view automatically includes:

```python
{
    "workflow_details": {
        "current_status": "in_progress",
        "current_status_meta": {
            "label": "In Progress",
            "color": "#0d6efd"
        },
        "next_transitions": [
            {
                "key": "mark_complete",
                "name": "Mark Complete",
                "from_status": "in_progress",
                "to_status": "completed"
            }
        ],
        "tag_details": {
            "urgent": {"enabled": True, "label": "Urgent"},
            "reviewed": {"enabled": False, "label": "Reviewed"}
        }
    }
}
```

### Using Workflow Data in Detail View

```python
class ProgramDetail(BaseDetail):
    def fetch_item_details(self):
        """Add custom logic based on workflow status"""
        data = super().fetch_item_details()

        obj_uuid = self.get_object_uuid()
        obj = self.get_object(object_uuid=obj_uuid)

        # Get workflow status
        workflow_obj = self.get_workflow_object(obj)
        if workflow_obj:
            current_status, _ = workflow_obj.get_current_status()

            # Add conditional data based on status
            if current_status == "completed":
                data["show_completion_report"] = True
                data["completion_date"] = obj.completed_at.isoformat()

            if current_status in ["pending_review", "in_review"]:
                data["show_review_actions"] = True

        return data
```

### Workflow Transactions in Timeline

Workflow transitions automatically appear in the activity timeline:
- Status changes (initiated → in_progress)
- Tag changes (urgent tag enabled/disabled)
- System transitions
- User-triggered transitions

---

## Audit Logs

Detail views automatically track and display audit logs.

### Default Audit Log Features

- **Create Events**: Record creation with all field values
- **Update Events**: Field changes with old/new values
- **Delete Events**: Record deletion
- **User Tracking**: Who made the change
- **Timestamp**: When the change occurred
- **Formatted Values**: Dates, ForeignKeys, booleans, choices automatically formatted

### Excluding Fields from Audit Logs

System fields are automatically excluded:
- `created_by`
- `created_at`
- `modified_by`
- `modified_at`
- `object_uuid`

To exclude additional fields, override `get_custom_changes_display()`:

```python
class ProgramDetail(BaseDetail):
    def get_custom_changes_display(self, obj, changes, field_mapping):
        """Exclude sensitive fields from audit log"""
        # Get default changes
        transformed_changes = super().get_custom_changes_display(
            obj, changes, field_mapping
        )

        # Exclude additional fields
        excluded_fields = ['internal_notes', 'password_hash', 'api_key']
        for field in excluded_fields:
            transformed_changes.pop(field, None)

        return transformed_changes
```

### Custom Audit Log Retrieval

Override `fetch_audit_logs()` for custom audit log logic:

```python
class ProgramDetail(BaseDetail):
    def fetch_audit_logs(self):
        """Custom audit log retrieval with filtering"""
        # Get default audit logs
        data = super().fetch_audit_logs()

        # Filter audit logs based on user role
        from zango.core.utils import get_current_role
        role = get_current_role()

        if role and role.name not in ["Admin", "Auditor"]:
            # Remove sensitive audit entries for non-admin users
            data["audit_logs"] = [
                log for log in data["audit_logs"]
                if log.get("action") != "delete"
            ]

        return data
```

---

## Complete Examples

### Example 1: Basic Detail View

```python
# detail.py
from ...packages.crud.detail.base import BaseDetail

class PatientDetail(BaseDetail):
    title = "name"  # Use name field as title

    class Meta:
        fields = ['id', 'name', 'code', 'email', 'phone', 'date_of_birth']
        show_activity_timeline = True
```

```python
# tables.py
from .detail import PatientDetail

class PatientTable(ModelTable):
    id = ModelCol(display_as="ID")
    name = ModelCol(display_as="Name")
    code = ModelCol(display_as="Code")

    class Meta:
        model = Patient
        fields = ['id', 'name', 'code']
        detail_class = PatientDetail  # Register detail class
```

### Example 2: Detail with Custom Data and Stats

```python
# detail.py
from ...packages.crud.detail.base import BaseDetail
from ...packages.workflow.base.utils import filter_objects_by_workflow_status

class AuditDetail(BaseDetail):
    """
    Detail class for Audit with findings stats
    """

    def fetch_item_details(self):
        """Add audit findings stats to detail response"""
        data = super().fetch_item_details()

        # Get the audit object
        obj_uuid = self.get_object_uuid()
        obj = self.get_object(object_uuid=obj_uuid)

        # Calculate findings stats
        from ..audit_findings.models import AuditFinding
        all_findings = AuditFinding.objects.filter(audit=obj)
        total_findings = all_findings.count()

        open_findings = filter_objects_by_workflow_status(
            AuditFinding, status="open"
        ).filter(audit=obj).count()

        closed_findings = filter_objects_by_workflow_status(
            AuditFinding, status=["closed", "submitted_capa"]
        ).filter(audit=obj).count()

        # Add stats to response
        data["stats"] = {
            "total_findings": total_findings,
            "open_findings": open_findings,
            "closed_findings": closed_findings,
        }

        return data
```

### Example 3: Detail with Role-Based Visibility

```python
# detail.py
from ...packages.crud.detail.base import BaseDetail
from ...packages.crud.table.column import ModelCol
from zango.core.utils import get_current_role
from ..utils.policy_utils import check_role_policy

class ProgramDetail(BaseDetail):
    id = ModelCol(display_as="ID")
    name = ModelCol(display_as="Name")
    code = ModelCol(display_as="Code")
    budget = ModelCol(
        display_as="Budget",
        user_roles=["Admin", "Finance Manager"]  # Only visible to these roles
    )
    internal_notes = ModelCol(
        display_as="Internal Notes",
        user_roles=["Admin"]  # Only visible to Admin
    )

    class Meta:
        fields = ['id', 'name', 'code', 'budget', 'internal_notes']

    def fetch_item_details(self):
        """Add role-based flags"""
        data = super().fetch_item_details()

        obj_uuid = self.get_object_uuid()
        role = get_current_role()

        # Add role-based flags
        data["can_edit_budget"] = False
        data["can_manage_vendors"] = False

        if role:
            data["can_edit_budget"] = check_role_policy(role.name, 'BudgetEditPolicy')
            data["can_manage_vendors"] = check_role_policy(role.name, 'VendorManagePolicy')

        return data

    def is_activity_timeline_visible(self, obj):
        """Only show timeline to Admin and Auditor roles"""
        role = get_current_role()
        if role and role.name in ["Admin", "Auditor"]:
            return True
        return False
```

### Example 4: Detail with Custom Title and Conditional Data

```python
# detail.py
from ...packages.crud.detail.base import BaseDetail

class ProgramDetail(BaseDetail):
    def get_title(self, obj, object_data):
        """Custom title with code and name"""
        return f"{obj.code} - {obj.name}"

    def fetch_item_details(self):
        """Add conditional data based on workflow status"""
        data = super().fetch_item_details()

        obj_uuid = self.get_object_uuid()
        obj = self.get_object(object_uuid=obj_uuid)

        # Get workflow status
        workflow_obj = self.get_workflow_object(obj)
        if workflow_obj:
            current_status, _ = workflow_obj.get_current_status()

            # Add status-specific data
            if current_status == "completed":
                data["show_completion_report"] = True
                data["completion_date"] = obj.completed_at.isoformat() if obj.completed_at else None

            if current_status in ["pending_review", "in_review"]:
                data["show_review_actions"] = True
                data["reviewers"] = self._get_reviewers(obj)

            # Check for tags
            tag_details = workflow_obj.get_tags_details()
            if tag_details.get('urgent', {}).get('enabled'):
                data["is_urgent"] = True

        # Add custom flags
        from zango.core.utils import get_current_role
        role = get_current_role()

        if role:
            data["can_edit"] = self._can_edit(role, obj)
            data["can_delete"] = self._can_delete(role, obj)

        return data

    def _get_reviewers(self, obj):
        """Get list of reviewers for object"""
        from ..review.models import Reviewer
        reviewers = Reviewer.objects.filter(program=obj, is_active=True)

        return [
            {
                "name": r.name,
                "email": r.email,
                "status": r.status,
            }
            for r in reviewers
        ]

    def _can_edit(self, role, obj):
        """Check if user can edit based on role and object state"""
        from ..utils.policy_utils import check_role_policy

        # Check policy
        if not check_role_policy(role.name, 'ProgramEditPolicy'):
            return False

        # Check object state
        if obj.status in ["completed", "archived"]:
            return False

        return True

    def _can_delete(self, role, obj):
        """Check if user can delete"""
        from ..utils.policy_utils import check_role_policy

        # Only Admin can delete
        if role.name != "Admin":
            return False

        # Can't delete if has related data
        if obj.vendors.exists() or obj.documents.exists():
            return False

        return True
```

---

## Best Practices

### 1. Use Table Fields by Default

Unless you need different fields in detail view, don't override `Meta.fields`:

```python
# ❌ Redundant - Duplicating table fields
class PatientDetail(BaseDetail):
    class Meta:
        fields = ['id', 'name', 'email']  # Same as table

# ✅ Better - Use table fields automatically
class PatientDetail(BaseDetail):
    pass  # Uses table's fields
```

### 2. Override fetch_item_details() for Custom Data

Add custom data by overriding `fetch_item_details()`, not `get()`:

```python
# ❌ Wrong - Overriding get()
class PatientDetail(BaseDetail):
    def get(self, request, *args, **kwargs):
        # Custom logic...
        return super().get(request, *args, **kwargs)

# ✅ Correct - Override fetch_item_details()
class PatientDetail(BaseDetail):
    def fetch_item_details(self):
        data = super().fetch_item_details()
        data["custom_stats"] = self._get_stats()
        return data
```

### 3. Use Role-Based Visibility Appropriately

Use `user_roles` for fields:

```python
class ProgramDetail(BaseDetail):
    budget = ModelCol(
        display_as="Budget",
        user_roles=["Admin", "Finance Manager"]  # Field visibility
    )

    class Meta:
        fields = ['id', 'name', 'budget']
```

### 4. Use Workflow Integration

Leverage workflow data instead of querying status manually:

```python
# ❌ Wrong - Manual status queries
def fetch_item_details(self):
    data = super().fetch_item_details()
    obj_uuid = self.get_object_uuid()
    obj = self.get_object(object_uuid=obj_uuid)

    # Manual workflow query
    from ...packages.workflow.base.models import WorkflowTransaction
    latest = WorkflowTransaction.objects.filter(
        obj_uuid=obj_uuid,
        transition_type='status'
    ).order_by('-created_at').first()

    data["current_status"] = latest.to_state if latest else None
    return data

# ✅ Correct - Use workflow object
def fetch_item_details(self):
    data = super().fetch_item_details()
    # Workflow data is automatically in data["workflow_details"]
    # Or use workflow object:
    obj_uuid = self.get_object_uuid()
    obj = self.get_object(object_uuid=obj_uuid)

    workflow_obj = self.get_workflow_object(obj)
    if workflow_obj:
        current_status, _ = workflow_obj.get_current_status()
        data["custom_status_logic"] = self._process_status(current_status)

    return data
```

### 5. Document Complex Logic

Add docstrings to complex methods:

```python
class ProgramDetail(BaseDetail):
    def fetch_item_details(self):
        """
        Add custom program data to detail view.

        Additional data included:
        - stats: Program statistics (vendors, documents, budget)
        - can_edit: Whether user can edit based on role and status
        - show_completion_report: Show completion report if status is completed
        """
        data = super().fetch_item_details()
        # ... implementation ...
        return data
```

---

## Troubleshooting

### Detail View Not Loading

**Problem**: Detail class not registered or configured incorrectly.

**Solution**: Ensure `detail_class` is in table Meta, not view:

```python
# In tables.py
from .detail import MyModelDetail

class MyModelTable(ModelTable):
    # ... columns ...

    class Meta:
        model = MyModel
        fields = ['id', 'name']
        detail_class = MyModelDetail  # Must be here!
```

### Fields Not Showing in Detail View

**Problem**: Fields not in `Meta.fields` or excluded.

**Solution**: Check field is in Meta.fields:

```python
class MyModelDetail(BaseDetail):
    class Meta:
        fields = ['id', 'name', 'missing_field']  # Add missing field
```

### Role-Based Fields Not Showing

**Problem**: Current user's role not in `user_roles` list.

**Debugging**:

```python
class MyModelDetail(BaseDetail):
    budget = ModelCol(
        display_as="Budget",
        user_roles=["Admin", "Finance Manager"]
    )

    def fetch_item_details(self):
        """Debug version"""
        data = super().fetch_item_details()

        from zango.core.utils import get_current_role
        role = get_current_role()
        print(f"User role: {role.name if role else 'No role'}")  # Debug
        print(f"Budget visible: {role.name in ['Admin', 'Finance Manager'] if role else False}")  # Debug

        return data
```

### Activity Timeline Not Showing

**Problem**: `show_activity_timeline` set to `False` or `is_activity_timeline_visible()` returning `False`.

**Solution**:

```python
# Check Meta option
class MyModelDetail(BaseDetail):
    class Meta:
        show_activity_timeline = True  # Ensure this is True or omitted (default)

# Or check method
def is_activity_timeline_visible(self, obj):
    """Ensure this returns True"""
    return True
```

### Custom Data Not Appearing

**Problem**: Not calling `super().fetch_item_details()` or returning wrong structure.

**Solution**:

```python
# ❌ Wrong - Not calling super()
def fetch_item_details(self):
    return {"custom_data": "value"}  # Missing default data!

# ✅ Correct - Call super() first
def fetch_item_details(self):
    data = super().fetch_item_details()  # Get default data
    data["custom_data"] = "value"  # Add custom data
    return data
```

### Workflow Details Not Showing

**Problem**: Workflow not configured on view.

**Solution**:

```python
# In views.py
class MyModelCrudView(BaseCrudView):
    # ... other attributes ...
    workflow = MyModelWorkflow  # Must configure workflow!
```

---

## Related Documentation

- **Views**: `references/packages/crud/views/core.md` - BaseCrudView, permission methods
- **Tables**: `references/packages/crud/tables/core.md` - Column types, row actions, include_in_detail parameter
- **Forms**: `references/packages/crud/forms/core.md` - Form field types, validation
- **Workflows**: `references/packages/workflow/workflow.md` - Status/tag management
- **Policies**: `references/core/policies.md` - Permission configuration
