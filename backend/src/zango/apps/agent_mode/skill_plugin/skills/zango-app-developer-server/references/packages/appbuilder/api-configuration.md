# AppBuilder Package API Configuration

This guide explains how to configure the AppBuilder package programmatically via API after creating CRUD views or custom pages.

## Overview

After creating CRUD views or custom pages in your Zango app, you need to:
1. **Add Routes** - Register the page paths in AppBuilder's global routes configuration
2. **Configure Menus** - Add menu items for specific user roles to make the pages accessible

Both can be done via API without using the App Panel UI.

## Prerequisites

1. AppBuilder package installed
2. Valid authentication (session cookie + CSRF token)
3. App domain configured (required for package config URL)

## Step 1: Get Package Configuration URL

First, get the base URL for the AppBuilder configuration API:

```bash
curl -s -b /tmp/zango_cookies \
  "http://localhost:8000/api/v1/apps/<app_uuid>/packages/?action=config_url&package_name=appbuilder"
```

**Response:**
```json
{
  "success": true,
  "response": {
    "url": "http://yourdomain.com/app/configure?token=abc123xyz"
  }
}
```

**IMPORTANT:** The returned URL includes an authentication token in the query string (e.g., `?token=abc123xyz`). Extract the base URL and token separately — the `token` must be passed as a query parameter in every subsequent API call.

```bash
CONFIG_BASE_URL="http://yourdomain.com/app/configure"
TOKEN="abc123xyz"
```

The configuration endpoints (always pass `token` as a query param):
- Routes API: `$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=<action>`
- Menu API: `$CONFIG_BASE_URL/api/?token=$TOKEN&action=<action>`

---

## Step 2: Managing Routes

Routes define all available pages in your application. They are global (not role-specific).

### List All Routes

Get the current routes configuration:

```bash
curl "$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=get_routes" \
  -H 'Content-Type: application/json'
```

**Response:**
```json
{
  "success": true,
  "response": {
    "id": 1,
    "routes": [
      {
        "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
        "name": "Patients",
        "path": "/app/patients",
        "page_type": "crud",
        "extra_params": {
          "api_endpoint": "/patients/patients"
        }
      }
    ],
    "created_at": "2026-03-25T06:14:19.112639Z",
    "modified_at": "2026-03-25T06:14:19.112669Z"
  }
}
```

### Add New Route

To add a route after creating a new CRUD view, **include all existing routes plus the new one**. The `save_routes` action replaces the entire routes configuration.

**Example: Adding "Country" route when "Patients" route already exists:**

```bash
curl "$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=save_routes" \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "routes": [
      {
        "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
        "name": "Patients",
        "path": "/app/patients",
        "page_type": "crud",
        "extra_params": {
          "api_endpoint": "/patients/patients"
        }
      },
      {
        "name": "Country",
        "path": "/app/country",
        "page_type": "crud",
        "icon": "<svg width=\"32\" height=\"32\" viewBox=\"0 0 32 32\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M17 16.5862V7C17 6.44749 16.5525 6 16 6C15.4475 6 15 6.44749 15 7V16.5862L11.7075 13.2925C11.3163 12.9025 10.6838 12.9025 10.2925 13.2925C9.9025 13.6837 9.9025 14.3162 10.2925 14.7075L16 20.4137L21.7076 14.7075C22.0976 14.3162 22.0976 13.6837 21.7076 13.2925C21.3163 12.9025 20.6838 12.9025 20.2925 13.2925L17 16.5862Z\" fill=\"black\"/><path d=\"M8 19C8.55251 19 9 19.4475 9 20V21.6C9 22.3738 9.62624 23 10.4 23H21.6C22.3738 23 23 22.3738 23 21.6V20C23 19.4475 23.4475 19 24 19C24.5525 19 25 19.4475 25 20V21.6C25 23.4775 23.4775 25 21.6 25H10.4C8.5225 25 7 23.4775 7 21.6V20C7 19.4475 7.44749 19 8 19Z\" fill=\"black\"/></svg>",
        "extra_params": {
          "api_endpoint": "/country/country"
        }
      }
    ]
  }'
```

**Important Notes:**
- **All routes MUST start with `/app`**: The `path` field must begin with `/app` (e.g., `/app/patients`, `/app/country`)
- **Include existing routes**: The first route has `route_id` already set - this preserves the existing route
- **New routes**: The second route doesn't have `route_id` - it will be auto-generated
- **Icon**: SVG string only — **do NOT use emoji** for route icons (e.g., `"<svg width=\"32\" height=\"32\" ...>...</svg>"`)
- **Replace all**: This replaces ALL routes, so always include existing ones
- **api_endpoint**: This is your actual CRUD view URL (module route + view route, e.g., `/patients/patients`)

**Response:**
```json
{
  "success": true,
  "response": {
    "id": 2,
    "routes": [
      {
        "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
        "name": "Patients",
        "path": "/app/patients",
        "page_type": "crud",
        "extra_params": {
          "api_endpoint": "/patients/patients"
        }
      },
      {
        "route_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
        "name": "Country",
        "path": "/app/country",
        "page_type": "crud",
        "icon": "<svg>...</svg>",
        "extra_params": {
          "api_endpoint": "/country/country"
        }
      }
    ],
    "menus_synced": 2,
    "created_at": "2026-03-25T06:20:00.000000Z",
    "modified_at": "2026-03-25T06:20:00.000000Z"
  }
}
```

The `menus_synced` field indicates how many menu configurations were updated.

### Update Existing Routes

Update an existing routes configuration (use the `id` from the get_routes response):

```bash
curl "$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=update_routes&pk=1" \
  -X PUT \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "routes": [
      {
        "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
        "name": "Patients Management",
        "path": "/app/patients",
        "page_type": "crud",
        "extra_params": {
          "api_endpoint": "/patients/patients"
        }
      }
    ]
  }'
```

### Route Object Structure

```typescript
{
  "route_id": string,           // UUID, auto-generated if not provided
  "name": string,                // Display name (required)
  "path": string,                // MUST start with /app (required, e.g., "/app/doctors")
  "page_type": string,           // "crud" | "profile360" | "custom" (required)
  "icon": string,                // SVG string ONLY — no emoji (optional, but recommended)
  "component": string,           // Component name for custom pages (optional)
  "extra_params": object         // Additional configuration (optional)
}
```

**Critical Rules:**
- **`path` MUST start with `/app`** - This is the AppBuilder frontend route (e.g., `/app/doctors`)
- **`api_endpoint`** (in `extra_params`) - This is your actual CRUD view URL:
  - Composed of: module route + view route
  - Example: If module route is `^doctors/` and view route is `doctors/`, then `api_endpoint` = `/doctors/doctors`
  - See [CRUD package documentation](../crud/overview.md#understanding-crud-view-urls) for details

**Page Type Examples:**

**CRUD Page:**
```json
{
  "name": "Doctors",
  "path": "/app/doctors",
  "page_type": "crud",
  "icon": "👨‍⚕️",
  "extra_params": {
    "api_endpoint": "/doctors/doctors"
  }
}
```

**Explanation:**
- User accesses: `http://yourdomain.com/app/doctors` (AppBuilder frontend)
- Frontend calls: `http://yourdomain.com/doctors/doctors` (Your CRUD view API)

**CRUD Page with SVG Icon:**
```json
{
  "name": "Country",
  "path": "/app/country",
  "page_type": "crud",
  "icon": "<svg width=\"32\" height=\"32\" viewBox=\"0 0 32 32\" fill=\"none\"><path d=\"...\" fill=\"black\"/></svg>",
  "extra_params": {
    "api_endpoint": "/country/country"
  }
}
```

**Profile360 Page:**
```json
{
  "name": "Doctor Profile",
  "path": "/app/profile360/doctors/:id",
  "page_type": "profile360",
  "icon": "👨‍⚕️"
}
```

**Custom Page:**
```json
{
  "name": "Dashboard",
  "path": "/app/dashboard",
  "page_type": "custom",
  "component": "Dashboard",
  "icon": "📊"
}
```

**Icon Guidelines:**
- **Route icons must be SVG strings only** — emoji are NOT supported for routes
- SVG icons should be 32x32 viewBox for consistency
- Icons are optional but highly recommended for better UX

---

## Step 3: Managing Menu Configurations

Menu configurations are role-specific. Each user role can have different menu items.

### List All Menu Configurations

Get all menu configurations for all roles:

```bash
curl "$CONFIG_BASE_URL/api/?token=$TOKEN&action=get_configs" \
  -H 'Content-Type: application/json'
```

**Response:**
```json
{
  "success": true,
  "response": [
    {
      "pk": 1,
      "user_role": "AnonymousUsers",          // RESPONSE: name. Requests need the numeric ID.
      "role": "AnonymousUsers",
      "menu": [
        {
          "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
          "name": "Patients",
          "uri": "/app/patients",
          "icon": "📄",
          "children": []
        }
      ],
      "config": {},
      "created_at": "2026-03-25T06:15:24.439314Z",
      "modified_at": "2026-03-25T06:15:24.439335Z"
    }
  ]
}
```

### Get Available Roles

Get roles that don't have menu configuration yet:

```bash
curl "$CONFIG_BASE_URL/api/?token=$TOKEN&action=get_available_roles" \
  -H 'Content-Type: application/json'
```

**Response:**
```json
{
  "success": true,
  "response": [
    {
      "id": 3,
      "name": "Doctor"
    },
    {
      "id": 4,
      "name": "Receptionist"
    }
  ]
}
```

### Get Routes List for Menu Creation

Get available routes to add to menus:

```bash
curl "$CONFIG_BASE_URL/api/?token=$TOKEN&action=get_routes_list" \
  -H 'Content-Type: application/json'
```

**Response:**
```json
{
  "success": true,
  "response": [
    {
      "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
      "name": "Patients",
      "path": "/app/patients",
      "icon": ""
    },
    {
      "route_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "name": "Country",
      "path": "/app/country",
      "icon": "<svg>...</svg>"
    }
  ]
}
```

### Create Menu Configuration for a Role

After creating a CRUD view, add it to a role's menu:

```bash
curl "$CONFIG_BASE_URL/api/?token=$TOKEN&action=create_config" \
  -X POST \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "user_role": 3,
    "menu": [
      {
        "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
        "name": "Patients",
        "uri": "/app/patients",
        "icon": "🏥",
        "children": []
      },
      {
        "route_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
        "name": "Country",
        "uri": "/app/country",
        "icon": "🌍",
        "children": []
      }
    ],
    "config": {}
  }'
```

**Parameters:**
- `user_role`: Role ID (number, get from available roles)
- `menu`: Array of menu items
- `config`: Additional configuration (optional, use `{}` if empty)

**Response:**
```json
{
  "success": true,
  "response": {
    "pk": 2,
    "user_role": "Doctor",                    // RESPONSE: name. Requests need the numeric ID.
    "role": "Doctor",
    "menu": [
      {
        "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
        "name": "Patients",
        "uri": "/app/patients",
        "icon": "🏥",
        "children": []
      }
    ],
    "config": {},
    "created_at": "2026-03-25T06:20:00.000000Z",
    "modified_at": "2026-03-25T06:20:00.000000Z"
  }
}
```

### Update Menu Configuration

Update an existing menu configuration (use the `pk` from the list response):

```bash
curl "$CONFIG_BASE_URL/api/?token=$TOKEN&action=update_config&pk=1" \
  -X PUT \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "menu": [
      {
        "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
        "name": "Patients",
        "uri": "/app/patients",
        "icon": "🏥",
        "children": []
      },
      {
        "route_id": "new-route-id",
        "name": "Appointments",
        "uri": "/app/appointments",
        "icon": "📅",
        "children": []
      }
    ]
  }'
```

### Delete Menu Configuration

```bash
curl "$CONFIG_BASE_URL/api/?token=$TOKEN&action=delete_config&pk=1" \
  -X DELETE \
  -H 'Content-Type: application/json'
```

**Response:**
```json
{
  "success": true,
  "response": "Configuration deleted successfully"
}
```

### Menu Item Structure

```typescript
{
  "route_id": string,      // UUID linking to route (required for sync)
  "name": string,          // Display name (required)
  "uri": string,           // URL path matching route path (required)
  "icon": string,          // Emoji or SVG icon (recommended)
  "children": array        // Nested menu items (required, use [] if no children)
}
```

**Important:**
- Always include `children` field, even if empty (`[]`)
- Use appropriate icons for menu items (emoji or SVG)
- Icons should match the entity/function (🏥 patients, 👨‍⚕️ doctors, 📅 appointments, 🌍 country, etc.)

**Nested Menu Example:**
```json
{
  "route_id": "",
  "name": "Management",
  "uri": "#",
  "icon": "⚙️",
  "children": [
    {
      "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
      "name": "Patients",
      "uri": "/app/patients",
      "icon": "🏥",
      "children": []
    },
    {
      "route_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "name": "Country",
      "uri": "/app/country",
      "icon": "🌍",
      "children": []
    }
  ]
}
```

---

## Complete Workflow Example

### Scenario: Adding a New CRUD Page After Creating the View

You've created a CRUD view for "Appointments" and now need to add it to AppBuilder.

**Step 1: Get existing routes**
```bash
curl "$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=get_routes" \
  -H 'Content-Type: application/json' \
  > routes.json
```

**Step 2: Prepare new routes array**

Extract existing routes and add the new one:
```bash
EXISTING_ROUTES=$(cat routes.json | jq '.response.routes')

# Create new route JSON
NEW_ROUTE='{
  "name": "Appointments",
  "path": "/app/appointments",
  "page_type": "crud",
  "icon": "📅",
  "extra_params": {
    "api_endpoint": "/appointments/appointments"
  }
}'

# Combine existing and new routes
ALL_ROUTES=$(echo $EXISTING_ROUTES | jq ". += [$NEW_ROUTE]")
```

**Step 3: Save updated routes**
```bash
curl "$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=save_routes" \
  -H 'Content-Type: application/json' \
  --data-raw "{\"routes\": $ALL_ROUTES}" \
  > updated_routes.json
```

**Step 4: Get the new route_id**
```bash
ROUTE_ID=$(cat updated_routes.json | jq -r '.response.routes[] | select(.path == "/app/appointments") | .route_id')
echo "New route_id: $ROUTE_ID"
```

**Step 5: Get existing menu config**
```bash
# List all configs
curl "$CONFIG_BASE_URL/api/?token=$TOKEN&action=get_configs" \
  -H 'Content-Type: application/json' \
  > configs.json

# Find the menu config pk for your target role
MENU_PK=$(cat configs.json | jq -r '.response[] | select(.role == "AnonymousUsers") | .pk')
echo "Menu PK: $MENU_PK"
```

**Step 6: Add to menu**
```bash
# Get existing menu items
EXISTING_MENU=$(cat configs.json | jq ".response[] | select(.pk == $MENU_PK) | .menu")

# Create new menu item
NEW_MENU_ITEM="{
  \"route_id\": \"$ROUTE_ID\",
  \"name\": \"Appointments\",
  \"uri\": \"/app/appointments\",
  \"icon\": \"📅\",
  \"children\": []
}"

# Combine
ALL_MENU=$(echo $EXISTING_MENU | jq ". += [$NEW_MENU_ITEM]")

# Update menu config
curl "$CONFIG_BASE_URL/api/?token=$TOKEN&action=update_config&pk=$MENU_PK" \
  -X PUT \
  -H 'Content-Type: application/json' \
  --data-raw "{\"menu\": $ALL_MENU}"
```

**Step 7: Verify**
```bash
# Check the updated config
curl "$CONFIG_BASE_URL/api/?token=$TOKEN&action=get_configs" \
  -H 'Content-Type: application/json' \
  | jq ".response[] | select(.pk == $MENU_PK)"
```

---

## Important Notes

### Route Sync Feature

When routes are updated (name, path, or icon changed), menu items are automatically synchronized based on `route_id`:
- Menu items with matching `route_id` will be updated automatically
- This ensures consistency across all role menus
- The `menus_synced` field in the response shows how many menus were updated

### Best Practices

1. **Always include route_id**: When creating menu items, use the `route_id` from routes to enable auto-sync
2. **Update routes carefully**: Since `save_routes` replaces all routes, always get existing routes first
3. **Always include children field**: Even if empty, include `"children": []` in menu items
4. **Use appropriate icons**: Add relevant emoji or SVG icons for better UX (🏥 🌍 👨‍⚕️ 📅 etc.)
5. **Test with one role**: Create menu configuration for one role first, verify it works, then replicate
6. **Consistent naming**: Keep route names and menu item names consistent

### Icon Recommendations

**Common Entity Icons:**
- Patients: 🏥 or 👤
- Doctors: 👨‍⚕️ or 🩺
- Appointments: 📅 or 🗓️
- Country/Location: 🌍 or 📍
- Settings: ⚙️ or 🔧
- Reports: 📊 or 📈
- Dashboard: 📊 or 🏠
- Users: 👥 or 👤
- Documents: 📄 or 📁

For custom SVG icons, use 32x32 viewBox with simple, clear designs.

### Response Field Mapping

**Routes API:**
- Uses `id` for the routes configuration record
- Returns array under `response.routes`
- `route_id` is UUID for each route

**Menu Config API:**
- Uses `pk` for the menu configuration record
- **In REQUESTS, `user_role` must be the role's numeric ID**, not its name.
  The server does `UserRoleModel.objects.get(pk=role_id)`, so a name fails
  with `Field 'id' expected a number but got '<name>'`. The field name is
  misleading — it is kept as `user_role` only for frontend compatibility.
  Get the ID from `action=get_available_roles`, which returns
  `[{"id": 3, "name": "Approver"}, ...]`.
- **In RESPONSES, `user_role` and `role` are the role NAME** (string). The
  examples above show responses; do not copy their shape into a request.
- Returns array directly under `response`

### Authentication

The `token` from the config URL response must be passed as a query parameter in every API call. All requests only need:
- `Content-Type: application/json` header

No additional CSRF tokens or Referer headers are required when passing the token as a query param.

### Error Handling

**Common Errors:**

- `"Configuration already exists for this role"` - Role already has a menu config, use UPDATE instead
- `"Invalid user role"` - Role ID doesn't exist
- `"Configuration not found"` - Menu config pk doesn't exist
- `"Invalid action"` - Check the action parameter in query string

---

## Quick Reference

### Routes API Endpoints

| Action | Method | Endpoint | Description |
|--------|--------|----------|-------------|
| List routes | GET | `$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=get_routes` | Get active routes |
| List all | GET | `$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=get_all_routes` | Get all route configs |
| Save routes | POST | `$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=save_routes` | Create/replace routes |
| Update routes | PUT | `$CONFIG_BASE_URL/routes/api/?token=$TOKEN&action=update_routes&pk=<id>` | Update specific config |

### Menu Config API Endpoints

| Action | Method | Endpoint | Description |
|--------|--------|----------|-------------|
| List configs | GET | `$CONFIG_BASE_URL/api/?token=$TOKEN&action=get_configs` | Get all menu configs |
| Available roles | GET | `$CONFIG_BASE_URL/api/?token=$TOKEN&action=get_available_roles` | Get unconfigured roles |
| Routes list | GET | `$CONFIG_BASE_URL/api/?token=$TOKEN&action=get_routes_list` | Get routes for dropdown |
| Get for edit | GET | `$CONFIG_BASE_URL/api/?token=$TOKEN&action=get_edit_config&pk=<pk>` | Get specific config |
| Create config | POST | `$CONFIG_BASE_URL/api/?token=$TOKEN&action=create_config` | Create menu for role |
| Update config | PUT | `$CONFIG_BASE_URL/api/?token=$TOKEN&action=update_config&pk=<pk>` | Update menu config |
| Delete config | DELETE | `$CONFIG_BASE_URL/api/?token=$TOKEN&action=delete_config&pk=<pk>` | Delete menu config |

### Required Headers

```bash
-H 'Content-Type: application/json'
```

The `token` query param handles authentication — no additional headers are needed.
