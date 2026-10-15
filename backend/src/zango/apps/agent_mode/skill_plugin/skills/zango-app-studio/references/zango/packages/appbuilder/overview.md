# AppBuilder Package Reference

The AppBuilder package is a complete React-based dynamic CRM framework for building modern, API-driven web applications on Zango.

## What is AppBuilder?

AppBuilder is a full-stack package that combines:
- **Frontend**: React-based SPA framework with dynamic routing, themes, and page types
- **Backend**: Django REST API views that serve the frontend and provide configuration endpoints
- **Configuration Models**: Database models for storing routes and menu configurations per role

It enables you to build complete web applications with CRUD operations, custom pages, and profile views without writing frontend code from scratch.

## Installation

### Install via App Panel

1. Navigate to your app in the App Panel (`http://localhost:8000/platform`)
2. Go to "Packages" section
3. Search for "appbuilder"
4. Click "Install" (use latest version)

## Architecture

### Frontend (React SPA)

React-based single-page application framework with dynamic routing, themes, and page types.

**Key Features**:
- Dynamic page types: CRUD, Profile360, Custom
- API-driven routes and menus
- Theme system via CSS variables
- Smart navigation (SPA + server routes)

See **[Frontend AppBuilder Reference](../../frontend/appbuilder.md)** for complete frontend architecture, framework details, and development guide.

### Backend (Django)

Located in `packages/appbuilder/backend/`:

**Two modules**:

1. **`app` module** (routes: `^`)
   - `AppView`: Renders the React SPA template
   - `AppInitializeAPI`: Returns routes, menu, theme, and profile info
   - URL: `/app/`

2. **`configure` module** (routes: `^configure/`)
   - Configuration APIs for managing routes and menus
   - CRUD operations for AppRoutesModel and AppMenuModel
   - URL: `/app/configure/`

**Models**:
- `AppRoutesModel`: Stores global route configurations (JSON field)
- `AppMenuModel`: Stores role-based menu and config (JSON field, OneToOne with UserRoleModel)

## Page Types

### 1. CRUD Pages

Auto-generated tables with full CRUD operations.

**Route Configuration**:
```json
{
  "path": "/app/doctors",
  "page_type": "crud",
  "entity": "doctors",
  "extra_params": {
    "api_endpoint": "/api/doctors/"
  }
}
```

**Backend Requirements**:
- CRUD views using `BaseCrudView` from the crud package
- Table, Form, and Model configured

### 2. Profile360 Pages

Comprehensive entity profiles with detailed information.

**Route Configuration**:
```json
{
  "path": "/app/profile360/doctors/:id",
  "page_type": "profile360",
  "entity": "doctors"
}
```

**Backend Requirements**:
- GET endpoint: `/{entity}/get-profile/{id}/`
- Returns detailed profile data

### 3. Custom Pages

User-defined React components for specialized functionality.

**Route Configuration**:
```json
{
  "path": "/app/dashboard",
  "page_type": "custom",
  "component": "Dashboard"
}
```

**Frontend Requirements**:
- Create React component
- Export in custom pages index

See **[Frontend AppBuilder Reference](../../frontend/appbuilder.md)** for complete guide on creating custom pages.

## Configuration

### Routes Configuration

Routes are stored in `AppRoutesModel` and define all available paths in the application.

**Example Routes**:
```json
[
  {
    "path": "/app/doctors",
    "page_type": "crud",
    "entity": "doctors",
    "extra_params": {
      "api_endpoint": "/api/doctors/"
    }
  },
  {
    "path": "/app/dashboard",
    "page_type": "custom",
    "component": "Dashboard"
  }
]
```

### Menu Configuration

Menus are role-based and stored in `AppMenuModel`. Each role can have a different menu structure.

**Example Menu**:
```json
[
  {
    "uri": "/app/dashboard",
    "name": "Dashboard",
    "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 20V10M10 20V4M16 20v-7M22 20H2\"/></svg>",
    "page_type": "custom",
    "component": "Dashboard"
  },
  {
    "uri": "/app/doctors",
    "name": "Doctors",
    "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M9 3v4a3 3 0 0 0 6 0V3\"/><path d=\"M12 14v3m0 0a4 4 0 0 0 4-4v-1a5 5 0 0 0-10 0v1a4 4 0 0 0 4 4Z\"/></svg>",
    "page_type": "crud",
    "entity": "doctors"
  }
]
```

### Theme Configuration

Themes are applied via the AppInitializeAPI and use CSS variables.

**Example Theme**:
```json
{
  "theme": {
    "colors": {
      "primary": "#5048ed",
      "secondary": "#6d7280",
      "background": "#ffffff",
      "text": "#1f2937"
    }
  }
}
```

## Development Workflow

### 1. Install AppBuilder Package

Install via App Panel.

### 2. Configure Routes (Via API - Mandatory After Every CRUD View)

**IMPORTANT:** After creating CRUD views or custom pages, you **MUST** add routes to AppBuilder. This is a mandatory step.

Configure routes via API - see [api-configuration.md](api-configuration.md) for complete guide.

Routes define all available pages (global, not role-specific).

### 3. Configure Menus (Via API - Mandatory After Every CRUD View)

**IMPORTANT:** After adding routes, you **MUST** configure menu items for relevant user roles. This is a mandatory step.

Configure menus via API - see [api-configuration.md](api-configuration.md) for complete guide.

Menu configurations are role-based - each role can have different menu items.

### 4. Build Custom Pages (Optional)

For custom React pages, see the **[Frontend AppBuilder Reference](../../frontend/appbuilder.md)** for complete setup, build commands, and development workflow.

### 5. Access the Application

Navigate to `http://yourdomain.com/app/` to see your application.

## Backend Integration

### Configuring Routes and Menus

Use the AppBuilder Configuration API to programmatically configure routes and menus.

See **[API Configuration Guide](api-configuration.md)** for complete details on:
- Creating and updating routes
- Managing role-based menus
- Route-menu synchronization
- Complete workflow examples

## Common Workflows

### Adding a New CRUD Page

1. Create your model, form, table, and view using crud package
2. Configure route and menu via **[API Configuration Guide](api-configuration.md)**
3. Access at `http://yourdomain.com/app/patients`

### Adding a Custom Page

1. Create React component - see **[Frontend AppBuilder Reference](../../frontend/appbuilder.md)**
2. Configure route and menu via **[API Configuration Guide](api-configuration.md)**
3. Access at your configured path

## Troubleshooting

### Frontend Not Loading

- Verify frontend build exists: `packages/appbuilder/static/appbuilder/js/`
- Check browser console for errors
- Verify `/app/initializer/` endpoint returns valid JSON

### Routes Not Working

- Verify routes are saved in `AppRoutesModel`
- Check that menus in `AppMenuModel` match routes
- Clear browser cache and hard reload

### Custom Pages Not Found

- Verify component is exported in `frontend/src/custom/pages/index.js`
- Check build output includes your component
- Verify `component` name in route matches export name (case-sensitive)

## Dependencies

AppBuilder typically works with:
- **crud package**: Required for CRUD page types
- **workflow package** (optional): Workflow integration

## Notes

- Frontend builds are versioned (reads from `frontend/package.json`)
- Theme changes require page refresh
- Menu is role-based - each role can have different menu items
- Routes are global - same routes available to all roles
- Smart navigation automatically handles SPA vs server routing

---

## Related Documentation

- **[API Configuration Guide](api-configuration.md)** - Complete guide for configuring routes and menus via API
- **[Frontend AppBuilder Reference](../../frontend/appbuilder.md)** - Complete guide for React frontend development, custom pages, themes, and build workflow
