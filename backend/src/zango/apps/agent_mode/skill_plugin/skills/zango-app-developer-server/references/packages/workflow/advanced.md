# Workflow Advanced Features

## Condition Methods

Condition methods check if a transition is allowed before executing.

### Method Signature

```python
def <transition_name>_condition(self, request, object_instance, **kwargs):
    """
    Check if transition can be performed.

    Returns:
        tuple: (allowed: bool, message: str)
    """
    # Validation logic
    return True, "Transition allowed"
```

### Example Conditions

```python
def draft_to_active_condition(self, request, object_instance, **kwargs):
    """Check if record can be activated"""
    # Check required fields
    if not object_instance.name:
        return False, "Name is required before activation"

    if not object_instance.email:
        return False, "Email is required before activation"

    # Check business rules
    if not object_instance.is_valid_for_activation():
        return False, "Record must meet all validation criteria"

    return True, "Transition allowed"

def active_to_closed_condition(self, request, object_instance, **kwargs):
    """Check if record can be closed"""
    # Check dependencies
    if object_instance.has_pending_tasks():
        return False, "Cannot close - pending tasks exist"

    return True, "Ready to close"
```

---

## Done Methods

Done methods execute logic after a transition completes successfully.

### Method Signature

```python
def <transition_name>_done(self, request, object_instance, transaction_obj):
    """
    Execute logic after transition completes.

    Args:
        request: HTTP request object
        object_instance: The model instance that transitioned
        transaction_obj: The workflow transaction record for this transition
    """
    # Post-transition logic
    pass
```

### Example Done Methods

```python
def draft_to_active_done(self, request, object_instance, transaction_obj):
    """Execute after activation"""
    from django.utils import timezone

    # Update activation metadata
    object_instance.activated_at = timezone.now()
    object_instance.activated_by = request.user
    object_instance.save()

    # Send notification
    send_activation_notification(object_instance)

    # Log the event
    log_status_change(object_instance, "draft", "active", request.user)

def active_to_closed_done(self, request, object_instance, transaction_obj):
    """Execute after closure"""
    from django.utils import timezone

    # Update closure metadata
    object_instance.closed_at = timezone.now()
    object_instance.closed_by = request.user
    object_instance.save()

    # Trigger cleanup tasks
    cleanup_related_records(object_instance)

    # Send closure notifications
    notify_stakeholders(object_instance)
```

---

## Complete Workflow Example

Here's a comprehensive example combining all features:

```python
from django import forms
from django.utils import timezone
from ...packages.workflow.base.engine import WorkflowBase
from ...packages.crud.forms import BaseSimpleForm

# Transition forms
class ApprovalForm(BaseSimpleForm):
    approval_notes = forms.CharField(label="Approval Notes", required=True)

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
        object_instance.save()
        return object_instance

    class Meta:
        title = "Approve Record"
        layout = "drawer-half"
        order = [["approval_notes"]]

class RejectionForm(BaseSimpleForm):
    rejection_reason = forms.CharField(label="Rejection Reason", required=True)

    def __init__(self, *args, **kwargs):
        super(RejectionForm, self).__init__(*args, **kwargs)
        self.Meta.title = "Reject Record"

        self.declared_fields['rejection_reason'].extra_ui_schema = {
            "ui:widget": "TextareaFieldWidget",
            "ui:options": {"rows": 3}
        }

    def save(self):
        object_instance = self.initial.get("object_instance")
        object_instance.rejection_reason = self.cleaned_data.get('rejection_reason')
        object_instance.save()
        return object_instance

    class Meta:
        title = "Reject Record"
        layout = "drawer-half"
        order = [["rejection_reason"]]

# Workflow
class PatientWorkflow(WorkflowBase):
    status_transitions = [
        {
            "name": "draft_to_pending",
            "display_name": "Submit for Approval",
            "description": "Submit patient record for approval",
            "from": "draft",
            "to": "pending",
            "confirmation_message": "Submit for approval?"
        },
        {
            "name": "pending_to_approved",
            "display_name": "Approve",
            "description": "Approve patient record",
            "from": "pending",
            "to": "approved",
            "form": ApprovalForm,
            "roles": ["Manager", "Admin"]
        },
        {
            "name": "pending_to_rejected",
            "display_name": "Reject",
            "description": "Reject patient record",
            "from": "pending",
            "to": "rejected",
            "form": RejectionForm,
            "roles": ["Manager", "Admin"]
        },
        {
            "name": "rejected_to_draft",
            "display_name": "Return to Draft",
            "description": "Return to draft for corrections",
            "from": "rejected",
            "to": "draft"
        },
        {
            "name": "approved_to_active",
            "display_name": "Activate",
            "description": "Activate approved patient",
            "from": "approved",
            "to": "active",
            "roles": ["Admin"]
        }
    ]

    # Condition methods
    def draft_to_pending_condition(self, request, object_instance, **kwargs):
        """Check if ready for submission"""
        if not object_instance.name:
            return False, "Patient name is required"

        if not object_instance.email and not object_instance.phone:
            return False, "Either email or phone is required"

        return True, "Ready for submission"

    def pending_to_approved_condition(self, request, object_instance, **kwargs):
        """Check if can be approved"""
        if not object_instance.is_complete():
            return False, "All required fields must be filled"

        return True, "Ready for approval"

    # Done methods
    def pending_to_approved_done(self, request, object_instance, transaction_obj):
        """Execute after approval"""
        object_instance.approved_at = timezone.now()
        object_instance.approved_by = request.user
        object_instance.save()

        # Send approval notification
        send_approval_email(object_instance)

    def pending_to_rejected_done(self, request, object_instance, transaction_obj):
        """Execute after rejection"""
        object_instance.rejected_at = timezone.now()
        object_instance.rejected_by = request.user
        object_instance.save()

        # Send rejection notification
        send_rejection_email(object_instance)

    def approved_to_active_done(self, request, object_instance, transaction_obj):
        """Execute after activation"""
        object_instance.activated_at = timezone.now()
        object_instance.activated_by = request.user
        object_instance.save()

        # Trigger activation processes
        activate_patient_services(object_instance)

    class Meta:
        on_create_status = "draft"
        statuses = {
            "draft": {"color": "gray", "label": "Draft"},
            "pending": {"color": "yellow", "label": "Pending Approval"},
            "approved": {"color": "green", "label": "Approved"},
            "rejected": {"color": "red", "label": "Rejected"},
            "active": {"color": "blue", "label": "Active"}
        }
```

---

## Common Workflow Patterns

### Approval Workflow with Rejection Path

```python
status_transitions = [
    {"name": "draft_to_pending", "from": "draft", "to": "pending"},
    {"name": "pending_to_approved", "from": "pending", "to": "approved", "roles": ["Manager"]},
    {"name": "pending_to_rejected", "from": "pending", "to": "rejected", "roles": ["Manager"]},
    {"name": "rejected_to_draft", "from": "rejected", "to": "draft"}
]
```

### Progressive Status Flow

```python
status_transitions = [
    {"name": "draft_to_review", "from": "draft", "to": "review"},
    {"name": "review_to_testing", "from": "review", "to": "testing"},
    {"name": "testing_to_approved", "from": "testing", "to": "approved"},
    {"name": "testing_to_review", "from": "testing", "to": "review"}  # Rollback
]
```

### Lifecycle with Terminal States

```python
status_transitions = [
    {"name": "draft_to_active", "from": "draft", "to": "active"},
    {"name": "active_to_completed", "from": "active", "to": "completed"},
    {"name": "active_to_cancelled", "from": "active", "to": "cancelled"},
    # Completed and cancelled are terminal - no transitions out
]
```

---

## Best Practices

1. **Validate in conditions** - Check all requirements before allowing transitions
2. **Keep done methods focused** - Execute only necessary post-transition logic
3. **Return clear messages** - Provide helpful error messages from conditions
4. **Log important transitions** - Track who performed critical status changes
5. **Send notifications** - Inform stakeholders of status changes
6. **Update metadata** - Track timestamps and users for each transition
7. **Handle errors gracefully** - Wrap done methods in try-except if needed

---

## Troubleshooting

### Condition Method Not Being Called

**Problem**: Method name doesn't match transition name

**Solution**: Use exact format `<transition_name>_condition`

### Done Method Not Executing

**Problem**: Transition failed or method name incorrect

**Solution**: Check condition passes and method name matches `<transition_name>_done`

### Transition Failing Silently

**Problem**: Condition returning single value instead of tuple

**Solution**:
```python
# Wrong
return False

# Correct
return False, "Error message"
```

### Object Not Saving Changes

**Problem**: Forgetting to call `obj.save()` in done method

**Solution**:
```python
def draft_to_active_done(self, request, object_instance, transaction_obj):
    object_instance.activated_at = timezone.now()
    object_instance.save()  # Don't forget this!
```

---

## System Transitions

System transitions are automatic transitions that execute programmatically without user interaction. They're used for automated workflow steps.

### Defining System Transitions

Mark a transition as system-only with `is_manual: False`:

```python
status_transitions = [
    {
        "name": "on_approval_auto_activate",
        "display_name": "Auto-Activate",
        "description": "Automatically activate after approval",
        "from": "approved",
        "to": "active",
        "is_manual": False  # System transition - not shown in UI
    },
    {
        "name": "approved_to_active",
        "display_name": "Activate",
        "description": "Manually activate approved record",
        "from": "approved",
        "to": "active",
        "is_manual": True  # Default - shown in UI
    }
]
```

**System Transition Properties**:
- `is_manual: False` - Marks transition as system-only
- Not shown in UI buttons
- Can only be executed programmatically
- Cannot be executed via API/UI clicks
- Still respects condition methods
- Still executes done methods

### Executing System Transitions

System transitions can only be executed programmatically:

```python
def approved_to_active_done(self, request, object_instance, transaction_obj):
    """After manual activation, trigger auto transitions"""
    # Check if there are follow-up system transitions
    if should_auto_transition(object_instance):
        # Execute system transition
        workflow_obj = self.get_workflow_object(object_instance)
        workflow_obj.execute_transition("on_approval_auto_activate", allow_system=True)
```

### Use Cases for System Transitions

**1. Automated Status Progression**

```python
status_transitions = [
    {
        "name": "pending_to_reviewing",
        "display_name": "Start Review",
        "from": "pending",
        "to": "reviewing"
    },
    {
        "name": "reviewing_to_approved",
        "display_name": "Approve",
        "from": "reviewing",
        "to": "approved"
    },
    {
        "name": "auto_activate_after_approval",
        "display_name": "Auto-Activate",
        "from": "approved",
        "to": "active",
        "is_manual": False  # System only
    }
]

def reviewing_to_approved_done(self, request, object_instance, transaction_obj):
    """After approval, automatically activate"""
    # Trigger system transition
    self.execute_transition("auto_activate_after_approval", allow_system=True)
```

**2. Scheduled/Timed Transitions**

```python
# In a celery task
from myapp.models import Program
from myapp.workflow import ProgramWorkflow

def auto_close_expired_programs():
    """Celery task to auto-close programs past end date"""
    from datetime import date

    expired_programs = Program.objects.filter(
        end_date__lt=date.today(),
        status='active'
    )

    for program in expired_programs:
        workflow = ProgramWorkflow(object_instance=program)
        # Execute system transition
        workflow.execute_transition("auto_close_expired", allow_system=True)
```

**3. Conditional Auto-Transitions**

```python
def active_to_suspended_done(self, request, object_instance, transaction_obj):
    """After suspension, check if should auto-reactivate"""
    # Check conditions
    if object_instance.suspension_reason == "temporary":
        # Schedule auto-reactivation
        schedule_auto_transition(
            object_instance,
            "auto_reactivate_after_suspension",
            delay_days=30
        )
```

### System Transition Best Practices

1. **Clear naming** - Use `auto_` prefix for system transitions
2. **Documentation** - Document when/why system transitions execute
3. **Logging** - Log all system transitions for audit trail
4. **Error handling** - Wrap system transitions in try-except
5. **Conditions** - Still use condition methods for validation

```python
# ✅ Good - Clear naming and error handling
def approved_to_active_done(self, request, object_instance, transaction_obj):
    """After approval, automatically activate if eligible"""
    try:
        # Check condition
        if object_instance.is_eligible_for_auto_activation():
            # Execute system transition
            success, message = self.execute_transition(
                "auto_activate_after_approval",
                allow_system=True
            )
            if success:
                logger.info(f"Auto-activated {object_instance}: {message}")
            else:
                logger.warning(f"Failed to auto-activate {object_instance}: {message}")
    except Exception as e:
        logger.error(f"Error in auto-activation: {e}")
```

---

## Summary

**Workflow Checklist**:
- [ ] Workflow inherits from `WorkflowBase`
- [ ] Meta.on_create_status defined
- [ ] All statuses defined with color and label
- [ ] Transitions have name, display_name, from, to
- [ ] Transition forms inherit from `BaseSimpleForm`
- [ ] Condition methods return (bool, str) tuples (or just bool)
- [ ] Done methods execute necessary logic
- [ ] Workflow integrated in view
- [ ] Transitions appear in UI
- [ ] Status changes work correctly
- [ ] System transitions marked with `is_manual: False` if needed
