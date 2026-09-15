# Zango Module Reference

Complete guide for creating and registering Zango modules.

## What Are Modules?

**Modules** are individual organizational spaces where application code is structured and organized.

**Key Concepts**:
- Each module represents a logical feature or domain area of your application
- Modules contain models, views, forms, tables, templates, and business logic
- Modules must be registered in `settings.json` to be recognized by the application
- Each module has its own URL routing configuration

---

## Module Organization Patterns

### Flat Structure (Simple Applications)

```
backend/
├── app/              # Core app module (required)
├── products/         # Product management
├── customers/        # Customer management
└── orders/           # Order management
```

### Hierarchical Structure (Complex Applications)

```
backend/
├── app/              # Core app module (required)
├── masters/          # Master data modules
│   ├── geography/    # Geographic data
│   └── product/      # Product catalog
├── members/          # User/member modules
│   ├── employees/    # Employee management
│   └── vendor/       # Vendor management
├── program/          # Program management
└── reports/          # Reporting module
```

---

## Module Folder Structure

### Basic Module Structure

```
backend/
└── mymodule/              # Your module folder
    ├── __init__.py        # Required: Makes it a Python package
    ├── models.py          # Database models (optional)
    ├── views.py           # View logic (optional)
    ├── urls.py            # URL routing (optional, if exposing URLs)
    ├── forms.py           # Form definitions (optional)
    ├── tables.py          # Table definitions (optional)
    ├── workflow.py        # Workflow definitions (optional)
    ├── tasks.py           # Background tasks (optional)
    ├── policies.json      # Access policies (optional)
    └── apis/              # REST API endpoints (optional subfolder)
```

### Required Files

- **`__init__.py`** - Makes the directory a Python package (can be empty)

### Common Files

- **`models.py`** - Database model definitions
- **`views.py`** - View classes and logic
- **`urls.py`** - URL patterns (if module exposes URLs)
- **`forms.py`** - Form classes
- **`tables.py`** - Table classes for list views

### Optional Files

- **`workflow.py`** - Workflow state management
- **`tasks.py`** - Celery background tasks
- **`policies.json`** - Role-based access policies
- **`detail.py`** - Custom detail views
- **`apis/`** - REST API endpoints subfolder

---

## Creating a New Module

### Step 1: Create Module Folder

Create the module directory in your application's backend folder:

```bash
workspace/
└── myapp/
    └── backend/
        └── patients/          # New module
            └── __init__.py    # Required: empty file
```

**Important**: Always create an `__init__.py` file to make it a valid Python package.

### Step 2: Create urls.py (If Exposing URLs)

If your module needs URL endpoints, create `urls.py`:

```python
from django.urls import path
from .views import MyView

urlpatterns = [
    path('my-endpoint/', MyView.as_view()),
]
```

**When to Skip urls.py**:
- Utility modules (shared helpers)
- Modules that only contain models used by other modules
- Modules with no public endpoints

**Examples of modules without URLs**:
- `utils` - Shared utility functions
- `helpers` - Helper classes
- `mixins` - Reusable mixins

---

## Registering Modules in settings.json

Every module must be registered in `settings.json`, even if it doesn't expose URLs.

### Step 1: Add to "modules" Array

Open `workspace/myapp/settings.json` and add your module:

```json
{
    "version": "1.0.0",
    "app_name": "myapp",
    "zango_version": ">=0.6.0",
    "modules": [
        {
            "name": "app",
            "path": "backend.app"
        },
        {
            "name": "patients",
            "path": "backend.patients"
        }
    ],
    "package_routes": [],
    "app_routes": []
}
```

**Module Registration Format**:
- **`name`**: Unique identifier for the module (used in routing)
- **`path`**: Python import path to the module (use dots, not slashes)

**Examples**:

Flat structure:
```json
{
    "name": "products",
    "path": "backend.products"
}
```

Hierarchical structure:
```json
{
    "name": "geography",
    "path": "backend.masters.geography"
}
```

```json
{
    "name": "employees",
    "path": "backend.members.employees"
}
```

### Step 2: Add to "app_routes" Array (If Exposing URLs)

Only add modules with URL endpoints to `app_routes`:

```json
{
    "app_routes": [
        {
            "module": "app",
            "re_path": "^",
            "url": "urls"
        },
        {
            "module": "patients",
            "re_path": "^patients/",
            "url": "urls"
        }
    ]
}
```

**Route Configuration**:
- **`module`**: Must match the `name` from modules array
- **`re_path`**: Regular expression for URL path (Django regex pattern)
- **`url`**: The urls file to use (typically `"urls"`)

**URL Path Examples**:

```json
{
    "module": "products",
    "re_path": "^products/",
    "url": "urls"
}
```
Accessible at: `http://myapp.local:8000/products/`

```json
{
    "module": "geography",
    "re_path": "^geography/",
    "url": "urls"
}
```
Accessible at: `http://myapp.local:8000/geography/`

```json
{
    "module": "program_documents",
    "re_path": "^program-documents/",
    "url": "urls"
}
```
Accessible at: `http://myapp.local:8000/program-documents/`

---

## Complete Example: Creating "Products" Module

### Step 1: Create Folder Structure

```bash
backend/
└── products/
    ├── __init__.py
    ├── models.py
    ├── views.py
    └── urls.py
```

### Step 2: Create Basic urls.py

```python
# backend/products/urls.py
from django.urls import path

urlpatterns = [
    # Add your URL patterns here
]
```

### Step 3: Register in settings.json

```json
{
    "modules": [
        {
            "name": "app",
            "path": "backend.app"
        },
        {
            "name": "products",
            "path": "backend.products"
        }
    ],
    "app_routes": [
        {
            "module": "app",
            "re_path": "^",
            "url": "urls"
        },
        {
            "module": "products",
            "re_path": "^products/",
            "url": "urls"
        }
    ]
}
```

### Step 4: Access Module

Module URLs are now accessible at: `http://myapp.local:8000/products/`

---

## Import Paths in Zango

### Understanding Relative Imports

In Zango, **all imports use relative paths** based on where your file is located. The number of dots depends on your file's location in the directory tree.

### How Relative Imports Work

Each dot (`.`) means "go up one directory level":
- `.` = current directory
- `..` = parent directory (go up 1 level)
- `...` = grandparent directory (go up 2 levels)
- `....` = great-grandparent directory (go up 3 levels)
- And so on...

### Project Structure Example

```
workspace/
└── myapp/                      # App root
    ├── backend/                # Your modules
    │   ├── patients/           # Flat module
    │   │   ├── models.py
    │   │   └── forms.py
    │   └── masters/            # Nested modules
    │       └── geography/
    │           └── models.py
    └── packages/               # Installed packages
        └── crud/
            └── forms.py
```

### Import Examples by File Location

**From `backend/patients/forms.py` (flat module, 2 levels deep):**

```python
# Same directory: patients/
from .models import Patient                          # . = patients/

# Sibling module: backend/doctors/
from ..doctors.models import Doctor                  # .. = backend/

# Nested module: backend/masters/geography/
from ..masters.geography.models import Country       # .. = backend/

# Packages: packages/crud/
from ...packages.crud.forms import BaseForm         # ... = myapp/ (app root)
```

**From `backend/masters/geography/models.py` (nested module, 3 levels deep):**

```python
# Same directory: masters/geography/
from .utils import some_function                     # . = geography/

# Parent module: masters/products/
from ..products.models import Product                # .. = masters/

# Sibling module: backend/patients/
from ...patients.models import Patient               # ... = backend/

# Packages: packages/crud/
from ....packages.crud.forms import BaseForm        # .... = myapp/ (app root)
```

### The Rule

**Count the directory levels from your file to the app root (workspace/myapp/), then add one more dot.**

From `backend/patients/forms.py`:
- Current: `forms.py`
- Go up 1: `patients/`
- Go up 2: `backend/`
- Go up 3: `myapp/` ← app root
- To access `packages/`: use `...packages`

From `backend/masters/geography/models.py`:
- Current: `models.py`
- Go up 1: `geography/`
- Go up 2: `masters/`
- Go up 3: `backend/`
- Go up 4: `myapp/` ← app root
- To access `packages/`: use `....packages`

### Common Import Patterns

```python
# Same module
from .models import MyModel              # Current directory

# Sibling modules (same depth)
from ..other_module.models import Other  # Up 1, then down

# Nested modules
from ..folder.submodule.models import X  # Up 1, then down path

# Packages (count dots to app root + packages)
from ...packages.crud.forms import BaseForm           # Flat module
from ....packages.crud.forms import BaseForm          # Nested module
```

### Why This Matters

1. **Multi-tenancy**: Each tenant has isolated schemas. Relative imports ensure correct resolution.
2. **Portability**: Modules work regardless of app name or location.
3. **Dynamic packages**: Packages can be added/removed without breaking code.

### Common Mistakes

❌ **Absolute imports** (don't work in Zango):
```python
from backend.patients.models import Patient
from myapp.backend.patients.models import Patient
from packages.crud.forms import BaseForm
```

✅ **Relative imports** (correct):
```python
from .models import Patient                    # Same directory
from ..other_module.models import Other        # Parent then down
from ...packages.crud.forms import BaseForm    # Up to root, then down
```

### Quick Tip

When writing imports, count the directory levels from your current file up to the common parent of both files, then navigate down to the target.

---

## Naming Conventions

### Folder Names (Module Directories)

- Use lowercase
- Use underscores for multi-word names
- Examples: `products`, `customer_orders`, `program_documents`

### Module "name" in settings.json

- Use lowercase
- Use underscores
- Should match or relate to folder name
- Examples: `"products"`, `"customer_orders"`, `"program_documents"`

### URL "re_path" in app_routes

- Use lowercase
- Use **hyphens** (not underscores) for multi-word paths
- Examples: `"^products/"`, `"^customer-orders/"`, `"^program-documents/"`

**Example Mapping**:
```
Folder:        customer_orders/
Module name:   "customer_orders"
URL path:      "^customer-orders/"
```

---

## Special Modules

### The "app" Module

- **Required**: Every application has an `app` module by default
- **Path**: `backend.app`
- **Route**: `^` (root path)
- **Purpose**: Contains core application logic, home views, and base templates
- **Order**: Should always be registered **first** in both `modules` and `app_routes`

```json
{
    "modules": [
        {
            "name": "app",
            "path": "backend.app"
        }
    ],
    "app_routes": [
        {
            "module": "app",
            "re_path": "^",
            "url": "urls"
        }
    ]
}
```

### The "utils" Module

- **Common Pattern**: For shared utilities
- **Path**: `backend.utils`
- **Routes**: Typically doesn't have routes (no entry in `app_routes`)
- **urls.py**: Not required
- **Purpose**: Helper functions, utilities, shared code used by other modules

```json
{
    "modules": [
        {
            "name": "app",
            "path": "backend.app"
        },
        {
            "name": "utils",
            "path": "backend.utils"
        }
    ],
    "app_routes": [
        {
            "module": "app",
            "re_path": "^",
            "url": "urls"
        }
        // No route for utils - it doesn't expose URLs
    ]
}
```

**Key Point**: Modules are registered in the `modules` array even if they don't have URLs. Only modules with URL endpoints need an entry in `app_routes`.

---

## Verification Checklist

After creating and registering a module, verify:

- [ ] Module folder exists in `backend/`
- [ ] `__init__.py` file exists in module folder
- [ ] Module is registered in `settings.json` under `modules` array
- [ ] Module name and path are correct in registration
- [ ] If module exposes URLs, it has an entry in `app_routes` array
- [ ] If module exposes URLs, `urls.py` file exists
- [ ] URL path uses hyphens (not underscores)
- [ ] "app" module is listed first in both arrays
- [ ] No syntax errors in settings.json (valid JSON)

---

## Common Patterns

### Pattern 1: Simple Feature Module

```
backend/patients/
├── __init__.py
├── models.py
├── views.py
└── urls.py
```

```json
{
    "modules": [
        {"name": "app", "path": "backend.app"},
        {"name": "patients", "path": "backend.patients"}
    ],
    "app_routes": [
        {"module": "app", "re_path": "^", "url": "urls"},
        {"module": "patients", "re_path": "^patients/", "url": "urls"}
    ]
}
```

### Pattern 2: Hierarchical Modules

```
backend/masters/
├── __init__.py
├── geography/
│   ├── __init__.py
│   ├── models.py
│   └── urls.py
└── products/
    ├── __init__.py
    ├── models.py
    └── urls.py
```

```json
{
    "modules": [
        {"name": "app", "path": "backend.app"},
        {"name": "geography", "path": "backend.masters.geography"},
        {"name": "products", "path": "backend.masters.products"}
    ],
    "app_routes": [
        {"module": "app", "re_path": "^", "url": "urls"},
        {"name": "geography", "re_path": "^geography/", "url": "urls"},
        {"name": "products", "re_path": "^products/", "url": "urls"}
    ]
}
```

### Pattern 3: Utility Module (No URLs)

```
backend/utils/
├── __init__.py
├── helpers.py
└── validators.py
```

```json
{
    "modules": [
        {"name": "app", "path": "backend.app"},
        {"name": "utils", "path": "backend.utils"}
    ],
    "app_routes": [
        {"module": "app", "re_path": "^", "url": "urls"}
        // No route for utils - it's for internal use only
    ]
}
```

---

## Best Practices

1. **Always create `__init__.py`** - Required for Python to recognize as a package
2. **Register modules immediately** - Add to settings.json right after creating folder
3. **Follow naming conventions** - Underscores in code, hyphens in URLs
4. **"app" module first** - Always list first in both arrays
5. **One module per feature** - Keep modules focused on a single responsibility
6. **Use hierarchical structure** - For larger applications with many modules
7. **Document module purpose** - Add docstrings in `__init__.py`
8. **Consistent organization** - All modules should follow same file structure

---

## Troubleshooting

### Module Not Found Error

**Problem**: `ModuleNotFoundError: No module named 'backend.mymodule'`

**Solutions**:
- Check `__init__.py` exists in module folder
- Verify path in settings.json matches folder structure
- Use dots, not slashes: `"backend.mymodule"` not `"backend/mymodule"`

### 404 Not Found on Module URL

**Problem**: Module URL returns 404

**Solutions**:
- Check module is in `app_routes` array
- Verify `re_path` pattern is correct
- Ensure `urls.py` exists in module
- Check `module` name matches `modules` array entry

### Invalid JSON in settings.json

**Problem**: Application won't start, JSON parse error

**Solutions**:
- Validate JSON syntax (no trailing commas)
- Use double quotes, not single quotes
- Check all brackets and braces are balanced
- Use a JSON validator tool
