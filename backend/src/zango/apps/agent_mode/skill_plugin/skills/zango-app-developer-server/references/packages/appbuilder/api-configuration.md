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
  "icon": string,                // Inline SVG ONLY — never emoji (required in practice)
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
  "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M9 3v4a3 3 0 0 0 6 0V3\"/><path d=\"M12 14v3m0 0a4 4 0 0 0 4-4v-1a5 5 0 0 0-10 0v1a4 4 0 0 0 4 4Z\"/></svg>",
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
  "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M9 3v4a3 3 0 0 0 6 0V3\"/><path d=\"M12 14v3m0 0a4 4 0 0 0 4-4v-1a5 5 0 0 0-10 0v1a4 4 0 0 0 4 4Z\"/></svg>"
}
```

**Custom Page:**
```json
{
  "name": "Dashboard",
  "path": "/app/dashboard",
  "page_type": "custom",
  "component": "Dashboard",
  "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 20V10M10 20V4M16 20v-7M22 20H2\"/></svg>"
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
          "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z\"/><path d=\"M14 3v5h5\"/></svg>",
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
        "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 21V7a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v14\"/><path d=\"M12 9v6M9 12h6\"/></svg>",
        "children": []
      },
      {
        "route_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
        "name": "Country",
        "uri": "/app/country",
        "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M3 12h18M12 3a15 15 0 0 1 0 18a15 15 0 0 1 0-18\"/></svg>",
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
        "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 21V7a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v14\"/><path d=\"M12 9v6M9 12h6\"/></svg>",
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
        "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 21V7a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v14\"/><path d=\"M12 9v6M9 12h6\"/></svg>",
        "children": []
      },
      {
        "route_id": "new-route-id",
        "name": "Appointments",
        "uri": "/app/appointments",
        "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><rect x=\"3\" y=\"5\" width=\"18\" height=\"16\" rx=\"2\"/><path d=\"M3 10h18M8 3v4M16 3v4\"/></svg>",
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
  "icon": string,          // Inline SVG ONLY — never emoji (required in practice)
  "children": array        // Nested menu items (required, use [] if no children)
}
```

**Important:**
- Always include `children` field, even if empty (`[]`)
- **`icon` is effectively required — never omit it and never send `""`.**
  The backend runs `clean_icon()` on every menu item, and its first branch is
  `if not icon: return "\U0001F4C4"`. So a missing or empty icon is silently
  replaced with the generic page emoji, and **every item in the sidebar renders
  as the same grey document** — no error, no warning, nothing in the logs.
  This was observed on a real run: all nine menu items came back as
  `{"name": "Products", "icon": "\U0001F4C4"}` because the agent sent no icon at
  all.
- **Use inline SVG for every icon. Never emoji — not for routes, not for
  menus.** `clean_icon()` has a second branch:

  ```python
  if "\ufffd" in icon or "�" in icon or icon.startswith("="):
      return "📄"
  ```

  Any icon carrying a replacement character is discarded for the grey document
  page. Emoji are multi-byte and only have to survive one mis-encoded hop — a
  shell heredoc, JSON written without `ensure_ascii=False`, `curl -d` under a
  non-UTF-8 locale — to arrive as `\ufffd` and be thrown away. The POST still
  returns `success: true`, so the failure is invisible unless you read the
  config back. Inline SVG is pure ASCII and cannot reach that branch.
- Give each entity a distinct glyph drawn as simple stroked paths, with
  `xmlns`, a 32×32 viewBox and `stroke="currentColor"` so it follows the
  sidebar's colour. Do not send an icon *name* like `"package"` — there is no
  icon-name lookup, so it falls into the image-URL branch and renders broken.

> **The sidebar renders the MENU icon, not the route icon.** Setting route
> icons while leaving menu icons blank still gives you a sidebar of identical
> grey pages. Both configs live in the tenant schema as JSON:
> `dynamic_models_approutesmodel.routes` and
> `dynamic_models_appmenumodel.menu` (one row per role).

**How the sidebar decides what to draw** (from the shipped renderer, in order):

| Value of `icon` | Rendered as |
|---|---|
| contains `<svg` | inlined markup — `<span class="navbar-icon">` + `dangerouslySetInnerHTML` |
| matches an emoji range, **or is ≤ 4 characters** | text — `<span class="navbar-icon navbar-icon-emoji">` |
| anything else, longer than 4 chars | **`<img src="{icon}">`** — treated as a URL |
| absent / empty | `clean_icon()` substitutes `\U0001F4C4` before it ever reaches the frontend |

Two consequences worth knowing:

- **A plain SVG string is inlined, so it must be self-contained** — include
  `xmlns`, size it 32×32, and prefer `fill="currentColor"` so it inherits the
  sidebar's colour instead of being hard-coded black.
- **A non-emoji short string silently becomes a broken `<img>`.** Sending
  `"box"` or `"package"` (a Lucide-style name, say) produces a broken image
  icon, not a fallback. There is no icon-name lookup — only SVG, emoji, or a
  real image URL.

Emoji are the safest default here: one character, no markup, no colour issues.

**Verify after posting the menu config.** Re-read the menu back (or open the
app) and confirm the icons are the ones you sent. If every `icon` in the
response is `"\U0001F4C4"`, you sent none — fix and re-post. A sidebar where
every entry has the same icon is a bug, not a styling preference.

**Nested Menu Example:**
```json
{
  "route_id": "",
  "name": "Management",
  "uri": "#",
  "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><circle cx=\"12\" cy=\"12\" r=\"3\"/><path d=\"M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.2 2.2M16.9 16.9l2.2 2.2M19.1 4.9l-2.2 2.2M7.1 16.9l-2.2 2.2\"/></svg>",
  "children": [
    {
      "route_id": "e0ea1311-9680-490b-889c-dabf67142bdf",
      "name": "Patients",
      "uri": "/app/patients",
      "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 21V7a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v14\"/><path d=\"M12 9v6M9 12h6\"/></svg>",
      "children": []
    },
    {
      "route_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "name": "Country",
      "uri": "/app/country",
      "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M3 12h18M12 3a15 15 0 0 1 0 18a15 15 0 0 1 0-18\"/></svg>",
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
  "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><rect x=\"3\" y=\"5\" width=\"18\" height=\"16\" rx=\"2\"/><path d=\"M3 10h18M8 3v4M16 3v4\"/></svg>",
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
4. **Always set a menu icon, and always as inline SVG** — never emoji, for
   menus or routes. Omitting it is not "no icon": the backend substitutes
   📄, so the whole sidebar renders as identical grey pages. Emoji are
   discarded the same way the moment one mis-encoded hop turns them into a
   replacement character, and the POST still returns `success: true`.
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

---

## Registering routes and menus end to end

### The sequence that works — follow it in this order

Routes must be saved **before** menus, because a menu item references a
`route_id` that only exists once the route is saved. Write payloads to files
and send them with `--data-binary @file`; inlining large JSON with `--data-raw`
is where quoting breaks.

```bash
# 0. Sanity: both must be reachable before you build any payload.
curl "$APPBUILDER_CONFIG_URL/routes/api/?token=$APPBUILDER_TOKEN&action=get_routes"
# -> {"success": true, "response": {"routes": []}}   <- empty is the start state

# 1. Save ALL routes in one call. save_routes REPLACES the array, so send
#    every route, not just the new one.
curl -X POST -H 'Content-Type: application/json' \
  --data-binary @routes_payload.json \
  "$APPBUILDER_CONFIG_URL/routes/api/?token=$APPBUILDER_TOKEN&action=save_routes"

# 2. Read back the SAVED route_ids. The server generates them — you cannot
#    invent them, and the ids in your payload file are not what got stored.
curl "$APPBUILDER_CONFIG_URL/routes/api/?token=$APPBUILDER_TOKEN&action=get_routes"

# 3. Roles WITHOUT a menu config yet -> [{"id": 3, "name": "Approver"}, ...]
curl "$APPBUILDER_CONFIG_URL/api/?token=$APPBUILDER_TOKEN&action=get_available_roles"

# 4. One config per role, using the numeric id from 3 and the route_ids from 2
curl -X POST -H 'Content-Type: application/json' \
  --data-binary @menu_role3.json \
  "$APPBUILDER_CONFIG_URL/api/?token=$APPBUILDER_TOKEN&action=create_config"

# 5. Read both back and CHECK THE CONTENT, not the status code.
curl "$APPBUILDER_CONFIG_URL/api/?token=$APPBUILDER_TOKEN&action=get_configs"
```

Note `get_available_roles` only returns roles that do **not** yet have a
config, so it shrinks as you go. Re-fetch it rather than caching, and expect
`Configuration already exists for this role` if you retry one.

### Four failures that return `success: true`

Every one of these has shipped. None of them raises an error, so **a 200 is not
evidence that this step worked** — only a read-back is.

1. **Route ids invented instead of read back.** The menu saves fine and every
   sidebar item is dead, because its `route_id` matches no route. Always take
   ids from step 2's response.
2. **Menus posted before routes.** Same outcome, same silence.
3. **Icons mangled to `📄`** — see the icon rule above. Check every `icon`
   value contains `<svg`.
4. **A role silently skipped.** `get_available_roles` shrinks as configs are
   created, so a loop that caches the first response stops early and the last
   role gets no menu at all.

### Verify before moving on — check values, not status codes

```bash
curl "$APPBUILDER_CONFIG_URL/routes/api/?token=$APPBUILDER_TOKEN&action=get_routes"
curl "$APPBUILDER_CONFIG_URL/api/?token=$APPBUILDER_TOKEN&action=get_configs"
```

All four must hold, and you must state each one in your summary:

- `get_routes` returns your routes, **not `[]`**
- every custom page you wrote in 5d appears with `page_type: "custom"` and a
  `component` matching its export name exactly
- `get_configs` returns **one config per role** — count them against the roles
  in the run context
- **every menu item's `route_id` appears in `get_routes`**, and every `icon`
  contains `<svg>`

If any check fails, fix it now. Do not proceed to STEP 6 and do not report the
app as complete: a saved route with no menu, or a menu pointing at ids that do
not exist, leaves the app with a sidebar that is empty or entirely dead links —
which is indistinguishable, to the person opening the app, from the frontend
never having been built.

Full request shapes:
[packages/appbuilder/api-configuration.md](references/packages/appbuilder/api-configuration.md).
`curl` is permitted for this, but only against this app's own domain and
localhost. The token lasts 30 minutes.

If `appbuilder_config_url` is UNAVAILABLE, skip 5h and list the routes and
menu entries an operator must add. Do NOT skip 5a-5g because of it - the
frontend build does not depend on the config API.
