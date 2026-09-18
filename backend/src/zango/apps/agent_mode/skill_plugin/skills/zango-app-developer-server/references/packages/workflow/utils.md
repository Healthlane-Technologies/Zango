# Workflow Utility Functions Reference

Utility functions for filtering records by workflow status and tags.

## Essential Imports

```python
from ...packages.workflow.base.utils import (
    filter_objects_by_workflow_status,
    filter_objects_by_workflow_tag,
    filter_object_uuids_by_workflow_status,
    filter_object_uuids_by_workflow_tag
)
```

---

## Table of Contents

1. [Overview](#overview)
2. [Filtering by Status](#filtering-by-status)
3. [Filtering by Tags](#filtering-by-tags)
4. [UUID vs QuerySet Functions](#uuid-vs-queryset-functions)
5. [Advanced Usage](#advanced-usage)
6. [Complete Examples](#complete-examples)
7. [Best Practices](#best-practices)

---

## Overview

Workflow utility functions allow you to filter records based on their current workflow state:
- **Status filtering** - Get records in specific status(es)
- **Tag filtering** - Get records with specific tag(s) enabled/disabled
- **UUID functions** - Get list of UUIDs matching criteria
- **QuerySet functions** - Get Django QuerySet of matching records

**Common Use Cases**:
- Display lists of records in specific status
- Count records by status for dashboards
- Filter records with specific tags enabled
- Build custom queries combining workflow and other criteria

---

## Filtering by Status

### filter_objects_by_workflow_status()

Get Django QuerySet of records filtered by workflow status.

**Function Signature**:

```python
def filter_objects_by_workflow_status(model_class, status=None):
    """
    Get actual model instances filtered by workflow status.

    Args:
        model_class: Django model class (e.g., Program, Patient)
        status: Status to filter by - can be string or list
                If None, returns all records with workflow states

    Returns:
        QuerySet: Django QuerySet of matching records
    """
```

**Examples**:

```python
from ...packages.workflow.base.utils import filter_objects_by_workflow_status
from .models import Program

# Get all active programs
active_programs = filter_objects_by_workflow_status(Program, status='active')

# Get programs in multiple statuses
programs = filter_objects_by_workflow_status(
    Program,
    status=['active', 'draft']
)

# Get all programs with any workflow status
all_programs = filter_objects_by_workflow_status(Program)

# Use like any Django QuerySet
active_count = filter_objects_by_workflow_status(Program, status='active').count()
active_names = filter_objects_by_workflow_status(Program, status='active').values_list('name', flat=True)
```

### filter_object_uuids_by_workflow_status()

Get list of UUIDs for records filtered by workflow status.

**Function Signature**:

```python
def filter_object_uuids_by_workflow_status(model_class, status=None):
    """
    Filter objects by workflow status and return their UUIDs.

    Args:
        model_class: Django model class (e.g., Program, Patient)
        status: Status to filter by - can be string or list
                If None, returns all UUIDs with workflow states

    Returns:
        list: List of UUIDs (as UUID objects)
    """
```

**Examples**:

```python
from ...packages.workflow.base.utils import filter_object_uuids_by_workflow_status
from .models import Program

# Get UUIDs of all active programs
active_uuids = filter_object_uuids_by_workflow_status(Program, status='active')

# Get UUIDs of programs in multiple statuses
uuids = filter_object_uuids_by_workflow_status(
    Program,
    status=['active', 'draft', 'pending']
)

# Use UUIDs in custom queries
Program.objects.filter(object_uuid__in=active_uuids, created_by=user)
```

---

## Filtering by Tags

### filter_objects_by_workflow_tag()

Get Django QuerySet of records filtered by workflow tag.

**Function Signature**:

```python
def filter_objects_by_workflow_tag(model_class, tag_name=None, tag_state='enabled'):
    """
    Get actual model instances filtered by workflow tag.

    Args:
        model_class: Django model class (e.g., Program, Patient)
        tag_name: Tag name to filter by - can be string or list
                  If None, returns all records with tags in specified state
        tag_state: 'enabled' or 'disabled' (default: 'enabled')

    Returns:
        QuerySet: Django QuerySet of matching records
    """
```

**Examples**:

```python
from ...packages.workflow.base.utils import filter_objects_by_workflow_tag
from .models import Program

# Get all programs marked as urgent
urgent_programs = filter_objects_by_workflow_tag(
    Program,
    tag_name='urgent',
    tag_state='enabled'
)

# Get programs with multiple tags enabled
flagged_programs = filter_objects_by_workflow_tag(
    Program,
    tag_name=['urgent', 'high_priority'],
    tag_state='enabled'
)

# Get programs where confidential tag is disabled
non_confidential = filter_objects_by_workflow_tag(
    Program,
    tag_name='confidential',
    tag_state='disabled'
)

# Get all programs with any tags enabled
all_tagged = filter_objects_by_workflow_tag(Program, tag_state='enabled')

# Use like any Django QuerySet
urgent_count = filter_objects_by_workflow_tag(
    Program,
    tag_name='urgent',
    tag_state='enabled'
).count()
```

### filter_object_uuids_by_workflow_tag()

Get list of UUIDs for records filtered by workflow tag.

**Function Signature**:

```python
def filter_object_uuids_by_workflow_tag(model_class, tag_name=None, tag_state='enabled'):
    """
    Filter objects by workflow tag and return their UUIDs.

    Args:
        model_class: Django model class (e.g., Program, Patient)
        tag_name: Tag name to filter by - can be string or list
                  If None, returns all UUIDs with tags in specified state
        tag_state: 'enabled' or 'disabled' (default: 'enabled')

    Returns:
        list: List of UUIDs (as UUID objects)
    """
```

**Examples**:

```python
from ...packages.workflow.base.utils import filter_object_uuids_by_workflow_tag
from .models import Program

# Get UUIDs of urgent programs
urgent_uuids = filter_object_uuids_by_workflow_tag(
    Program,
    tag_name='urgent',
    tag_state='enabled'
)

# Get UUIDs of programs with multiple tags
uuids = filter_object_uuids_by_workflow_tag(
    Program,
    tag_name=['urgent', 'confidential'],
    tag_state='enabled'
)

# Use UUIDs in custom queries
Program.objects.filter(object_uuid__in=urgent_uuids, organization=org)
```

---

## UUID vs QuerySet Functions

### When to Use UUID Functions

Use UUID functions when you need to:
- Combine workflow filtering with other complex queries
- Pass UUIDs to other functions/APIs
- Build custom QuerySets with additional filters

```python
# Get UUIDs of active programs
active_uuids = filter_object_uuids_by_workflow_status(Program, status='active')

# Use in custom query with additional filters
my_active_programs = Program.objects.filter(
    object_uuid__in=active_uuids,
    created_by=request.user,
    organization=org,
    start_date__gte=date.today()
)
```

### When to Use QuerySet Functions

Use QuerySet functions when you:
- Need records directly
- Want to use Django QuerySet methods (count, values, annotate, etc.)
- Don't need additional filtering

```python
# Get active programs directly
active_programs = filter_objects_by_workflow_status(Program, status='active')

# Use QuerySet methods
active_count = active_programs.count()
active_names = active_programs.values_list('name', flat=True)
recent_active = active_programs.filter(created_at__gte=date.today())
```

---

## Advanced Usage

### Combining Status and Tag Filters

```python
from ...packages.workflow.base.utils import (
    filter_objects_by_workflow_status,
    filter_object_uuids_by_workflow_tag
)
from .models import Program

# Get active programs that are also urgent
active_programs = filter_objects_by_workflow_status(Program, status='active')
urgent_uuids = filter_object_uuids_by_workflow_tag(Program, tag_name='urgent')

active_and_urgent = active_programs.filter(object_uuid__in=urgent_uuids)
```

### Using in Table get_table_data_queryset()

Filter table data by workflow state:

```python
# In tables.py
from ...packages.crud.table.base import ModelTable
from ...packages.workflow.base.utils import filter_object_uuids_by_workflow_status

class ProgramTable(ModelTable):
    # ... columns ...

    def get_table_data_queryset(self):
        """Show only active and draft programs in table"""
        queryset = super().get_table_data_queryset()

        # Filter by status
        allowed_uuids = filter_object_uuids_by_workflow_status(
            self.model,
            status=['active', 'draft']
        )

        return queryset.filter(object_uuid__in=allowed_uuids)
```

### Using in Detail View

```python
# In detail.py
from ...packages.crud.detail.base import BaseDetail
from ...packages.workflow.base.utils import filter_objects_by_workflow_status

class ProgramDetail(BaseDetail):
    def fetch_item_details(self):
        """Add stats about related programs"""
        data = super().fetch_item_details()

        obj_uuid = self.get_object_uuid()
        obj = self.get_object(object_uuid=obj_uuid)

        # Get related programs by status
        from ..program.models import Program
        related_active = filter_objects_by_workflow_status(
            Program,
            status='active'
        ).filter(parent_program=obj).count()

        related_draft = filter_objects_by_workflow_status(
            Program,
            status='draft'
        ).filter(parent_program=obj).count()

        data["related_programs"] = {
            "active": related_active,
            "draft": related_draft
        }

        return data
```

### Building Dashboard Stats

```python
# In views.py
from django.views.generic import TemplateView
from ...packages.workflow.base.utils import filter_objects_by_workflow_status
from .models import Program

class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get counts by status
        context['active_count'] = filter_objects_by_workflow_status(
            Program, status='active'
        ).count()

        context['draft_count'] = filter_objects_by_workflow_status(
            Program, status='draft'
        ).count()

        context['closed_count'] = filter_objects_by_workflow_status(
            Program, status='closed'
        ).count()

        # Get urgent programs
        from ...packages.workflow.base.utils import filter_objects_by_workflow_tag
        context['urgent_programs'] = filter_objects_by_workflow_tag(
            Program,
            tag_name='urgent',
            tag_state='enabled'
        )[:10]  # Top 10 urgent programs

        return context
```

---

## Complete Examples

### Example 1: Filtering in List View

```python
from django.views.generic import ListView
from ...packages.workflow.base.utils import filter_objects_by_workflow_status
from .models import Program

class ActiveProgramsListView(ListView):
    model = Program
    template_name = "programs/active_list.html"
    context_object_name = "programs"

    def get_queryset(self):
        """Get only active programs"""
        return filter_objects_by_workflow_status(Program, status='active')
```

### Example 2: Multiple Status Filter with Additional Criteria

```python
from ...packages.workflow.base.utils import filter_objects_by_workflow_status
from .models import Program

def get_my_programs(user, organization):
    """Get user's programs in active or draft status"""
    # Get programs in specific statuses
    programs = filter_objects_by_workflow_status(
        Program,
        status=['active', 'draft']
    )

    # Add additional filters
    my_programs = programs.filter(
        created_by=user,
        organization=organization
    )

    return my_programs
```

### Example 3: Tag-Based Filtering

```python
from ...packages.workflow.base.utils import filter_objects_by_workflow_tag
from .models import Program

def get_priority_programs(organization):
    """Get all high-priority and urgent programs"""
    # Get programs with either tag enabled
    priority_programs = filter_objects_by_workflow_tag(
        Program,
        tag_name=['urgent', 'high_priority'],
        tag_state='enabled'
    )

    # Filter by organization
    return priority_programs.filter(organization=organization)
```

### Example 4: Combining Status and Tags

```python
from ...packages.workflow.base.utils import (
    filter_objects_by_workflow_status,
    filter_object_uuids_by_workflow_tag
)
from .models import Program

def get_active_urgent_programs():
    """Get active programs marked as urgent"""
    # Get active programs
    active_programs = filter_objects_by_workflow_status(Program, status='active')

    # Get UUIDs of urgent programs
    urgent_uuids = filter_object_uuids_by_workflow_tag(
        Program,
        tag_name='urgent',
        tag_state='enabled'
    )

    # Combine both filters
    return active_programs.filter(object_uuid__in=urgent_uuids)
```

### Example 5: Dashboard with Multiple Filters

```python
from django.views.generic import TemplateView
from ...packages.workflow.base.utils import (
    filter_objects_by_workflow_status,
    filter_objects_by_workflow_tag
)
from .models import Program, Audit

class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Program stats
        context['programs'] = {
            'active': filter_objects_by_workflow_status(Program, status='active').count(),
            'draft': filter_objects_by_workflow_status(Program, status='draft').count(),
            'closed': filter_objects_by_workflow_status(Program, status='closed').count(),
            'urgent': filter_objects_by_workflow_tag(
                Program, tag_name='urgent', tag_state='enabled'
            ).count()
        }

        # Audit stats
        context['audits'] = {
            'open': filter_objects_by_workflow_status(Audit, status='open').count(),
            'closed': filter_objects_by_workflow_status(Audit, status='closed').count()
        }

        # Recent urgent programs
        context['recent_urgent'] = filter_objects_by_workflow_tag(
            Program, tag_name='urgent', tag_state='enabled'
        ).order_by('-created_at')[:5]

        return context
```

---

## Best Practices

### 1. Use QuerySet Functions When Possible

```python
# ✅ Good - Direct QuerySet
programs = filter_objects_by_workflow_status(Program, status='active')
count = programs.count()

# ❌ Avoid - Extra step with UUIDs
uuids = filter_object_uuids_by_workflow_status(Program, status='active')
programs = Program.objects.filter(object_uuid__in=uuids)
count = programs.count()
```

### 2. Cache Results for Multiple Uses

```python
# ✅ Good - Cache the queryset
active_programs = filter_objects_by_workflow_status(Program, status='active')
count = active_programs.count()
names = active_programs.values_list('name', flat=True)
recent = active_programs.filter(created_at__gte=date.today())

# ❌ Avoid - Multiple DB hits
count = filter_objects_by_workflow_status(Program, status='active').count()
names = filter_objects_by_workflow_status(Program, status='active').values_list('name', flat=True)
```

### 3. Use UUIDs for Complex Queries

```python
# ✅ Good - Complex query combining multiple filters
active_uuids = filter_object_uuids_by_workflow_status(Program, status='active')
urgent_uuids = filter_object_uuids_by_workflow_tag(Program, tag_name='urgent')

programs = Program.objects.filter(
    object_uuid__in=active_uuids,
    organization=org,
    created_by=user
).filter(object_uuid__in=urgent_uuids)
```

### 4. Use list for Multiple Statuses/Tags

```python
# ✅ Good - List for multiple values
programs = filter_objects_by_workflow_status(
    Program,
    status=['active', 'draft', 'pending']
)

tagged = filter_objects_by_workflow_tag(
    Program,
    tag_name=['urgent', 'high_priority']
)
```

### 5. Check for Empty Results

```python
# ✅ Good - Check before using
active_programs = filter_objects_by_workflow_status(Program, status='active')
if active_programs.exists():
    # Process programs
    for program in active_programs:
        process_program(program)
else:
    # Handle no results
    logger.info("No active programs found")
```

---

## Related Documentation

- **Statuses**: `statuses.md` - Status definitions
- **Tags**: `tags.md` - Tag definitions and usage
- **Transitions**: `transitions.md` - Status and tag transitions
- **Tables**: `../crud/tables/core.md` - StatusCol and TagsCol for search
