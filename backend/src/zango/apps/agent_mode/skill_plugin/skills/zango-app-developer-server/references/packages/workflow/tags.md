# Workflow Tags Reference

Tags provide a secondary classification system for records, independent of status. Tags can be enabled/disabled dynamically to flag records for various purposes.

## What Are Tags?

Tags are boolean flags that can be toggled on/off for records, independent of workflow status.

**Common Use Cases**:
- **Priority flags** - Mark records as "urgent", "high_priority"
- **Feature flags** - Mark records as "featured", "promoted"
- **Process flags** - Mark records as "needs_review", "pending_approval"
- **Category flags** - Mark records as "confidential", "public"
- **Temporary markers** - Mark records as "archived", "flagged"

**Key Differences from Status**:
- Status is singular (one status at a time)
- Tags are multiple (many tags can be enabled simultaneously)
- Status changes follow defined transitions
- Tags can be enabled/disabled independently

---

## Table of Contents

1. [Defining Tags](#defining-tags)
2. [Tag Transitions](#tag-transitions)
3. [Tag Display](#tag-display)
4. [Tag Permissions](#tag-permissions)
5. [Tag Conditions](#tag-conditions)
6. [Tag Done Methods](#tag-done-methods)
7. [Form-Based Tag Transitions](#form-based-tag-transitions)
8. [Complete Examples](#complete-examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Defining Tags

Tags are defined in the workflow's `Meta.tags`:

```python
from ...packages.workflow.base.engine import WorkflowBase

class ProgramWorkflow(WorkflowBase):
    class Meta:
        # ... statuses ...

        tags = [
            ("urgent", "Urgent"),
            ("high_priority", "High Priority"),
            ("needs_review", "Needs Review"),
            ("confidential", "Confidential")
        ]
```

**Tag Format**: `(key, label)`
- **key**: Internal identifier (lowercase, underscores)
- **label**: Display name shown to users

---

## Tag Transitions

Tag transitions define how tags can be enabled or disabled with optional forms, confirmation messages, and role restrictions.

### Basic Tag Transition

```python
class ProgramWorkflow(WorkflowBase):
    tag_transitions = [
        {
            "name": "urgent",
            "enabled": {
                "confirmation_message": "Mark this program as urgent?",
                "roles": ["Manager", "Admin"]
            },
            "disabled": {
                "confirmation_message": "Remove urgent flag?",
                "roles": ["Manager", "Admin"]
            }
        }
    ]

    class Meta:
        # ... statuses ...
        tags = [("urgent", "Urgent")]
```

**Tag Transition Properties**:
- **name**: Tag key (must match tag in Meta.tags)
- **enabled**: Configuration for enabling the tag
  - `confirmation_message`: User confirmation prompt
  - `roles`: List of roles allowed to enable
  - `form`: Optional form for collecting data (see below)
- **disabled**: Configuration for disabling the tag
  - `confirmation_message`: User confirmation prompt
  - `roles`: List of roles allowed to disable
  - `form`: Optional form for collecting data

---

## Tag Display

Tags are automatically displayed in the CRUD interface using `TagsCol`:

```python
# In tables.py
from ...packages.crud.table.base import ModelTable
from ...packages.crud.table.column import ModelCol, TagsCol

class ProgramTable(ModelTable):
    id = ModelCol(display_as="ID")
    name = ModelCol(display_as="Name")
    tags = TagsCol(display_as="Tags")  # Auto-displays enabled tags

    class Meta:
        model = Program
        fields = ['id', 'name']  # Don't include 'tags' - it's a custom column
```

**TagsCol Features**:
- Automatically displays all enabled tags for the record
- Tags shown as comma-separated list
- Auto-integrates with workflow's Meta.tags
- Searchable by tag name

---

## Tag Permissions

Control who can enable/disable tags using role restrictions:

### Role-Based Tag Control

```python
tag_transitions = [
    {
        "name": "confidential",
        "enabled": {
            "confirmation_message": "Mark as confidential?",
            "roles": ["Admin"]  # Only Admin can enable
        },
        "disabled": {
            "confirmation_message": "Remove confidential flag?",
            "roles": ["Admin", "Manager"]  # Admin and Manager can disable
        }
    }
]
```

### Asymmetric Permissions

Different roles for enabling vs disabling:

```python
tag_transitions = [
    {
        "name": "needs_review",
        "enabled": {
            "roles": ["User", "Manager", "Admin"]  # Anyone can flag for review
        },
        "disabled": {
            "roles": ["Manager", "Admin"]  # Only Manager/Admin can clear flag
        }
    }
]
```

---

## Tag Conditions

Condition methods control whether a tag can be enabled/disabled based on business logic.

### Method Signature

```python
def <tag_name>_enabled_condition(self, request, object_instance, **kwargs):
    """Check if tag can be enabled"""
    # Validation logic
    return True  # or False

def <tag_name>_disabled_condition(self, request, object_instance, **kwargs):
    """Check if tag can be disabled"""
    # Validation logic
    return True  # or False
```

### Example Tag Conditions

```python
class ProgramWorkflow(WorkflowBase):
    tag_transitions = [
        {
            "name": "urgent",
            "enabled": {
                "confirmation_message": "Mark as urgent?",
                "roles": ["Manager", "Admin"]
            },
            "disabled": {
                "confirmation_message": "Remove urgent flag?",
                "roles": ["Manager", "Admin"]
            }
        },
        {
            "name": "confidential",
            "enabled": {
                "confirmation_message": "Mark as confidential?",
                "roles": ["Admin"]
            },
            "disabled": {
                "confirmation_message": "Remove confidential flag?",
                "roles": ["Admin"]
            }
        }
    ]

    def urgent_enabled_condition(self, request, object_instance, **kwargs):
        """Only active programs can be marked urgent"""
        current_status, _ = self.get_current_status()
        if current_status != "active":
            return False
        return True

    def urgent_disabled_condition(self, request, object_instance, **kwargs):
        """Can always remove urgent flag"""
        return True

    def confidential_enabled_condition(self, request, object_instance, **kwargs):
        """Check if program has sensitive data before marking confidential"""
        if not object_instance.has_sensitive_data():
            return False
        return True

    class Meta:
        # ... statuses ...
        tags = [
            ("urgent", "Urgent"),
            ("confidential", "Confidential")
        ]
```

---

## Tag Done Methods

Done methods execute logic after a tag is successfully enabled or disabled.

### Method Signature

```python
def <tag_name>_enabled_done(self, request, object_instance, transaction_obj, **kwargs):
    """Execute after tag is enabled"""
    pass

def <tag_name>_disabled_done(self, request, object_instance, transaction_obj, **kwargs):
    """Execute after tag is disabled"""
    pass
```

### Example Tag Done Methods

```python
class ProgramWorkflow(WorkflowBase):
    tag_transitions = [
        {
            "name": "urgent",
            "enabled": {"confirmation_message": "Mark as urgent?"},
            "disabled": {"confirmation_message": "Remove urgent flag?"}
        }
    ]

    def urgent_enabled_done(self, request, object_instance, transaction_obj, **kwargs):
        """Execute when urgent tag is enabled"""
        from django.utils import timezone

        # Update timestamp
        object_instance.marked_urgent_at = timezone.now()
        object_instance.marked_urgent_by = request.user
        object_instance.save()

        # Send notifications
        send_urgent_notification(object_instance)

        # Log the event
        log_tag_change(object_instance, "urgent", "enabled", request.user)

    def urgent_disabled_done(self, request, object_instance, transaction_obj, **kwargs):
        """Execute when urgent tag is disabled"""
        # Clear timestamp
        object_instance.marked_urgent_at = None
        object_instance.marked_urgent_by = None
        object_instance.save()

        # Log the event
        log_tag_change(object_instance, "urgent", "disabled", request.user)

    class Meta:
        # ... statuses ...
        tags = [("urgent", "Urgent")]
```

---

## Form-Based Tag Transitions

Collect additional information when enabling/disabling tags.

### Step 1: Create Tag Form

```python
from django import forms
from ...packages.crud.forms import BaseSimpleForm

class UrgentForm(BaseSimpleForm):
    urgent_reason = forms.CharField(label="Reason for Urgency", required=True)
    escalation_level = forms.ChoiceField(
        label="Escalation Level",
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High")
        ],
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(UrgentForm, self).__init__(*args, **kwargs)
        self.Meta.title = "Mark as Urgent"

        self.declared_fields['urgent_reason'].extra_ui_schema = {
            "ui:widget": "TextareaFieldWidget",
            "ui:options": {"rows": 3}
        }

    def save(self):
        object_instance = self.initial.get("object_instance")
        object_instance.urgent_reason = self.cleaned_data.get('urgent_reason')
        object_instance.escalation_level = self.cleaned_data.get('escalation_level')
        object_instance.save()
        return object_instance

    class Meta:
        title = "Mark as Urgent"
        layout = "drawer-half"
        order = [
            ["urgent_reason"],
            ["escalation_level"]
        ]
```

### Step 2: Add Form to Tag Transition

```python
tag_transitions = [
    {
        "name": "urgent",
        "enabled": {
            "confirmation_message": "Mark this program as urgent?",
            "form": UrgentForm,  # Form when enabling
            "roles": ["Manager", "Admin"]
        },
        "disabled": {
            "confirmation_message": "Remove urgent flag?",
            # No form when disabling
            "roles": ["Manager", "Admin"]
        }
    }
]
```

### Complete Form-Based Tag Example

```python
from django import forms
from ...packages.workflow.base.engine import WorkflowBase
from ...packages.crud.forms import BaseSimpleForm

# Form for enabling confidential tag
class ConfidentialForm(BaseSimpleForm):
    confidential_reason = forms.CharField(label="Reason for Confidentiality", required=True)
    access_level = forms.ChoiceField(
        label="Access Level",
        choices=[
            ("restricted", "Restricted"),
            ("classified", "Classified"),
            ("top_secret", "Top Secret")
        ],
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(ConfidentialForm, self).__init__(*args, **kwargs)
        self.Meta.title = "Mark as Confidential"

        self.declared_fields['confidential_reason'].extra_ui_schema = {
            "ui:widget": "TextareaFieldWidget",
            "ui:options": {"rows": 3}
        }

    def save(self):
        object_instance = self.initial.get("object_instance")
        object_instance.confidential_reason = self.cleaned_data.get('confidential_reason')
        object_instance.access_level = self.cleaned_data.get('access_level')
        object_instance.save()
        return object_instance

    class Meta:
        title = "Mark as Confidential"
        layout = "drawer-half"
        order = [
            ["confidential_reason"],
            ["access_level"]
        ]

# Workflow with form-based tags
class ProgramWorkflow(WorkflowBase):
    tag_transitions = [
        {
            "name": "urgent",
            "enabled": {
                "confirmation_message": "Mark as urgent?",
                "roles": ["Manager", "Admin"]
            },
            "disabled": {
                "confirmation_message": "Remove urgent flag?",
                "roles": ["Manager", "Admin"]
            }
        },
        {
            "name": "confidential",
            "enabled": {
                "confirmation_message": "Mark as confidential?",
                "form": ConfidentialForm,
                "roles": ["Admin"]
            },
            "disabled": {
                "confirmation_message": "Remove confidential flag?",
                "roles": ["Admin"]
            }
        }
    ]

    def confidential_enabled_done(self, request, object_instance, transaction_obj, **kwargs):
        """Execute after marking confidential"""
        from django.utils import timezone

        object_instance.marked_confidential_at = timezone.now()
        object_instance.marked_confidential_by = request.user
        object_instance.save()

        # Send notification to security team
        notify_security_team(object_instance)

    def confidential_disabled_done(self, request, object_instance, transaction_obj, **kwargs):
        """Execute after removing confidential flag"""
        object_instance.marked_confidential_at = None
        object_instance.marked_confidential_by = None
        object_instance.access_level = None
        object_instance.save()

    class Meta:
        on_create_status = "draft"
        statuses = {
            "draft": {"color": "gray", "label": "Draft"},
            "active": {"color": "green", "label": "Active"}
        }
        tags = [
            ("urgent", "Urgent"),
            ("confidential", "Confidential")
        ]
```

---

## Complete Examples

### Example 1: Simple Tags

```python
from ...packages.workflow.base.engine import WorkflowBase

class ProgramWorkflow(WorkflowBase):
    status_transitions = [
        {
            "name": "draft_to_active",
            "display_name": "Activate",
            "from": "draft",
            "to": "active"
        }
    ]

    tag_transitions = [
        {
            "name": "featured",
            "enabled": {
                "confirmation_message": "Feature this program?",
                "roles": ["Admin"]
            },
            "disabled": {
                "confirmation_message": "Unfeature this program?",
                "roles": ["Admin"]
            }
        },
        {
            "name": "archived",
            "enabled": {
                "confirmation_message": "Archive this program?",
                "roles": ["Admin", "Manager"]
            },
            "disabled": {
                "confirmation_message": "Unarchive this program?",
                "roles": ["Admin", "Manager"]
            }
        }
    ]

    class Meta:
        on_create_status = "draft"
        statuses = {
            "draft": {"color": "gray", "label": "Draft"},
            "active": {"color": "green", "label": "Active"}
        }
        tags = [
            ("featured", "Featured"),
            ("archived", "Archived")
        ]
```

### Example 2: Tags with Conditions and Done Methods

```python
from ...packages.workflow.base.engine import WorkflowBase
from django.utils import timezone

class ProgramWorkflow(WorkflowBase):
    status_transitions = [
        {
            "name": "draft_to_active",
            "display_name": "Activate",
            "from": "draft",
            "to": "active"
        }
    ]

    tag_transitions = [
        {
            "name": "urgent",
            "enabled": {
                "confirmation_message": "Mark as urgent?",
                "roles": ["Manager", "Admin"]
            },
            "disabled": {
                "confirmation_message": "Remove urgent flag?",
                "roles": ["Manager", "Admin"]
            }
        },
        {
            "name": "needs_review",
            "enabled": {
                "confirmation_message": "Flag for review?",
                "roles": ["User", "Manager", "Admin"]
            },
            "disabled": {
                "confirmation_message": "Clear review flag?",
                "roles": ["Manager", "Admin"]
            }
        }
    ]

    # Tag conditions
    def urgent_enabled_condition(self, request, object_instance, **kwargs):
        """Only active programs can be urgent"""
        current_status, _ = self.get_current_status()
        return current_status == "active"

    def needs_review_enabled_condition(self, request, object_instance, **kwargs):
        """Can only flag for review if not already urgent"""
        from ...packages.workflow.base.models import WorkflowTransaction

        # Check if urgent tag is enabled
        last_urgent_transaction = WorkflowTransaction.objects.filter(
            transition_type="tag",
            transition_name="urgent",
            obj_uuid=object_instance.object_uuid
        ).order_by('-created_at').first()

        if last_urgent_transaction and last_urgent_transaction.to_state == "enabled":
            return False  # Already urgent, don't need review flag
        return True

    # Tag done methods
    def urgent_enabled_done(self, request, object_instance, transaction_obj, **kwargs):
        """Execute when urgent tag enabled"""
        object_instance.marked_urgent_at = timezone.now()
        object_instance.save()
        send_urgent_notification(object_instance)

    def urgent_disabled_done(self, request, object_instance, transaction_obj, **kwargs):
        """Execute when urgent tag disabled"""
        object_instance.marked_urgent_at = None
        object_instance.save()

    def needs_review_enabled_done(self, request, object_instance, transaction_obj, **kwargs):
        """Execute when needs_review tag enabled"""
        notify_reviewers(object_instance)

    class Meta:
        on_create_status = "draft"
        statuses = {
            "draft": {"color": "gray", "label": "Draft"},
            "active": {"color": "green", "label": "Active"}
        }
        tags = [
            ("urgent", "Urgent"),
            ("needs_review", "Needs Review")
        ]
```

---

## Best Practices

### 1. Use Clear Tag Names

```python
# ✅ Good - Clear and specific
tags = [
    ("high_priority", "High Priority"),
    ("needs_review", "Needs Review"),
    ("confidential", "Confidential")
]

# ❌ Avoid - Vague or unclear
tags = [
    ("flag1", "Flag 1"),
    ("temp", "Temp"),
    ("misc", "Misc")
]
```

### 2. Provide Confirmation Messages

Always include confirmation messages for clarity:

```python
# ✅ Good
tag_transitions = [
    {
        "name": "urgent",
        "enabled": {
            "confirmation_message": "Mark this program as urgent? This will notify all stakeholders."
        },
        "disabled": {
            "confirmation_message": "Remove urgent flag? This will stop urgent notifications."
        }
    }
]
```

### 3. Use Tags for Multiple Classifications

Tags excel when records need multiple simultaneous flags:

```python
# A program can be both urgent AND confidential
tags = [
    ("urgent", "Urgent"),
    ("confidential", "Confidential"),
    ("needs_review", "Needs Review"),
    ("featured", "Featured")
]
```

### 4. Combine Tags with Status

Use status for lifecycle, tags for classification:

```python
# Status: Where is it in the lifecycle?
statuses = {
    "draft": {"color": "gray", "label": "Draft"},
    "active": {"color": "green", "label": "Active"},
    "closed": {"color": "blue", "label": "Closed"}
}

# Tags: What special attributes does it have?
tags = [
    ("urgent", "Urgent"),
    ("high_priority", "High Priority"),
    ("archived", "Archived")
]
```

### 5. Document Tag Behavior

Add docstrings to tag condition and done methods:

```python
def urgent_enabled_condition(self, request, object_instance, **kwargs):
    """
    Check if program can be marked urgent.

    Requirements:
    - Program must be in 'active' status
    - Program must have assigned team members

    Returns:
        bool: True if tag can be enabled
    """
    current_status, _ = self.get_current_status()
    return current_status == "active" and object_instance.has_team_members()
```

---

## Troubleshooting

### Tags Not Appearing in UI

**Problem**: TagsCol not added to table or workflow not configured.

**Solution**:

```python
# 1. Add TagsCol to table
class MyTable(ModelTable):
    tags = TagsCol(display_as="Tags")

    class Meta:
        model = MyModel
        fields = ['id', 'name']  # Don't include 'tags'

# 2. Add workflow to view
class MyCrudView(BaseCrudView):
    workflow = MyWorkflow  # Must configure workflow

# 3. Define tags in workflow Meta
class MyWorkflow(WorkflowBase):
    class Meta:
        tags = [("urgent", "Urgent")]  # Must define tags
```

### Tag Enable/Disable Buttons Not Showing

**Problem**: No tag_transitions defined or role restrictions.

**Solution**:

```python
# Define tag transitions
tag_transitions = [
    {
        "name": "urgent",
        "enabled": {
            "confirmation_message": "Mark as urgent?",
            # "roles": ["Admin"]  # Remove role restriction or ensure user has role
        },
        "disabled": {
            "confirmation_message": "Remove urgent flag?"
        }
    }
]
```

### Tag Condition Not Being Called

**Problem**: Method name doesn't match pattern.

**Solution**: Use exact format `<tag_name>_enabled_condition` or `<tag_name>_disabled_condition`:

```python
# ❌ Wrong
def urgent_condition(self, ...):
    pass

# ✅ Correct
def urgent_enabled_condition(self, ...):
    pass

def urgent_disabled_condition(self, ...):
    pass
```

### Tag Done Method Not Executing

**Problem**: Method name doesn't match pattern or tag transition failed.

**Solution**: Use exact format `<tag_name>_enabled_done` or `<tag_name>_disabled_done`:

```python
# ❌ Wrong
def urgent_done(self, ...):
    pass

# ✅ Correct
def urgent_enabled_done(self, ...):
    pass

def urgent_disabled_done(self, ...):
    pass
```

### Form Data Not Saving

**Problem**: Not accessing object_instance correctly in form save().

**Solution**:

```python
def save(self):
    object_instance = self.initial.get("object_instance")
    # Update fields
    object_instance.field = self.cleaned_data.get('field')
    object_instance.save()
    return object_instance
```

---

## Related Documentation

- **Statuses**: `statuses.md` - Status definitions and lifecycle
- **Transitions**: `transitions.md` - Status transitions
- **Advanced**: `advanced.md` - Condition and done methods
- **Utils**: `utils.md` - Utility functions for filtering by tags
- **Tables**: `../crud/tables.md` - TagsCol column type
