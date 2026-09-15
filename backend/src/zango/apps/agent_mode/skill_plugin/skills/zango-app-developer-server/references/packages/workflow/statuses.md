# Workflow Statuses Reference

## Essential Imports

```python
from ...packages.workflow.base.engine import WorkflowBase
```

---

## Basic Workflow Structure

```python
from ...packages.workflow.base.engine import WorkflowBase

class MyWorkflow(WorkflowBase):
    status_transitions = []  # Transitions defined here

    class Meta:
        on_create_status = "draft"  # Initial status for new records
        statuses = {}  # All possible statuses
```

---

## Defining Statuses

Define all statuses in `Meta.statuses`:

```python
class Meta:
    on_create_status = "draft"
    statuses = {
        "draft": {
            "color": "gray",
            "label": "Draft",
        },
        "active": {
            "color": "green",
            "label": "Active",
        },
        "closed": {
            "color": "blue",
            "label": "Closed",
        }
    }
```

**Status Properties**:
- **color**: Badge color (gray, green, blue, orange, red, purple, yellow)
- **label**: Display name shown to users

---

## Available Colors

| Color | Typical Use |
|-------|-------------|
| `gray` | Draft, Inactive, Archived |
| `green` | Active, Approved, Completed |
| `blue` | In Progress, Under Review, Closed |
| `orange` | Pending, Warning |
| `red` | Rejected, Failed, Critical |
| `purple` | Special status |
| `yellow` | Caution, On Hold |

---

## Common Status Patterns

### Three-State Lifecycle

```python
statuses = {
    "draft": {"color": "gray", "label": "Draft"},
    "active": {"color": "green", "label": "Active"},
    "closed": {"color": "blue", "label": "Closed"}
}
```

### Approval Workflow

```python
statuses = {
    "draft": {"color": "gray", "label": "Draft"},
    "pending": {"color": "yellow", "label": "Pending Approval"},
    "approved": {"color": "green", "label": "Approved"},
    "rejected": {"color": "red", "label": "Rejected"}
}
```

### Project Lifecycle

```python
statuses = {
    "planning": {"color": "gray", "label": "Planning"},
    "active": {"color": "blue", "label": "Active"},
    "on_hold": {"color": "yellow", "label": "On Hold"},
    "completed": {"color": "green", "label": "Completed"},
    "cancelled": {"color": "red", "label": "Cancelled"}
}
```

---

## Integrating with View

Add the workflow to your `BaseCrudView`:

```python
from ...packages.crud.base import BaseCrudView
from .models import MyModel
from .forms import MyForm
from .tables import MyTable
from .workflow import MyWorkflow

class MyCrudView(BaseCrudView):
    page_title = "My Records"
    add_btn_title = "Add Record"
    model = MyModel
    form = MyForm
    table = MyTable
    workflow = MyWorkflow  # Add workflow reference
```

---

## Best Practices

1. **Choose meaningful status names** - Use lowercase with underscores (e.g., `pending_approval`)
2. **Pick appropriate colors** - Colors should match user expectations
3. **Set initial status** - Always define `on_create_status`
4. **Keep it simple** - Start with 3-4 statuses, add more only if needed
5. **Document status meaning** - Use clear, descriptive labels
