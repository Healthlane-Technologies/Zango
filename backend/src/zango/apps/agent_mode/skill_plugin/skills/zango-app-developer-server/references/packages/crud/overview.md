# Zango CRUD Package - Overview

Complete guide for building CRUD (Create, Read, Update, Delete) interfaces using Zango's CRUD package.

## What is the CRUD Package?

The Zango CRUD package provides a powerful framework for creating data management interfaces with minimal code.

**Key Benefits**:
- Rapid development of data management interfaces
- Consistent UI/UX across the application
- Built-in pagination, search, and sorting
- Automatic form validation and error handling
- Customizable actions and permissions

---

## CRUD Architecture

The CRUD pattern consists of **three main components**:

```
┌─────────────────────────────────────────┐
│         BaseCrudView (views.py)         │
│  Orchestrates the entire CRUD interface │
└───────────┬────────────────┬────────────┘
            │                │
     ┌──────▼──────┐  ┌─────▼──────┐
     │  BaseForm   │  │ ModelTable │
     │ (forms.py)  │  │(tables.py) │
     └──────┬──────┘  └─────┬──────┘
            │                │
     ┌──────▼────────────────▼──────┐
     │      Model (models.py)        │
     │    Data Structure Definition  │
     └───────────────────────────────┘
```

1. **Forms** (`forms.py`) - Define how data is input and validated
2. **Tables** (`tables.py`) - Define how data is displayed in list views
3. **Views** (`views.py`) - Connect forms and tables to create complete CRUD interfaces

---

## Quick Start

For detailed documentation on each component, see:

- [Forms Reference](forms/core.md) - BaseForm, field types, validation, and layouts (worked examples: [forms/examples.md](forms/examples.md))
- [Tables Reference](tables/core.md) - ModelTable, columns, row actions, and search (advanced patterns: [tables/advanced.md](tables/advanced.md))
- [Views Reference](views/core.md) - BaseCrudView, integration, and URL configuration (method reference: [views/reference.md](views/reference.md); troubleshooting: [views/troubleshooting.md](views/troubleshooting.md))

---

## After Creating a CRUD View

After you've created your CRUD view (Model, Form, Table, View, URLs), you need to **configure it in AppBuilder** to make it accessible via the AppBuilder frontend.

### Understanding CRUD View URLs

Your CRUD view URL is composed of:
1. **Module route** (in `settings.json` → `app_routes`) - e.g., `^patients/`
2. **View route** (in module's `urls.py`) - e.g., `patients/`
3. **Final CRUD view URL** = `/patients/patients/`

**Example:**
```python
# settings.json
{
  "app_routes": [
    {
      "re_path": "^patients/",
      "module": "patients",
      "url": "urls"
    }
  ]
}

# patients/urls.py
urlpatterns = [
    path('patients/', PatientsCrudView.as_view(), name='patients-crud'),
]

# Final URL: /patients/patients/
```

### Step 1: Add Route to AppBuilder

Add your CRUD page to AppBuilder routes. **All AppBuilder routes must start with `/app`**.

**Example:** For CRUD view at `/patients/patients/`, add this route:

```json
{
  "name": "Patients",
  "path": "/app/patients",
  "page_type": "crud",
  "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 21V7a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v14\"/><path d=\"M12 9v6M9 12h6\"/></svg>",
  "extra_params": {
    "api_endpoint": "/patients/patients"
  }
}
```

**Important:** The `api_endpoint` is your **actual CRUD view URL** (module route + view route).

### Step 2: Add Menu Item for User Roles

Add the menu item to specific user roles so they can access it from the menu.

**Example:**
```json
{
  "route_id": "<generated-route-id>",
  "name": "Patients",
  "uri": "/app/patients",
  "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 21V7a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v14\"/><path d=\"M12 9v6M9 12h6\"/></svg>",
  "children": []
}
```

### Step 3: Preview Your CRUD Page

After configuration, access your CRUD page via AppBuilder at:
```
http://yourdomain.com/app/<route-name>
```

**Example:** `http://yourdomain.com/app/patients`

The AppBuilder frontend (at `/app/patients`) will call your CRUD view API (at `/patients/patients/`).

### Detailed Configuration Guide

For complete instructions on configuring routes and menus via API:
- **[AppBuilder API Configuration Guide](../appbuilder/api-configuration.md)**

This includes:
- How to add routes with proper `api_endpoint`
- How to configure menus for roles
- Complete workflow examples
- Authentication requirements

**Important:** The appbuilder package must be installed for this to work.
