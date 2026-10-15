# Workflow Transitions Reference

## Simple Transitions

Simple transitions change status without collecting additional data.

### Simple Transition Structure

```python
status_transitions = [
    {
        "name": "draft_to_active",                    # Unique identifier
        "display_name": "Activate",                   # Button text
        "description": "Activate this record",        # Tooltip/help text
        "from": "draft",                              # Source status
        "to": "active",                               # Target status
        "confirmation_message": "Are you sure?",      # Confirmation prompt
        "roles": ["Admin", "Manager"]                 # Optional: restrict by role
    }
]
```

**Transition Properties**:
- **name**: Unique identifier (use `from_to` convention)
- **display_name**: Text shown on button
- **description**: Tooltip or help text
- **from**: Source status
- **to**: Target status
- **confirmation_message**: User confirmation prompt
- **roles** (optional): List of roles allowed to perform transition

### Complete Simple Transition Example

```python
from ...packages.workflow.base.engine import WorkflowBase

class PatientWorkflow(WorkflowBase):
    status_transitions = [
        {
            "name": "draft_to_active",
            "display_name": "Activate",
            "description": "Activate this patient record",
            "from": "draft",
            "to": "active",
            "confirmation_message": "Are you sure you want to activate this patient?"
        },
        {
            "name": "active_to_inactive",
            "display_name": "Deactivate",
            "description": "Deactivate this patient record",
            "from": "active",
            "to": "inactive",
            "confirmation_message": "Are you sure you want to deactivate?"
        },
        {
            "name": "inactive_to_active",
            "display_name": "Reactivate",
            "description": "Reactivate this patient record",
            "from": "inactive",
            "to": "active",
            "confirmation_message": "Reactivate this patient?"
        }
    ]

    class Meta:
        on_create_status = "draft"
        statuses = {
            "draft": {"color": "gray", "label": "Draft"},
            "active": {"color": "green", "label": "Active"},
            "inactive": {"color": "red", "label": "Inactive"}
        }
```

---

## Form-Based Transitions

Form-based transitions collect additional data during the status change.

### Step 1: Create Transition Form

```python
from django import forms
from ...packages.crud.forms import BaseSimpleForm

class ClosureForm(BaseSimpleForm):
    closure_notes = forms.CharField(label="Closure Notes", required=True)
    closure_date = forms.DateField(label="Closure Date", required=True)

    def __init__(self, *args, **kwargs):
        super(ClosureForm, self).__init__(*args, **kwargs)
        self.Meta.title = "Close Record"

        # Configure textarea widget
        self.declared_fields['closure_notes'].extra_ui_schema = {
            "ui:widget": "TextareaFieldWidget",
            "ui:options": {"rows": 4}
        }

    def save(self):
        object_instance = self.initial.get("object_instance")
        object_instance.closure_notes = self.cleaned_data.get('closure_notes')
        object_instance.closure_date = self.cleaned_data.get('closure_date')
        object_instance.save()
        return object_instance

    class Meta:
        title = "Close Record"
        layout = "drawer-half"
        order = [
            ["closure_notes"],
            ["closure_date"]
        ]
```

**Critical Points**:
- Inherit from `BaseSimpleForm` (NOT `BaseForm`)
- Access object via `self.initial.get("object_instance")`
- Save changes to the object instance
- Return the object instance

### Step 2: Add Form to Transition

```python
{
    "name": "active_to_closed",
    "display_name": "Close",
    "description": "Close this record",
    "from": "active",
    "to": "closed",
    "form": ClosureForm,  # Add form reference
    "roles": ["Admin"]
}
```

### Complete Form-Based Transition Example

```python
from django import forms
from ...packages.workflow.base.engine import WorkflowBase
from ...packages.crud.forms import BaseSimpleForm

# Transition form
class ApprovalForm(BaseSimpleForm):
    approval_notes = forms.CharField(label="Approval Notes", required=True)
    approved_by = forms.CharField(label="Approved By", required=True)

    def __init__(self, *args, **kwargs):
        super(ApprovalForm, self).__init__(*args, **kwargs)
        self.Meta.title = "Approve Record"

        self.declared_fields['approval_notes'].extra_ui_schema = {
            "ui:widget": "TextareaFieldWidget",
            "ui:options": {"rows": 3}
        }

    def save(self):
        object_instance = self.initial.get("object_instance")
        object_instance.approval_notes = self.cleaned_data.get('approval_notes')
        object_instance.approved_by = self.cleaned_data.get('approved_by')
        object_instance.save()
        return object_instance

    class Meta:
        title = "Approve Record"
        layout = "drawer-half"
        order = [
            ["approval_notes"],
            ["approved_by"]
        ]

# Workflow
class MyWorkflow(WorkflowBase):
    status_transitions = [
        {
            "name": "draft_to_pending",
            "display_name": "Submit for Approval",
            "description": "Submit for approval",
            "from": "draft",
            "to": "pending",
            "confirmation_message": "Submit this record for approval?"
        },
        {
            "name": "pending_to_approved",
            "display_name": "Approve",
            "description": "Approve this record",
            "from": "pending",
            "to": "approved",
            "form": ApprovalForm,
            "roles": ["Manager", "Admin"]
        }
    ]

    class Meta:
        on_create_status = "draft"
        statuses = {
            "draft": {"color": "gray", "label": "Draft"},
            "pending": {"color": "yellow", "label": "Pending Approval"},
            "approved": {"color": "green", "label": "Approved"}
        }
```

---

## Common Transition Patterns

### Bidirectional Transitions

```python
status_transitions = [
    {
        "name": "draft_to_active",
        "display_name": "Activate",
        "from": "draft",
        "to": "active"
    },
    {
        "name": "active_to_draft",
        "display_name": "Move to Draft",
        "from": "active",
        "to": "draft"
    }
]
```

### Multi-Path Transitions

```python
status_transitions = [
    {
        "name": "pending_to_approved",
        "display_name": "Approve",
        "from": "pending",
        "to": "approved",
        "roles": ["Manager"]
    },
    {
        "name": "pending_to_rejected",
        "display_name": "Reject",
        "from": "pending",
        "to": "rejected",
        "roles": ["Manager"]
    },
    {
        "name": "pending_to_draft",
        "display_name": "Return to Draft",
        "from": "pending",
        "to": "draft"
    }
]
```

---

## Best Practices

1. **Naming convention** - Use `from_to` format (e.g., `draft_to_active`)
2. **Clear button text** - Use action verbs ("Activate", "Approve", "Close")
3. **Confirmation messages** - Always provide clear confirmation prompts
4. **Role restrictions** - Limit sensitive transitions to specific roles
5. **Form transitions** - Use when additional data is needed
6. **Bidirectional paths** - Allow reversing transitions when appropriate

---

## Troubleshooting

### Transition Buttons Not Showing

**Problem**: Current object status doesn't match transition "from"

**Solution**: Check object's current status matches transition source

### Form Not Saving

**Problem**: Not accessing object_instance correctly

**Solution**:
```python
def save(self):
    object_instance = self.initial.get("object_instance")
    # Update fields
    object_instance.save()
    return object_instance
```

### Role Restriction Not Working

**Problem**: Roles not configured or user doesn't have role

**Solution**: Verify role names match exactly and user has assigned role
