# Zango CRUD Views — Method Reference

> Method reference and worked examples for `BaseCrudView`. Start at [core.md](core.md).

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
