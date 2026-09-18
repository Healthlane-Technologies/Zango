# Zango CRUD Views — Core

> Splits of the CRUD views reference: **core.md** (this file), [reference.md](reference.md) (method reference, complete examples), [troubleshooting.md](troubleshooting.md).

## Essential Imports

```python
from ...packages.crud.base import BaseCrudView
from .models import MyModel
from .forms import MyModelForm
from .tables import MyModelTable
from .workflow import MyModelWorkflow  # Optional
from .detail import MyModelDetail  # Optional - or use Meta.detail_class in table
```

---

## Table of Contents

1. [BaseCrudView - Main CRUD Interface](#basecrudview---main-crud-interface)
2. [View Attributes](#view-attributes)
3. [Permission Methods](#permission-methods)
4. [Detail Class Integration](#detail-class-integration)
5. [Workflow Integration](#workflow-integration)
6. [Custom Templates](#custom-templates)
7. [Method Reference](reference.md#method-reference)
8. [Complete Examples](reference.md#complete-examples)
9. [Best Practices](troubleshooting.md#best-practices)
10. [Troubleshooting](troubleshooting.md#troubleshooting)

---

## BaseCrudView - Main CRUD Interface

`BaseCrudView` is the main class for creating CRUD interfaces with table, form, detail view, and workflow support.

### Basic Structure

```python
class MyModelCrudView(BaseCrudView):
    # Required attributes
    page_title = "My Model"
    add_btn_title = "Add My Model"  # REQUIRED - DO NOT FORGET
    model = MyModel
    form = MyModelForm
    table = MyModelTable

    # Optional attributes
    workflow = MyModelWorkflow  # Optional
    table_template = "crud/table.html"  # Optional - override template
    detail_template = "crud/detail.html"  # Optional - override template
```

---

## View Attributes

### Required Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_title` | str | **Yes** | Page title displayed at top |
| `add_btn_title` | str | **Yes** | Text for "Add" button (forgetting this causes errors!) |
| `model` | Model class | **Yes** | Django model class |
| `form` | Form class | **Yes** | Form class (BaseForm or BaseSimpleForm) |
| `table` | Table class | **Yes** | Table class (ModelTable) |

⚠️ **Critical**: Missing `add_btn_title` will cause an AttributeError when the view loads!

### Optional Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow` | Workflow class | `None` | Workflow class for status/tag management |
| `table_template` | str | `"crud/table.html"` | Custom template for table view |
| `detail_template` | str | `"crud/detail.html"` | Custom template for detail view |

### Detail Class Configuration

The detail class is **NOT** configured directly on the view. It's configured in the **table's Meta class**:

```python
# In tables.py
class MyModelTable(ModelTable):
    # ... columns ...

    class Meta:
        model = MyModel
        fields = ['id', 'name']
        detail_class = MyModelDetail  # Configure detail class here
```

See [Detail Class Integration](#detail-class-integration) below for details.

---

## Permission Methods

BaseCrudView provides three permission check methods that control UI button visibility and feature access.

### Method 1: display_add_button_check()

Controls whether the "Add" button is displayed in the table view.

**Default Implementation**: Checks if `"add"` feature is enabled in policies.

**Override for Custom Logic**:

```python
class PatientCrudView(BaseCrudView):
    page_title = "Patients"
    add_btn_title = "Add Patient"
    model = Patient
    form = PatientForm
    table = PatientTable

    def display_add_button_check(self, request):
        """
        Control add button visibility with custom logic.

        Args:
            request: Django request object

        Returns:
            bool: True if add button should be displayed, False otherwise
        """
        from zango.core.utils import get_current_role
        from ..utils.policy_utils import check_role_policy

        # Get current user's role
        role = get_current_role()
        if role and role.name:
            # Check against custom policy
            return check_role_policy(role.name, 'PatientCreationPolicy')
        return False
```

**Common Use Cases**:
- Role-based access control
- Business logic (e.g., only allow add if certain conditions met)
- Time-based restrictions (e.g., only during business hours)
- Quota limits (e.g., max 100 records per organization)

### Method 2: display_download_button_check()

Controls whether the "Export/Download" button is displayed.

**Default Implementation**: Checks if `"download"` or `"export"` feature is enabled in policies.

**Override for Custom Logic**:

```python
def display_download_button_check(self, request):
    """
    Control export button visibility.

    Args:
        request: Django request object

    Returns:
        bool: True if export button should be displayed, False otherwise
    """
    from zango.core.utils import get_current_role

    role = get_current_role()
    if role and role.name:
        # Only specific roles can export
        allowed_roles = ["Admin", "Manager", "Analyst"]
        return role.name in allowed_roles
    return False
```

**Common Use Cases**:
- Role-based export permissions
- Audit logging requirements (only certain roles can export sensitive data)
- License-based restrictions
- Data sensitivity controls

### Method 3: has_upload_perm()

Controls whether bulk upload functionality is available.

**Default Implementation**: Checks if `"upload"` feature is enabled in policies.

**Override for Custom Logic**:

```python
def has_upload_perm(self, request):
    """
    Control upload functionality availability.

    Args:
        request: Django request object

    Returns:
        bool: True if upload is allowed, False otherwise
    """
    from zango.core.utils import get_current_role

    role = get_current_role()
    if role and role.name:
        # Only admins can bulk upload
        return role.name == "Admin"
    return False
```

**Common Use Cases**:
- Restrict bulk imports to admin users
- Require special permissions for data imports
- Control data entry methods

### Policy Features vs Check Methods

There are **two ways** to control permissions:

**Method 1: Policy Features** (in policies.json)

```json
{
    "name": "PatientCrudViewAccessPolicy",
    "description": "Full access to Patient CRUD",
    "statement": {
        "permissions": [
            {
                "name": "backend.patients.views.PatientCrudView",
                "type": "view",
                "features": ["add", "download", "upload"]
            }
        ]
    },
    "roles": ["Admin", "Manager"]
}
```

**Method 2: Check Methods** (in view class - shown above)

**How They Work Together**:
- **Policy features** define baseline access at the role level
- **Check methods** add additional runtime logic (business rules, conditions)
- If **only policy** is defined: Feature is enabled for all users with that policy
- If **check method** is defined: It provides additional control layer
- Check methods can call `has_view_feature(request, "add")` to check policy, then add extra logic

**Note**: After creating/updating policies, you MUST sync from App Panel. See `references/core/policies.md`.

---

## Detail Class Integration

Detail views provide a dedicated page for viewing a single record with custom layout and sections.

### Configuration

Detail classes are configured in the **table's Meta class**, not directly on the view:

```python
# In detail.py
from ...packages.crud.detail.base import BaseDetail

class PatientDetail(BaseDetail):
    def get_sections(self, obj):
        return [
            {
                "title": "Basic Information",
                "fields": ["name", "code", "email", "phone"],
            },
            {
                "title": "Medical Information",
                "fields": ["date_of_birth", "blood_group", "allergies"],
            }
        ]
```

```python
# In tables.py
class PatientTable(ModelTable):
    id = ModelCol(display_as="ID")
    name = ModelCol(display_as="Name")
    # ... other columns ...

    class Meta:
        model = Patient
        fields = ['id', 'name', 'code', 'email']
        detail_class = PatientDetail  # Configure detail class here
```

```python
# In views.py - No detail class configuration needed here!
class PatientCrudView(BaseCrudView):
    page_title = "Patients"
    add_btn_title = "Add Patient"
    model = Patient
    form = PatientForm
    table = PatientTable
    # workflow = PatientWorkflow  # Optional
```

### How Detail Views Work

1. **User clicks on a table row** → Detail view opens
2. **View calls `get_detail_obj(table_obj)`** to get detail instance
3. **Detail class renders** using `detail_template` with custom sections
4. **Detail view shows** formatted field values, related objects, and custom sections

### Detail Class Features

See `references/packages/crud/detail.md` for complete detail class documentation including:
- Custom sections and layouts
- Related object display
- Custom field rendering
- Actions and permissions
- Workflow integration

---

## Workflow Integration

Workflows add status/tag management and state transitions to CRUD records.

### Basic Workflow Setup

```python
# In workflow.py
from ...packages.workflow.base.base import BaseWorkflow

class ProgramWorkflow(BaseWorkflow):
    class Meta:
        model = Program
        on_create_status = "initiated"  # Initial status when record created

        statuses = {
            "initiated": {
                "label": "Initiated",
                "color": "#6c757d"
            },
            "in_progress": {
                "label": "In Progress",
                "color": "#0d6efd"
            },
            "completed": {
                "label": "Completed",
                "color": "#198754"
            }
        }

        transitions = [
            {
                "name": "Start Progress",
                "from_status": "initiated",
                "to_status": "in_progress"
            },
            {
                "name": "Mark Complete",
                "from_status": "in_progress",
                "to_status": "completed"
            }
        ]
```

```python
# In tables.py
from ...packages.crud.table.column import StatusCol, WorkflowTransitionsCol

class ProgramTable(ModelTable):
    id = ModelCol(display_as="ID")
    name = ModelCol(display_as="Name")
    status = StatusCol(display_as="Status")  # Auto-displays current status
    transitions = WorkflowTransitionsCol(display_as="Actions")  # Auto-displays available transitions

    class Meta:
        model = Program
        fields = ['id', 'name']  # Don't include status/transitions - they're custom columns
```

```python
# In views.py
class ProgramCrudView(BaseCrudView):
    page_title = "Programs"
    add_btn_title = "Add Program"
    model = Program
    form = ProgramForm
    table = ProgramTable
    workflow = ProgramWorkflow  # Add workflow
```

### Workflow Features

- **Automatic status initialization**: When a record is created, `on_create_status` is set
- **Status display**: `StatusCol` automatically shows current status with color badge
- **Transitions display**: `WorkflowTransitionsCol` shows available transitions based on current status
- **Role-based transitions**: Transitions can be restricted by role
- **Workflow history**: Track all status changes with timestamps

See `references/packages/workflow/workflow.md` for complete workflow documentation.

---

## Custom Templates

Override default templates for table and detail views.

### Default Templates

```python
class BaseCrudView(TemplateView):
    table_template = "crud/table.html"
    detail_template = "crud/detail.html"
```

### Custom Template Example

```python
class PatientCrudView(BaseCrudView):
    page_title = "Patients"
    add_btn_title = "Add Patient"
    model = Patient
    form = PatientForm
    table = PatientTable

    # Custom templates
    table_template = "patients/custom_table.html"
    detail_template = "patients/custom_detail.html"
```

**Use Cases**:
- Custom styling for specific CRUD views
- Additional UI elements (charts, graphs, etc.)
- Custom JavaScript/CSS for specific views
- Integration with third-party UI libraries

---

## URL Configuration

Register the view in your module's `urls.py`:

```python
from django.urls import path
from .views import MyModelCrudView

urlpatterns = [
    path('my-model/', MyModelCrudView.as_view(), name='my_model_crud'),
]
```

**⚠️ CRITICAL: Never Use Empty Paths**

ALWAYS specify a non-empty path for CRUD views:

```python
# ❌ WRONG - Empty path causes routing issues
urlpatterns = [
    path('', MyModelCrudView.as_view(), name='my_model_crud'),
]

# ✅ CORRECT - Always specify a path
urlpatterns = [
    path('my-model/', MyModelCrudView.as_view(), name='my_model_crud'),
]
```

Empty paths can cause URL conflicts and routing problems. Every CRUD view must have a distinct, non-empty path.

**URL Path Convention**:
- **Never use empty paths** (`''`) for CRUD views
- Use lowercase
- Use hyphens (not underscores)
- Keep it simple and descriptive
- Always end with trailing slash
- Example: `patients/`, `service-types/`, `audit-findings/`

---
