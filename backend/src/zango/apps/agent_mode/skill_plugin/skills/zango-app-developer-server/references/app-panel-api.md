> **Server-mode note (Agent Mode).** Commands in this file that use
> `docker compose` or the `zango` CLI **cannot be run** in server mode, and
> Bash is otherwise read-only. Treat those as background reference.
> Two exceptions: the **npm commands allowed by STEP 5d** (scaffold, install,
> build) do run — Node is available — and you run the **`manage.py` commands
> listed in STEP 7** (migrations, sync, static) yourself.

# Zango App Panel API Reference

All endpoints are under `http://localhost:8000/api/v1/` unless otherwise noted. All responses follow the format `{success: bool, response: {...}}`.

## Authentication

Zango uses Django session auth with CSRF protection. All API calls require authentication.

### Login Flow (Shell)

```bash
# Step 1: Get CSRF cookie
curl -s -c /tmp/zango_cookies http://localhost:8000/auth/login/ -o /dev/null
CSRF=$(grep csrftoken /tmp/zango_cookies | awk '{print $NF}')

# Step 2: Login (returns 302 on success, sets sessionid cookie)
curl -s -L -c /tmp/zango_cookies -b /tmp/zango_cookies -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Origin: http://localhost:8000" \
  -H "Referer: http://localhost:8000/auth/login/" \
  -d "csrfmiddlewaretoken=$CSRF&username=platform_admin%40zango.dev&password=Zango%40123" \
  -o /dev/null

# Step 3: Refresh CSRF for subsequent mutating requests
CSRF=$(grep csrftoken /tmp/zango_cookies | awk '{print $NF}')
# All POST/PUT/DELETE must include: -H "X-CSRFToken: $CSRF" -H "Referer: http://localhost:8000/platform/"
```

**Important:** Replace username/password with values from `deploy/.env` (`PLATFORM_USERNAME` / `PLATFORM_USER_PASSWORD`). URL-encode special characters (e.g., `@` → `%40`, `#` → `%23`).

The API also supports Knox TokenAuthentication — both `SessionAuthentication` and `TokenAuthentication` are accepted.

---

## Apps

### List Apps
```
GET /api/v1/apps/
→ {success, response: {apps: [...], message}}
```

### Create App (async)
```
POST /api/v1/apps/
Body: name=<name>&description=<description>
Headers: X-CSRFToken, Referer
→ {success, response: {message, app_uuid, task_id}}
```

App creation is **async**. Poll for completion:
```
GET /api/v1/apps/?action=get_app_creation_status&task_id=<task_id>
→ {success, response: {message, deployed: bool, status}}
```
Wait until `response.deployed == true`.

### Get App Details
```
GET /api/v1/apps/<uuid>/
→ {success, response: {app: {...}}}

GET /api/v1/apps/<uuid>/?include_dropdown_options=true
→ Also returns dropdown_options: {timezones, datetime_formats, date_formats}
```

### Update App (configure domains, timezone, etc.)
```
PUT /api/v1/apps/<uuid>/
Body: domains=<url-encoded-json>&timezone=<tz>&date_format=<fmt>&datetime_format=<fmt>
Headers: X-CSRFToken, Referer
→ {success, response: {message, app_uuid}}
```

**Domain configuration example:**
```
domains=[{"domain":"myapp.local","is_primary":true}]
```
The `domains` value must be URL-encoded when sent as form data.

---

## Roles

Default roles created with every app: `AnonymousUsers` (id=1), `SystemUsers` (id=2).

### List Roles
```
GET /api/v1/apps/<uuid>/roles/
Optional: ?search=<term>&include_dropdown_options=true
→ {success, response: {roles: {total_records, records: [...]}}}
```

### Create Role
```
POST /api/v1/apps/<uuid>/roles/
Body: name=<name>&policies=<comma-separated-ids>
→ {success, response: {message, role_id}}
```

### Get / Update Role
```
GET /api/v1/apps/<uuid>/roles/<id>/
→ {success, response: {role: {...}, all_policies: [...]}}

PUT /api/v1/apps/<uuid>/roles/<id>/
Body: name, policies, policy_groups, is_active
→ {success, response: {message, role_id}}
```

---

## Users (App Users)

### List Users
```
GET /api/v1/apps/<uuid>/users/
Optional: ?search=<term>&include_dropdown_options=true
→ {success, response: {users: {total_records, records: [...]}, pn_country_code}}
```

### Create User
```
POST /api/v1/apps/<uuid>/users/
Body: name=<name>&email=<email>&mobile=&password=<password>&roles=<role_id>
→ {success, response: {message}}
```

**Important:** The `mobile` field must be present in the POST body even if empty. The `roles` field accepts a role ID (integer).

### Get / Update User
```
GET /api/v1/apps/<uuid>/users/<id>/
PUT /api/v1/apps/<uuid>/users/<id>/
```

---

## Policies

Policies are primarily managed through `policies.json` in the app workspace. After creating or updating `policies.json`, you must sync them to the platform.

### Sync Policies (after creating/updating policies.json)

**Important:** Always call this after creating or updating `policies.json` in the codebase.

```bash
POST /api/v1/apps/<uuid>/policies/?action=sync_policies
Headers:
  -H "X-CSRFToken: <csrf_token>"
  -H "Referer: http://localhost:8000/platform/"
  -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundary..."
Body: (empty multipart form data)
→ {success: true, response: {message: "Policies synced successfully"}}
```

**Example:**
```bash
curl -s -b /tmp/zango_cookies -X POST \
  "http://localhost:8000/api/v1/apps/$APP_UUID/policies/?action=sync_policies" \
  -H "X-CSRFToken: $CSRF" \
  -H "Referer: http://localhost:8000/platform/" \
  -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundary" \
  --data-raw '------WebKitFormBoundary--'
```

### List/Read Policies

```
GET /api/v1/apps/<uuid>/policies/
Optional: ?search=<term>
→ {success, response: {policies: {total_records, records: [...]}}}

GET /api/v1/apps/<uuid>/policies/<id>/
GET /api/v1/apps/<uuid>/permissions/    # alias
```

### Update Policy (assign roles)

**CRITICAL:** The PUT request REPLACES all roles in the policy, so you must include ALL roles that exist in the system.

**Step 1 — Fetch all role IDs:**
```bash
curl -s -b /tmp/zango_cookies \
  "http://localhost:8000/api/v1/apps/<app_uuid>/roles/" \
  | jq -r '.response.results[] | "\(.id) - \(.name)"'
```

**Step 2 — Update policy with ALL role IDs:**

Use curl's `-F` flag to send multipart form data. Include every role ID from step 1.

```bash
curl "http://localhost:8000/api/v1/apps/<app_uuid>/policies/<policy_id>/" \
  -X PUT \
  -b /tmp/zango_cookies \
  -H "X-CSRFToken: $CSRF" \
  -H "Referer: http://localhost:8000/platform/" \
  -F "id=<policy_id>" \
  -F "roles=1" \
  -F "roles=2" \
  -F "roles=3"
```

**Notes:**
- Each `-F "roles=X"` adds one role. Repeat for every role ID returned in step 1.
- **Do NOT use `--data-raw` with manual boundaries** — it will silently fail to update roles.
- Policy ID for `AllowFromAnywhere` is typically `1`.

---

## Packages

Available packages: `appbuilder`, `communication`, `crud`, `workflow`.

### List Packages
```
GET /api/v1/apps/<uuid>/packages/
Optional: ?search=<term>
→ {success, response: {packages: {total_records, records: [{name, versions, status, config_url}], installed_count}}}
```

### Install Package
```
POST /api/v1/apps/<uuid>/packages/
Body: name=<name>&version=<version>
→ {success, response: {message: "Package Installed"}}
```

### Get Package Config URL
```
GET /api/v1/apps/<uuid>/packages/?action=config_url&package_name=<name>
→ {success, response: {url}}
```
Requires a domain to be configured on the app.

---

## Codebase

```
GET /api/v1/apps/<uuid>/codebase/
→ {success, response: {app_codebase: {app_name, version, modules, package_routes, app_routes, route_tree, workspace_path, ...}}}
```

Returns the full codebase structure including modules, routes, and workspace path.

---

## Themes

### List / Get Theme
```
GET /api/v1/apps/<uuid>/themes/
GET /api/v1/apps/<uuid>/themes/<id>/
```

### Update Theme
```
PUT /api/v1/apps/<uuid>/themes/<id>/
Body: name, config (JSON string), is_active
```

**Known bug:** Theme creation via POST has a bug — the serializer calls `json.loads()` on data DRF has already parsed. Use the App Panel UI for creating themes. Reading and updating existing themes works fine via API.

Default theme config structure:
```json
{
  "color": {"primary": "#5048ED", "secondary": "#E1D6AE", "background": "#ffffff"},
  "button": {"color": "#ffffff", "background": "#5048ED", "border_color": "#C7CED3", "border_radius": "10"},
  "typography": {"font_family": "Open Sans"}
}
```

---

## Secrets

App secrets store API keys and credentials encrypted in the database. Always use secrets for app-level credentials — **never put them in the project `.env` file**.

**Requires** `FIELD_ENCRYPTION_KEY` in `deploy/.env` (32-byte Fernet key — generate once at bootstrap and never change).

**Key naming rules** (enforced by regex `^[A-Z][a-z0-9_]*$`):
- First character must be uppercase
- Remaining characters: lowercase letters, digits, or `_`
- No spaces, no other special characters
- Examples: `My_api_key`, `Stripe_secret`, `Sendgrid_api_key`

### List Secrets
```
GET /api/v1/apps/<uuid>/secrets/?page=1&page_size=20&search=
→ {success, response: {secrets: {total_records, total_pages, next, previous, records: [{id, key, is_active, created_at, modified_at}]}, message}}
```

### Create Secret
```bash
curl -b /tmp/zango_cookies -X POST \
  "http://localhost:8000/api/v1/apps/$APP_UUID/secrets/" \
  -H "X-CSRFToken: $CSRF" \
  -F "key=My_secret_key" \
  -F "value=mysecretvalue"
→ {success: true, response: {message: "Secret created successfully", secret_id: 1}}
```

### Get Secret Value
```
GET /api/v1/apps/<uuid>/secrets/?action=get_secret_value&secret_id=<id>
→ {success: true, response: {secret_value: "<decrypted value>"}}
```

### Update Secret
```bash
curl -b /tmp/zango_cookies -X PUT \
  "http://localhost:8000/api/v1/apps/$APP_UUID/secrets/?secret_id=<id>" \
  -H "X-CSRFToken: $CSRF" \
  -F "key=My_secret_key" \
  -F "value=updated_value"
→ {success: true, response: {message: "Secret updated successfully", secret_id: 1}}
```

### Delete Secret
```
DELETE /api/v1/apps/<uuid>/secrets/?secret_id=<id>
Headers: X-CSRFToken
```
Secret must be set to inactive before deletion.

---

## Tasks (Async/Celery)

### List Tasks
```
GET /api/v1/apps/<uuid>/tasks/
Optional: ?page=1&page_size=10&search=<term>&include_dropdown_options=true
→ {success, response: {tasks: {total_records, total_pages, next, previous, records: [...]}}}
```

Each task record includes: `id`, `name`, `is_enabled`, `crontab`, `schedule`, `kwargs`, `args`, `code`, `run_history`, `created_at`, `modified_at`, `attached_policies`, `interval`, `master_task`.

### Get Task Details
```
GET /api/v1/apps/<uuid>/tasks/<id>/
→ {success, response: {task: {...}}}
```

### Sync Tasks (after creating/updating tasks.py)

**Important:** Always call this after creating or updating `tasks.py` in the codebase to register new tasks with the platform.

```bash
POST /api/v1/apps/<uuid>/tasks/
Headers:
  -H "X-CSRFToken: <csrf_token>"
  -H "Referer: http://localhost:8000/platform/"
Body: (empty)
→ {success: true, response: {message: "Tasks synced successfully"}}
```

**Example:**
```bash
curl -s -b /tmp/zango_cookies -X POST \
  "http://localhost:8000/api/v1/apps/$APP_UUID/tasks/" \
  -H "X-CSRFToken: $CSRF" \
  -H "Referer: http://localhost:8000/platform/" \
  -H "Content-Length: 0"
```

---

### Update Task (Configure CRON Schedule)
```
POST /api/v1/apps/<uuid>/tasks/<id>/
Body (multipart/form-data):
  - crontab_exp: JSON string e.g. {"minute":"0","hour":"2","day_of_week":"*","day_of_month":"*","month_of_year":"*"}
  - is_enabled: true|false
  - kwargs: JSON object (task parameters)
Headers: X-CSRFToken, Referer
→ {success, response: {message: "Task updated successfully"}}
```

**Example:**
```bash
curl -b /tmp/zango_cookies -X POST \
  "http://localhost:8000/api/v1/apps/$APP_UUID/tasks/2/" \
  -H "X-CSRFToken: $CSRF" \
  -H "Referer: http://localhost:8000/platform/" \
  -F 'crontab_exp={"minute":"0","hour":"1","day_of_week":"*","day_of_month":"*","month_of_year":"*"}' \
  -F 'is_enabled=true' \
  -F 'kwargs={}'
```

**Note:** Use `-F` flags for proper multipart/form-data encoding. The `-F` flag automatically handles Content-Type and boundaries.

**IMPORTANT:** After updating task configuration, restart Celery service:
```bash
docker compose -f deploy/docker_compose.yml restart celery
```

---

## Audit Logs

```
GET /api/v1/apps/<uuid>/auditlog/
Optional: ?search=<term>
→ {success, response: {audit_logs: {total_records, records: [...]}}}
```
Records include: `actor`, `actor_type`, `action`, `object_type`, `timestamp`, `changes`.

---

## Access Logs

```
GET /api/v1/apps/<uuid>/access-logs/
Optional: ?search=<term>
→ {success, response: {access_logs: {total_records, records: [...]}, total_failed_attempts}}
```

---

## Releases

```
GET /api/v1/apps/<uuid>/releases/
→ {success, response: {releases: {total_records, records: [...]}}}

POST /api/v1/apps/<uuid>/releases/
```

---

## SAML Providers

```
GET /api/v1/apps/<uuid>/saml-providers/
POST /api/v1/apps/<uuid>/saml-providers/
GET /api/v1/apps/<uuid>/saml-providers/<id>/
PUT /api/v1/apps/<uuid>/saml-providers/<id>/
```

---

## Platform Users

```
GET /api/v1/auth/platform-users/
→ {success, response: {platform_users: {total_records, records: [{id, name, email, apps, is_superadmin, is_active}]}}}

POST /api/v1/auth/platform-users/
Body: name=<name>&email=<email>&password=<password>

GET /api/v1/auth/platform-users/<id>/
PUT /api/v1/auth/platform-users/<id>/
```

---

## Health Check

```
GET /api/v1/health/
→ {success, response: {status, timestamp, services: {redis, cache, celery, celery_beat}}}
```

---

## Celery Status

```
GET /platform/celery-status/
→ {success, response: {status: bool, active_workers: {...}}}
```

---

## Pagination

List endpoints return paginated results:
```json
{"total_records": 10, "total_pages": 1, "next": null, "previous": null, "records": [...]}
```
Query params: `?page=1&page_size=10`

## Search and Filtering

Most list endpoints support `?search=<term>` for text search and column-specific filters via `?columns[field_name]=value`.
