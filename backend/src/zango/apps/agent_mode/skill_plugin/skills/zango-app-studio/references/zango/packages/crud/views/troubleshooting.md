# Zango CRUD Views — Troubleshooting

> Best practices, troubleshooting and the verification checklist for `BaseCrudView`. Start at [core.md](core.md).

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

- **Forms**: `references/packages/crud/forms/core.md` - Form field types, validation, custom schema
- **Tables**: `references/packages/crud/tables/core.md` - Column types, row actions, custom display
- **Detail Views**: `references/packages/crud/detail.md` - Detail class, sections, custom rendering
- **Workflows**: `references/packages/workflow/workflow.md` - Status/tag management, transitions
- **Policies**: `references/core/policies.md` - Permission configuration, policy features
