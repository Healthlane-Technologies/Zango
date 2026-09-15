> **Server-mode note (Agent Mode).** Commands in this file that use
> `docker compose`, `npm`/`npx`, `manage.py` or the `zango` CLI **cannot be
> run** in server mode: Bash is read-only, Node is unavailable, and the
> platform runs migrations and sync for you. Treat them as background
> reference for how the pieces fit together, not as steps to execute.

# Async Tasks in Zango

Async tasks in Zango enable non-blocking execution and improve the overall responsiveness and scalability of your application. They allow you to offload time-consuming operations like database queries, API calls, and file processing to run in the background.

## Overview

Zango provides two primary ways to execute async tasks:

1. **Direct Invocation** — Trigger tasks programmatically from anywhere in your code
2. **Scheduled Execution** — Configure tasks to run automatically at predetermined intervals

## Creating Async Tasks

### File Location

Create a `tasks.py` file in your module directory:
```
workspaces/<app_name>/backend/<module_name>/tasks.py
```

### Task Definition

Tasks are regular Python functions decorated with `@shared_task` from Celery:

```python
from celery import shared_task

@shared_task
def my_async_task(param1, param2):
    # Task logic here
    # Perform database operations, API calls, file processing, etc.
    pass

@shared_task
def send_email_notification(user_id, message):
    # Email sending logic
    pass

@shared_task
def process_data():
    # Data processing logic
    pass
```

**Key Points:**
- Multiple tasks can be defined in a single `tasks.py` file
- Each task must use the `@shared_task` decorator
- Tasks are regular Python functions that can accept parameters
- Suitable for time-consuming operations that shouldn't block the main application

## Manually Triggering Async Tasks

You can trigger async tasks programmatically from views, forms, or any other part of your code.

### Import the Executor

```python
from zango.core.tasks import zango_task_executor
```

### Execute the Task

```python
zango_task_executor.delay(
    request.tenant.name,
    "backend.module_name.tasks.task_function_name",
    # Optional: pass keyword arguments to the task
    param1="value1",
    param2="value2"
)
```

**IMPORTANT:** Use the full path from app root (e.g., `backend.notifications.tasks.send_email`, not just `notifications.tasks.send_email`).

### Example: Triggering from a View

```python
from zango.core.tasks import zango_task_executor
from django.http import JsonResponse

def trigger_notification(request):
    # Trigger async task
    zango_task_executor.delay(
        request.tenant.name,
        "backend.notifications.tasks.send_email_notification",
        user_id=request.user.id,
        message="Your report is ready"
    )

    return JsonResponse({"status": "Task triggered"})
```

### Parameters

- **Tenant name** (required): `request.tenant.name` — specifies which tenant the task belongs to
- **Task path** (required): Full path string to the task function from app root (e.g., `"backend.module_name.tasks.function_name"`)
- **Keyword arguments** (optional): Any parameters the task function expects

## Scheduling Async Tasks

Tasks can be configured to run automatically at specified intervals or times.

### Configuration via App Panel UI

1. Navigate to **Tasks** menu in the App Panel
2. Click **Sync** button to load latest tasks from codebase
3. Find your task in the list
4. Click the three-dot menu icon next to the task
5. Select **Update Task**
6. Configure:
   - **Frequency** — how often the task runs
   - **Timing** — when the task should execute
   - **Enable/Disable** — activate or deactivate the task
7. Save your configuration

### Configuration via API

See [app-panel-api.md](../app-panel-api.md) for programmatic task scheduling using the Tasks API endpoints.

## Syncing Async Tasks

After creating or modifying tasks in your codebase, you must sync them to make them available in the platform.

### Method 1: Via Command Line

```bash
docker compose -f deploy/docker_compose.yml exec app bash -c \
  "cd <PROJECT_NAME> && zango update-apps --app_name <app_name>"
```

This command syncs tasks, policies, and other app configurations.

### Method 2: Via App Panel UI

1. Navigate to **Tasks** menu
2. Click the **Sync** button
3. Wait for the loading indicator to complete
4. New tasks will appear in the list

### Method 3: Via API (Preferred for automation)

```bash
curl -s -b /tmp/zango_cookies -X POST \
  "http://localhost:8000/api/v1/apps/$APP_UUID/tasks/" \
  -H "X-CSRFToken: $CSRF" \
  -H "Referer: http://localhost:8000/platform/" \
  -H "Content-Length: 0"
```

See [app-panel-api.md](../app-panel-api.md) → Tasks → Sync Tasks for full details.

## Restarting Celery Service

**CRITICAL:** After creating or modifying async tasks, you must restart the Celery service for changes to take effect.

```bash
docker compose -f deploy/docker_compose.yml restart celery
```

## Viewing Async Tasks

Access async tasks through the App Panel:

1. Navigate to **Tasks** menu
2. View table with task details:
   - Task name
   - Status (enabled/disabled)
   - Execution frequency
   - Last run time
   - Other relevant information

If recently added tasks don't appear, click the **Sync** button to refresh the list.

## Common Use Cases

- **Background data synchronization** — sync data with external APIs
- **Cleanup processes** — remove old records, clear caches
- **Periodic calculations** — generate reports, aggregate statistics
- **Email/SMS notifications** — send communications without blocking requests
- **File processing** — handle uploads, generate PDFs, process images
- **Database maintenance** — optimize tables, update denormalized data

## Best Practices

1. **Keep tasks idempotent** — tasks should be safe to retry if they fail
2. **Handle errors gracefully** — use try/except blocks and log errors
3. **Avoid long-running tasks** — break large tasks into smaller chunks
4. **Use task parameters** — make tasks reusable with different inputs
5. **Sync after changes** — always sync and restart celery after modifying tasks
6. **Monitor task execution** — check logs and task status regularly

## Workflow Summary

```
1. Create tasks.py in your module
   └─> Define functions with @shared_task decorator

2. Sync tasks
   └─> Call Sync Tasks API: POST /api/v1/apps/<uuid>/tasks/
       (see app-panel-api.md → Tasks → Sync Tasks)

3. Restart Celery
   └─> docker compose restart celery

4. Trigger tasks
   ├─> Manually: use zango_task_executor.delay() with full path
   └─> Scheduled: configure via App Panel or API

5. Monitor tasks
   └─> View in App Panel Tasks menu
```
