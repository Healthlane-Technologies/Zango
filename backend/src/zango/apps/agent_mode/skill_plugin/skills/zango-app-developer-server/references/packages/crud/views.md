# CRUD Views Reference

Views connect forms, tables, workflows, and detail views to create the complete CRUD interface.

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
7. [Method Reference](#method-reference)
8. [Complete Examples](#complete-examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

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

## Method Reference

BaseCrudView provides several methods you can override for custom behavior.

### get_table_obj(**kwargs)

Returns the table instance for the current request.

```python
def get_table_obj(self, **kwargs):
    """
    Create and return table instance.

    Returns:
        ModelTable: Table instance with request and crud_view_instance set
    """
    return self.table(request=self.request, crud_view_instance=self, **kwargs)
```

**Override Example**:

```python
def get_table_obj(self, **kwargs):
    """Add extra context to table"""
    table_obj = super().get_table_obj(**kwargs)
    table_obj.extra_context = {"organization": self.request.user.organization}
    return table_obj
```

### get_detail_obj(table_obj)

Returns the detail view instance. Automatically uses `detail_class` from table Meta if defined.

```python
def get_detail_obj(self, table_obj):
    """
    Create and return detail view instance.

    Args:
        table_obj: Table instance

    Returns:
        BaseDetail: Detail instance (from table Meta or default BaseDetail)
    """
    if hasattr(table_obj.Meta, "detail_class"):
        detail_class = table_obj.Meta.detail_class
        return detail_class(
            request=self.request,
            crud_view_instance=self,
            table_obj=table_obj
        )

    from ..detail.base import BaseDetail
    return BaseDetail(
        request=self.request,
        crud_view_instance=self,
        table_obj=table_obj
    )
```

**Override Example**:

```python
def get_detail_obj(self, table_obj):
    """Pass additional context to detail view"""
    detail_obj = super().get_detail_obj(table_obj)
    detail_obj.show_audit_log = self.request.user.is_superuser
    return detail_obj
```

### get_workflow_obj(**kwargs)

Returns the workflow instance if workflow is configured.

```python
def get_workflow_obj(self, **kwargs):
    """
    Create and return workflow instance.

    Args:
        **kwargs: Can include object_instance for existing records

    Returns:
        BaseWorkflow or None: Workflow instance if configured, None otherwise
    """
    workflow_class = getattr(self, "workflow", None)
    if workflow_class:
        workflow_object = workflow_class(
            request=self.request,
            crud_view_instance=self,
            object_instance=kwargs.get("object_instance", None),
        )
        return workflow_object
    return None
```

**Override Example**:

```python
def get_workflow_obj(self, **kwargs):
    """Add custom workflow initialization"""
    workflow_obj = super().get_workflow_obj(**kwargs)
    if workflow_obj:
        workflow_obj.user_role = get_current_role()
    return workflow_obj
```

### get_form(data=None, files=None, instance=None)

Returns the form instance for create or row action forms.

```python
def get_form(self, data=None, files=None, instance=None):
    """
    Create and return form instance.

    Args:
        data: POST data
        files: Uploaded files
        instance: Model instance (for edit forms)

    Returns:
        BaseForm or BaseSimpleForm: Form instance
    """
    action_type = self.request.GET.get("action_type")
    if action_type == "row":
        # Handle row action form
        object_uuid = self.request.GET.get("object_uuid")
        action_key = self.request.GET.get("action_key")
        return self.get_row_action_form(
            object_uuid, action_key, data, files, instance
        )

    # Return create form
    return self.form(data=data, files=files, crud_view_instance=self)
```

**Override Example**:

```python
def get_form(self, data=None, files=None, instance=None):
    """Pass custom context to form"""
    form = super().get_form(data, files, instance)
    form.current_user = self.request.user
    form.organization = self.request.user.organization
    return form
```

### get_row_action_form(obj_uuid, action_key, data=None, files=None, instance=None)

Returns form for row actions.

```python
def get_row_action_form(self, obj_uuid, action_key, data=None, files=None, instance=None):
    """
    Get form for row action.

    Args:
        obj_uuid: UUID of the object
        action_key: Key of the action
        data: POST data
        files: Uploaded files
        instance: Model instance

    Returns:
        BaseForm: Form instance for the action

    Raises:
        ImproperlyConfigured: If action or form not found
        PermissionDenied: If user cannot perform action
    """
    table_obj = self.get_table_obj()
    row_actions = self.get_row_actions(table_obj)
    row_action = [r for r in row_actions if r["key"] == action_key]

    if not row_action:
        raise ImproperlyConfigured("No row action found or action is not allowed")

    row_action = row_action[0]
    action_form = row_action.get("form")

    if not action_form:
        raise ImproperlyConfigured("Form is not configured for this action")

    if not instance:
        model = action_form.Meta.model
        instance = model.objects.get(object_uuid=obj_uuid)

    # Check permission
    can_perform_action = table_obj.can_include_row_action(
        self.request, row_action, instance
    )
    if not can_perform_action:
        raise PermissionDenied(f"Can not perform action {row_action['name']}")

    return action_form(
        data=data, files=files, instance=instance, crud_view_instance=self
    )
```

**Override Example**:

```python
def get_row_action_form(self, obj_uuid, action_key, data=None, files=None, instance=None):
    """
    Use different form for edit action based on user role or record state.
    """
    if action_key == 'edit':
        # Use different form based on workflow status
        if not instance:
            instance = self.model.objects.get(object_uuid=obj_uuid)

        # Use specialized edit form if record is in certain state
        workflow_obj = self.get_workflow_obj(object_instance=instance)
        if workflow_obj:
            current_status, _ = workflow_obj.get_current_status()
            if current_status == 'approved':
                # Use restricted edit form for approved records
                from .forms import ProgramRestrictedEditForm
                return ProgramRestrictedEditForm(
                    data=data,
                    files=files,
                    instance=instance,
                    crud_view_instance=self
                )

        # Use regular edit form
        from .forms import ProgramEditForm
        return ProgramEditForm(
            data=data,
            files=files,
            instance=instance,
            crud_view_instance=self
        )

    # For other actions, use parent method
    return super().get_row_action_form(obj_uuid, action_key, data, files, instance)
```

### get_context_data(**kwargs)

Builds context for template rendering.

```python
def get_context_data(self, **kwargs):
    """
    Build template context.

    Returns:
        dict: Context dictionary with:
            - page_title: Page title
            - table_metadata: JSON metadata for table
            - forms_metadata: JSON metadata for forms
            - add_btn_title: Add button text
            - has_add_perm: Whether add button is shown
            - has_export_perm: Whether export button is shown
            - has_upload_permission: Whether upload is allowed
            - display_frame: Whether to display frame
    """
    context = super().get_context_data(**kwargs)

    if self.request.GET.get("action_type"):
        return context

    table_obj = self.get_table_obj()

    context["page_title"] = self.page_title
    context["table_metadata"] = json.dumps(table_obj.get_table_metadata())
    context["forms_metadata"] = json.dumps(self.get_forms_metadata())
    context["add_btn_title"] = self.add_btn_title or "Add New"
    context["has_add_perm"] = self.display_add_button_check(self.request)
    context["has_export_perm"] = self.display_download_button_check(self.request)
    context["has_upload_permission"] = self.has_upload_perm(self.request)
    context["display_frame"] = self.display_frame(self.request)

    # Get table view context
    table_view_context = table_obj.get_context_data(context, **kwargs)
    context.update(table_view_context)

    # Get detail view context if needed
    view = self.get_request_view()
    if view == "detail":
        detail_object = self.get_detail_obj(table_obj)
        detail_view_context = detail_object.get_context_data(context, **kwargs)
        context.update(detail_view_context)

    return context
```

**Override Example**:

```python
def get_context_data(self, **kwargs):
    """Add custom context for template"""
    context = super().get_context_data(**kwargs)
    context['organization_name'] = self.request.user.organization.name
    context['show_analytics'] = self.request.user.has_perm('view_analytics')
    return context
```

---

## Complete Examples

### Example 1: Basic CRUD View

```python
# models.py
from django.db import models
from zango.apps.dynamic_models.models import DynamicModelBase

class ServiceType(DynamicModelBase):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
```

```python
# forms.py
from ...packages.crud.forms import BaseForm
from ...packages.crud.form_fields import ModelField
from .models import ServiceType

class ServiceTypeForm(BaseForm):
    name = ModelField(
        placeholder="Service Type Name",
        required=True,
        required_msg="Name is required"
    )
    code = ModelField(
        placeholder="Service Code",
        required=True,
        required_msg="Code is required",
        pattern="^[A-Z0-9_]+$",
        pattern_msg="Code must be uppercase letters, numbers, and underscores only"
    )
    description = ModelField(
        placeholder="Description",
        required=False
    )

    class Meta:
        model = ServiceType
        title = "Service Type"
        layout = "drawer-half"
        order = [
            ["name", "code"],
            ["description"]
        ]
```

```python
# tables.py
from ...packages.crud.table.base import ModelTable
from ...packages.crud.table.column import ModelCol, StringCol
from .models import ServiceType
from .forms import ServiceTypeForm

class ServiceTypeTable(ModelTable):
    id = ModelCol(display_as="ID", searchable=True, sortable=True)
    name = ModelCol(display_as="Name", searchable=True, sortable=True)
    code = ModelCol(display_as="Code", searchable=True, sortable=True)
    is_active = StringCol(display_as="Status", searchable=True, sortable=False)

    row_actions = [
        {
            "name": "Edit",
            "key": "edit",
            "description": "Edit service type",
            "type": "form",
            "form": ServiceTypeForm
        }
    ]

    def is_active_getval(self, obj):
        if obj.is_active:
            return '<span class="badge badge-success">Active</span>'
        return '<span class="badge badge-secondary">Inactive</span>'

    class Meta:
        model = ServiceType
        fields = ['id', 'name', 'code', 'is_active']
        row_selector = {}
```

```python
# views.py
from ...packages.crud.base import BaseCrudView
from .models import ServiceType
from .forms import ServiceTypeForm
from .tables import ServiceTypeTable

class ServiceTypeCrudView(BaseCrudView):
    page_title = "Service Types"
    add_btn_title = "Add Service Type"
    model = ServiceType
    form = ServiceTypeForm
    table = ServiceTypeTable
```

### Example 2: CRUD with Workflow and Detail Class

```python
# workflow.py
from ...packages.workflow.base.base import BaseWorkflow
from .models import Program

class ProgramWorkflow(BaseWorkflow):
    class Meta:
        model = Program
        on_create_status = "initiated"

        statuses = {
            "initiated": {"label": "Initiated", "color": "#6c757d"},
            "in_progress": {"label": "In Progress", "color": "#0d6efd"},
            "completed": {"label": "Completed", "color": "#198754"},
            "cancelled": {"label": "Cancelled", "color": "#dc3545"}
        }

        transitions = [
            {"name": "Start", "from_status": "initiated", "to_status": "in_progress"},
            {"name": "Complete", "from_status": "in_progress", "to_status": "completed"},
            {"name": "Cancel", "from_status": ["initiated", "in_progress"], "to_status": "cancelled"}
        ]
```

```python
# detail.py
from ...packages.crud.detail.base import BaseDetail

class ProgramDetail(BaseDetail):
    def get_sections(self, obj):
        return [
            {
                "title": "Program Information",
                "fields": ["name", "code", "description"],
            },
            {
                "title": "Dates",
                "fields": ["start_date", "end_date"],
            },
            {
                "title": "Status",
                "fields": ["status"],
            }
        ]
```

```python
# tables.py
from ...packages.crud.table.base import ModelTable
from ...packages.crud.table.column import ModelCol, StatusCol, WorkflowTransitionsCol
from .models import Program
from .forms import ProgramForm
from .detail import ProgramDetail

class ProgramTable(ModelTable):
    id = ModelCol(display_as="ID")
    name = ModelCol(display_as="Name", searchable=True, sortable=True)
    code = ModelCol(display_as="Code", searchable=True, sortable=True)
    status = StatusCol(display_as="Status")
    transitions = WorkflowTransitionsCol(display_as="Actions")

    row_actions = [
        {
            "name": "Edit",
            "key": "edit",
            "description": "Edit program",
            "type": "form",
            "form": ProgramForm
        }
    ]

    class Meta:
        model = Program
        fields = ['id', 'name', 'code']  # status/transitions are custom cols
        detail_class = ProgramDetail  # Configure detail class
        row_selector = {}
```

```python
# views.py
from ...packages.crud.base import BaseCrudView
from .models import Program
from .forms import ProgramForm
from .tables import ProgramTable
from .workflow import ProgramWorkflow

class ProgramCrudView(BaseCrudView):
    page_title = "Programs"
    add_btn_title = "Add Program"
    model = Program
    form = ProgramForm
    table = ProgramTable
    workflow = ProgramWorkflow
```

### Example 3: CRUD with Custom Permissions

```python
# views.py
from ...packages.crud.base import BaseCrudView
from zango.core.utils import get_current_role
from ..utils.policy_utils import check_role_policy
from .models import Program
from .forms import ProgramForm
from .tables import ProgramTable
from .workflow import ProgramWorkflow

class ProgramCrudView(BaseCrudView):
    page_title = "Programs"
    add_btn_title = "Add Program"
    model = Program
    form = ProgramForm
    table = ProgramTable
    workflow = ProgramWorkflow

    def display_add_button_check(self, request):
        """
        Only allow program creation for users with ProgramCreationPolicy
        """
        role = get_current_role()
        if role and role.name:
            return check_role_policy(role.name, 'ProgramCreationPolicy')
        return False

    def display_download_button_check(self, request):
        """
        Only allow export for Admin and Manager roles
        """
        role = get_current_role()
        if role and role.name:
            return role.name in ["Admin", "Manager"]
        return False

    def has_upload_perm(self, request):
        """
        Only allow bulk upload for Admin role
        """
        role = get_current_role()
        if role and role.name:
            return role.name == "Admin"
        return False
```

### Example 4: Custom Row Action Form Based on State

```python
# views.py
from ...packages.crud.base import BaseCrudView
from .models import Program
from .forms import ProgramForm, ProgramEditForm, ProgramRestrictedEditForm
from .tables import ProgramTable
from .workflow import ProgramWorkflow

class ProgramCrudView(BaseCrudView):
    page_title = "Programs"
    add_btn_title = "Add Program"
    model = Program
    form = ProgramForm
    table = ProgramTable
    workflow = ProgramWorkflow

    def get_row_action_form(self, obj_uuid, action_key, data=None, files=None, instance=None):
        """
        Use different edit form based on program status
        """
        if action_key == 'edit':
            if not instance:
                instance = self.model.objects.get(object_uuid=obj_uuid)

            # Get workflow status
            workflow_obj = self.get_workflow_obj(object_instance=instance)
            if workflow_obj:
                current_status, _ = workflow_obj.get_current_status()

                # Use restricted form for completed programs
                if current_status == 'completed':
                    return ProgramRestrictedEditForm(
                        data=data,
                        files=files,
                        instance=instance,
                        crud_view_instance=self
                    )

            # Use regular edit form
            return ProgramEditForm(
                data=data,
                files=files,
                instance=instance,
                crud_view_instance=self
            )

        # For other actions, use parent method
        return super().get_row_action_form(obj_uuid, action_key, data, files, instance)
```

---

## Best Practices

### 1. Always Define add_btn_title

Missing this attribute is the most common error:

```python
# ❌ Wrong - Missing add_btn_title
class MyCrudView(BaseCrudView):
    page_title = "My Model"
    model = MyModel
    form = MyForm
    table = MyTable

# ✅ Correct
class MyCrudView(BaseCrudView):
    page_title = "My Model"
    add_btn_title = "Add My Model"  # Required!
    model = MyModel
    form = MyForm
    table = MyTable
```

### 2. Configure Detail Class in Table Meta

Detail class should be configured in the table's Meta, not the view:

```python
# ❌ Wrong - No detail_class attribute on view
class MyCrudView(BaseCrudView):
    page_title = "My Model"
    add_btn_title = "Add"
    model = MyModel
    form = MyForm
    table = MyTable
    detail_class = MyDetail  # This doesn't work!

# ✅ Correct - Configure in table Meta
class MyTable(ModelTable):
    # ... columns ...

    class Meta:
        model = MyModel
        fields = ['id', 'name']
        detail_class = MyDetail  # Correct location
```

### 3. Use Permission Methods for Complex Logic

For complex permission logic, override check methods instead of only using policies:

```python
def display_add_button_check(self, request):
    """Complex business logic for add permission"""
    role = get_current_role()
    if not role:
        return False

    # Check policy
    if not check_role_policy(role.name, 'MyModelCreatePolicy'):
        return False

    # Additional business logic
    if request.user.organization.subscription_expired:
        return False

    if request.user.organization.record_count >= request.user.organization.max_records:
        return False

    return True
```

### 4. Keep Views Thin

Move business logic to models, forms, or services. Views should primarily coordinate:

```python
# ❌ Wrong - Too much logic in view
class ProgramCrudView(BaseCrudView):
    # ... attributes ...

    def get_form(self, data=None, files=None, instance=None):
        form = super().get_form(data, files, instance)
        # Complex business logic here...
        if data:
            # Lots of validation...
            # Database queries...
            # External API calls...
        return form

# ✅ Correct - Delegate to form/model/service
class ProgramCrudView(BaseCrudView):
    # ... attributes ...

    def get_form(self, data=None, files=None, instance=None):
        form = super().get_form(data, files, instance)
        # Simple coordination only
        form.organization = self.request.user.organization
        return form
```

### 5. Consistent Naming

Use consistent naming across all CRUD components:

```python
# ✅ Good naming convention
Model: Program
Form: ProgramForm
Table: ProgramTable
View: ProgramCrudView
Workflow: ProgramWorkflow
Detail: ProgramDetail
```

### 6. Document Permission Logic

If you override permission methods, document the logic:

```python
def display_add_button_check(self, request):
    """
    Control program creation permission.

    Requirements:
    - User must have ProgramCreationPolicy assigned to their role
    - Organization subscription must be active
    - Organization must not have reached record limit

    Returns:
        bool: True if user can create programs
    """
    # ... implementation ...
```

### 7. Test All Permission Scenarios

Test permission methods with different roles and conditions:

- User with no role
- User with role but no policy
- User with policy but business condition fails
- User with all permissions

---

## Troubleshooting

### Error: AttributeError: 'MyCrudView' object has no attribute 'add_btn_title'

**Problem**: Forgot to define `add_btn_title` in view.

**Solution**:
```python
class MyCrudView(BaseCrudView):
    page_title = "My Model"
    add_btn_title = "Add My Model"  # Add this!
    model = MyModel
    form = MyForm
    table = MyTable
```

### Add Button Not Showing

**Problem**: `display_add_button_check()` is returning False or policy not assigned.

**Debugging Steps**:

1. **Check policy assignment**:
   - Is policy synced from App Panel?
   - Is policy assigned to user's role?
   - Does policy include `"add"` feature?

2. **Check custom check method**:
```python
def display_add_button_check(self, request):
    """Debug version"""
    from zango.core.utils import get_current_role
    role = get_current_role()
    print(f"User role: {role}")  # Debug

    if role and role.name:
        result = check_role_policy(role.name, 'MyPolicy')
        print(f"Policy check result: {result}")  # Debug
        return result
    return False
```

3. **Check browser console** for JavaScript errors

### Export/Download Button Not Showing

**Problem**: `display_download_button_check()` is returning False or policy not assigned.

**Solution**: Same debugging steps as "Add Button Not Showing" above, but check `"download"` or `"export"` feature.

### Detail View Not Loading

**Problem**: Detail class not configured correctly.

**Solution**: Ensure `detail_class` is in table Meta, not view:

```python
# In tables.py
class MyTable(ModelTable):
    # ... columns ...

    class Meta:
        model = MyModel
        fields = ['id', 'name']
        detail_class = MyDetail  # Must be here, not in view!
```

### Workflow Not Working

**Problem**: Workflow not configured on view or table doesn't have StatusCol/WorkflowTransitionsCol.

**Solution**:

1. **Add workflow to view**:
```python
class MyCrudView(BaseCrudView):
    # ... other attributes ...
    workflow = MyWorkflow  # Add this
```

2. **Add workflow columns to table**:
```python
class MyTable(ModelTable):
    status = StatusCol(display_as="Status")
    transitions = WorkflowTransitionsCol(display_as="Actions")

    class Meta:
        model = MyModel
        fields = ['id', 'name']  # Don't include status/transitions
```

### 404 Not Found on CRUD URL

**Problem**: Module not registered or URLs not configured.

**Solution**:

1. **Check module is in `settings.json`**:
```json
{
    "app_routes": [
        "mymodule"
    ]
}
```

2. **Check `urls.py` exists and is configured**:
```python
# mymodule/urls.py
from django.urls import path
from .views import MyCrudView

urlpatterns = [
    path('my-model/', MyCrudView.as_view(), name='my_model_crud'),
]
```

3. **Restart server** after adding new modules

### Form Not Saving - No Errors

**Problem**: Form `save()` method not calling `super().save()` or not returning instance.

**Solution**:
```python
class MyForm(BaseForm):
    # ... fields ...

    def save(self, commit=True):
        instance = super().save(commit=False)  # Must call super()
        # ... custom logic ...
        if commit:
            instance.save()
        return instance  # Must return instance
```

### Row Action Permission Denied

**Problem**: `can_perform_row_action_<action_key>()` returning False in table.

**Solution**: Check table method and ensure it uses `self.user_role`:

```python
# In table
def can_perform_row_action_edit(self, request, obj):
    """Check if user can edit"""
    # ❌ Wrong - don't use get_current_role() in table
    # role = get_current_role()

    # ✅ Correct - use self.user_role
    if self.user_role:
        return check_role_policy(self.user_role.name, 'MyEditPolicy')
    return False
```

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

## Verification Checklist

After creating CRUD views, verify:

- [ ] View inherits from `BaseCrudView`
- [ ] View has `page_title` defined
- [ ] View has `add_btn_title` defined (REQUIRED)
- [ ] View references `model`, `form`, and `table`
- [ ] Workflow configured if using StatusCol/TagsCol
- [ ] Detail class configured in table Meta (if needed)
- [ ] Permission methods implemented if custom logic needed
- [ ] URLs registered in `urls.py`
- [ ] Module listed in `settings.json` `app_routes`
- [ ] Can access CRUD interface via browser
- [ ] Add button shows for authorized users
- [ ] Export button shows for authorized users
- [ ] Can create new records
- [ ] Can edit records via row actions
- [ ] Can view detail page
- [ ] Workflow transitions work (if applicable)
- [ ] Policies synced from App Panel

---

## Related Documentation

- **Forms**: `references/packages/crud/forms.md` - Form field types, validation, custom schema
- **Tables**: `references/packages/crud/tables.md` - Column types, row actions, custom display
- **Detail Views**: `references/packages/crud/detail.md` - Detail class, sections, custom rendering
- **Workflows**: `references/packages/workflow/workflow.md` - Status/tag management, transitions
- **Policies**: `references/core/policies.md` - Permission configuration, policy features
