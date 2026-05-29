```markdown
# Zango AI Framework — Tools Implementation (Backend + Frontend)

## Prerequisites

Phase 1 (Provider Layer) and Phase 2 core (Agent, Prompt, Invocation models) are complete.

Available from prior phases:
- `zango/ai/providers/` — Provider registry, BaseLLMProvider, implementations
- `zango/ai/models/provider.py` — AppLLMProvider, AppLLMProviderModel
- `zango/ai/models/invocation.py` — AppLLMInvocation (with agent FK, rounds_detail, etc.)
- `zango/ai/models/agent.py` — AppLLMAgent, AppLLMAgentToolConfig
- `zango/ai/exceptions.py` — Typed exceptions
- `zango/ai/encryption.py` — Encryption utilities
- `zango/ai/__init__.py` — get_agent(), get_provider()

This prompt covers the **complete Tools subsystem** — backend (decorator, registry, 
sync, executor, confirmation, models, API) and frontend (App Panel UI for viewing 
tools, attaching to agents, managing confirmations).

---

## BACKEND

### File Structure

```
zango/
├── ai/
│   ├── tools/
│   │   ├── __init__.py          # Public exports: @tool, ToolParam, ToolSafety
│   │   ├── decorator.py         # @tool decorator, ToolParam, schema generation
│   │   ├── registry.py          # TOOL_REGISTRY, autodiscovery, sync to DB
│   │   ├── executor.py          # Tool execution with timeout, error handling
│   │   └── confirmation.py      # Confirmation resolution pipeline
│   ├── models/
│   │   ├── tool.py              # AppLLMTool, AppLLMToolCall
│   │   └── confirmation.py      # AppLLMToolConfirmation
│   └── api/
│       ├── tool_serializers.py  # DRF serializers for tools
│       ├── tool_views.py        # API views for tool management
│       ├── confirmation_views.py # API views for confirmation management
│       └── urls.py              # UPDATED: add tool and confirmation routes
```

App-developer side (in each Zango workspace):
```
workspaces/{app_name}/
├── {module}/
│   └── tools.py                 # Developer defines @tool functions here
```

---

### 1. `zango/ai/tools/__init__.py`

```python
"""
Public API for the tools subsystem.

Exports:
- tool: Decorator for registering tool functions
- ToolParam: Parameter descriptor for providing LLM metadata
- ToolSafety: Enum for safety classification (READ_ONLY, WRITE, EXTERNAL)
- TOOL_REGISTRY: The in-memory registry (for framework internal use)
- autodiscover_tools: Trigger tool discovery (called on app startup)
- sync_tools_to_db: Sync discovered tools to database (called on app startup)
- get_tool_function: Look up a tool function by name
"""

from zango.ai.tools.decorator import tool, ToolParam, ToolSafety
from zango.ai.tools.registry import (
    TOOL_REGISTRY,
    autodiscover_tools,
    sync_tools_to_db,
    get_tool_function,
    get_all_tool_metas,
)
```

---

### 2. `zango/ai/tools/decorator.py`

```python
"""
The @tool decorator and ToolParam descriptor.

## How @tool works

1. Developer writes a function with type hints and ToolParam descriptors
2. @tool extracts function signature, type hints, ToolParam metadata
3. Builds a JSON Schema from the parameters (for LLM tool-use API)
4. Stores all metadata on func._tool_meta as a ToolMeta dataclass
5. Registers the function in TOOL_REGISTRY (in-memory dict)
6. Returns the original function (unchanged — can still be called directly)

## ToolParam

Provides per-parameter metadata that the LLM needs:
- description (required): What this parameter represents
- default: Default value (makes parameter optional in JSON schema)
- enum: List of allowed values (adds "enum" constraint to schema)

If a parameter has a ToolParam as its default, the ToolParam's description 
goes into the JSON schema, and its default value (if any) makes the param optional.

If a parameter has no ToolParam (regular default or no default), it gets a 
generic description derived from the parameter name.

## Type Mapping (Python → JSON Schema)

str         → {"type": "string"}
int         → {"type": "integer"}
float       → {"type": "number"}
bool        → {"type": "boolean"}
list        → {"type": "array"}
list[str]   → {"type": "array", "items": {"type": "string"}}
list[int]   → {"type": "array", "items": {"type": "integer"}}
dict        → {"type": "object"}
Optional[X] → type X, parameter NOT added to "required" list
X | None    → same as Optional[X]

For complex nested types (e.g., list[dict]), use {"type": "array", "items": {"type": "object"}}.
Don't attempt deep recursive schema generation — keep it pragmatic.

## Display Function

A tool can optionally register a display function that generates a human-readable
description for the confirmation UI:

    @my_tool.display
    def my_tool_display(**kwargs) -> str:
        emp = Employee.objects.get(id=kwargs["employee_id"])
        return f"Flag '{kwargs['topic']}' as weak area for {emp.name}"

The display function:
- Receives the same kwargs as the tool function
- Returns a string shown in the confirmation UI instead of raw JSON
- Can make DB queries to resolve IDs to human-readable names
- Should NOT have side effects
- Is optional — if not registered, the confirmation UI shows raw tool_input JSON

## Implementation Details
"""

import inspect
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, get_type_hints, get_origin, get_args

# Sentinel for "no default provided"
_MISSING = object()


class ToolSafety(Enum):
    READ_ONLY = "read_only"    # Only reads data, no side effects
    WRITE = "write"            # Modifies data in the database
    EXTERNAL = "external"      # Calls external services (Slack, email, webhooks, etc.)


class ToolParam:
    """
    Parameter descriptor providing metadata for LLM schema generation.
    
    Usage:
        @tool(name="get_scores", description="Get employee scores")
        def get_scores(
            employee_id: int = ToolParam(description="The employee's database ID"),
            days: int = ToolParam(description="Days to look back", default=7),
            section: str = ToolParam(
                description="Section filter",
                default=None,
                enum=["pharma", "ai_tech", "technical", "domain_process"],
            ),
        ) -> dict:
            ...
    """
    
    def __init__(
        self,
        description: str,
        default: Any = _MISSING,
        enum: list | None = None,
    ):
        self.description = description
        self.default = default
        self.enum = enum


@dataclass
class ToolMeta:
    """All metadata about a registered tool, attached to func._tool_meta."""
    name: str
    description: str
    section: str
    safety: ToolSafety
    requires_confirmation: bool
    timeout_seconds: int
    rate_limit: int | None          # Max calls per minute, None = unlimited
    parameters_schema: dict         # JSON Schema for LLM tool-use
    python_path: str                # "assessments.tools.get_employee_score_history"
    return_type: str | None         # "dict", "list[str]", etc. (for documentation)
    display_func: Callable | None   # The @tool_name.display function, if registered
    schema_hash: str                # SHA256 of parameters_schema for change detection


class _ToolDecorator:
    """
    Wrapper returned by @tool that supports the .display sub-decorator.
    
    This allows:
        @tool(name="my_tool", description="...")
        def my_tool(...):
            ...
        
        @my_tool.display
        def my_tool_display(**kwargs) -> str:
            return "Human-readable description"
    """
    
    def __init__(self, func: Callable, meta: ToolMeta):
        self._func = func
        self._meta = meta
        # Copy function attributes so it still behaves like the original function
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__
    
    def __call__(self, *args, **kwargs):
        """Call the original function directly."""
        return self._func(*args, **kwargs)
    
    def display(self, display_func: Callable) -> Callable:
        """
        Register a display function for this tool.
        
        Usage:
            @my_tool.display
            def my_tool_display(**kwargs) -> str:
                return "Human-readable description"
        """
        self._meta.display_func = display_func
        self._func._tool_meta = self._meta  # Update the meta on the original func
        return display_func


def tool(
    name: str,
    description: str,
    section: str = "general",
    safety: ToolSafety = ToolSafety.READ_ONLY,
    requires_confirmation: bool = False,
    timeout_seconds: int = 30,
    rate_limit: int | None = None,
) -> Callable:
    """
    Decorator that registers a function as an LLM tool.
    
    Args:
        name: Unique tool name. This is what the LLM sees and calls.
              Convention: snake_case, descriptive. e.g., "get_employee_score_history"
        description: What this tool does. Written FOR the LLM — should clearly explain
                     when and why the LLM should use this tool. Max ~200 words.
        section: Grouping for panel UI. e.g., "assessments", "notifications", "analytics"
        safety: READ_ONLY (no side effects), WRITE (modifies DB), EXTERNAL (external service)
        requires_confirmation: If True, execution needs human approval (see confirmation.py)
        timeout_seconds: Max execution time. Tool is killed after this.
        rate_limit: Max calls per minute across all agents. None = unlimited.
    
    Returns:
        A _ToolDecorator wrapper that supports .display sub-decorator.
    """
    
    def decorator(func: Callable) -> _ToolDecorator:
        # Step 1: Extract type hints and parameters
        hints = get_type_hints(func)
        sig = inspect.signature(func)
        
        # Step 2: Build JSON Schema from signature
        schema = _build_parameters_schema(func, hints, sig)
        
        # Step 3: Extract return type annotation
        return_type = None
        if 'return' in hints:
            return_type = _type_to_string(hints['return'])
        
        # Step 4: Compute python path
        python_path = f"{func.__module__}.{func.__qualname__}"
        
        # Step 5: Compute schema hash for change detection
        schema_hash = hashlib.sha256(
            json.dumps(schema, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        # Step 6: Create ToolMeta
        meta = ToolMeta(
            name=name,
            description=description,
            section=section,
            safety=safety,
            requires_confirmation=requires_confirmation,
            timeout_seconds=timeout_seconds,
            rate_limit=rate_limit,
            parameters_schema=schema,
            python_path=python_path,
            return_type=return_type,
            display_func=None,  # Set later via @tool_name.display
            schema_hash=schema_hash,
        )
        
        # Step 7: Attach meta to the original function
        func._tool_meta = meta
        
        # Step 8: Register in global registry
        from zango.ai.tools.registry import TOOL_REGISTRY
        TOOL_REGISTRY[name] = func
        
        # Step 9: Return wrapper that supports .display
        return _ToolDecorator(func, meta)
    
    return decorator


def _build_parameters_schema(func, hints, sig) -> dict:
    """
    Build a JSON Schema for the function's parameters.
    
    This is the schema that gets sent to the LLM in the tool definition.
    It must be a valid JSON Schema object with "type": "object", "properties", 
    and "required" fields.
    
    Rules:
    - Parameters with ToolParam(default=_MISSING) or no default → required
    - Parameters with ToolParam(default=<value>) → optional (not in required list)
    - Parameters with ToolParam(enum=[...]) → add "enum" constraint
    - The 'self' parameter is skipped (for methods)
    - The 'return' type hint is NOT included
    """
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        
        # Get type hint
        python_type = hints.get(param_name, str)
        
        # Get ToolParam descriptor (if parameter default is a ToolParam)
        tool_param = None
        if isinstance(param.default, ToolParam):
            tool_param = param.default
        
        # Build property schema
        prop = _python_type_to_json_schema(python_type)
        
        # Add description
        if tool_param:
            prop["description"] = tool_param.description
        else:
            # Generate from parameter name: "employee_id" → "employee id"
            prop["description"] = param_name.replace("_", " ")
        
        # Add enum constraint
        if tool_param and tool_param.enum:
            prop["enum"] = tool_param.enum
        
        properties[param_name] = prop
        
        # Determine if required
        if tool_param:
            if tool_param.default is _MISSING:
                required.append(param_name)
        elif param.default is inspect.Parameter.empty:
            required.append(param_name)
    
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def _python_type_to_json_schema(python_type) -> dict:
    """
    Convert a Python type annotation to a JSON Schema type definition.
    
    Mappings:
    str         → {"type": "string"}
    int         → {"type": "integer"}
    float       → {"type": "number"}
    bool        → {"type": "boolean"}
    list        → {"type": "array"}
    list[str]   → {"type": "array", "items": {"type": "string"}}
    list[int]   → {"type": "array", "items": {"type": "integer"}}
    dict        → {"type": "object"}
    Optional[X] → schema for X (optionality handled by required list)
    X | None    → schema for X
    
    For unrecognized types, default to {"type": "string"}.
    """
    # Handle Optional[X] and X | None
    origin = get_origin(python_type)
    args = get_args(python_type)
    
    # Union types (Optional[X] is Union[X, None])
    if origin is type(int | str):  # types.UnionType for X | Y syntax
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            return _python_type_to_json_schema(non_none_args[0])
    
    # typing.Optional / typing.Union
    import typing
    if origin is typing.Union:
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            return _python_type_to_json_schema(non_none_args[0])
    
    # list[X]
    if origin is list:
        schema = {"type": "array"}
        if args:
            schema["items"] = _python_type_to_json_schema(args[0])
        return schema
    
    # dict[K, V] → just "object"
    if origin is dict:
        return {"type": "object"}
    
    # Simple types
    type_map = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }
    
    return type_map.get(python_type, {"type": "string"})


def _type_to_string(python_type) -> str:
    """Convert a type annotation to a human-readable string for documentation."""
    origin = get_origin(python_type)
    args = get_args(python_type)
    
    if origin is list and args:
        return f"list[{_type_to_string(args[0])}]"
    if origin is dict and args:
        return f"dict[{_type_to_string(args[0])}, {_type_to_string(args[1])}]"
    
    if hasattr(python_type, '__name__'):
        return python_type.__name__
    
    return str(python_type)
```

---

### 3. `zango/ai/tools/registry.py`

```python
"""
In-memory registry of all discovered @tool functions.

## Lifecycle

1. App starts up
2. autodiscover_tools() scans all tools.py files in the workspace
3. Importing each file triggers @tool decorators → TOOL_REGISTRY populated
4. sync_tools_to_db() mirrors TOOL_REGISTRY → AppLLMTool table
   - New tools → create DB records
   - Changed tools (schema_hash differs) → update DB records
   - Removed tools (in DB but not in registry) → mark is_active=False

## Discovery Pattern

Like Celery's autodiscovery of tasks.py, we scan:
  workspaces/{app_name}/*/tools.py
  workspaces/{app_name}/*/*/tools.py

This is called from the app's startup hook (Zango's equivalent of Django's 
AppConfig.ready() method).

## Thread Safety

TOOL_REGISTRY is populated at startup before any requests are served.
It is read-only after startup. No locking needed.

## Implementation
"""

import importlib
import os
import glob
import logging
from typing import Callable

logger = logging.getLogger("zango.ai.tools")

# The global registry: tool_name → decorated function (with _tool_meta)
TOOL_REGISTRY: dict[str, Callable] = {}


def autodiscover_tools(workspace_path: str) -> int:
    """
    Scan all tools.py files in the workspace and import them.
    Importing triggers @tool decorators which populate TOOL_REGISTRY.
    
    Args:
        workspace_path: Absolute path to the app workspace directory.
                        e.g., "/zango/zango_project/workspaces/assesshq/"
    
    Returns:
        Number of tools discovered.
    
    Discovery patterns:
        {workspace_path}/*/tools.py         → e.g., assessments/tools.py
        {workspace_path}/*/*/tools.py       → e.g., backend/assessments/tools.py
    
    Implementation:
    1. Use glob to find all matching tools.py files
    2. Convert file paths to module paths (relative to workspace)
    3. Import each module using importlib.import_module()
    4. On import error: log warning, continue with next file (don't crash the app)
    5. Return count of newly registered tools
    """
    initial_count = len(TOOL_REGISTRY)
    
    patterns = [
        os.path.join(workspace_path, "*/tools.py"),
        os.path.join(workspace_path, "*/*/tools.py"),
        os.path.join(workspace_path, "*/*/*/tools.py"),
    ]
    
    discovered_files = set()
    for pattern in patterns:
        discovered_files.update(glob.glob(pattern))
    
    for file_path in sorted(discovered_files):
        module_path = _file_path_to_module(file_path, workspace_path)
        if module_path:
            try:
                importlib.import_module(module_path)
                logger.info(f"Discovered tools from: {module_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to import tools from {module_path}: {e}",
                    exc_info=True,
                )
    
    new_count = len(TOOL_REGISTRY) - initial_count
    logger.info(f"Tool autodiscovery complete: {new_count} new tools, {len(TOOL_REGISTRY)} total")
    return new_count


def _file_path_to_module(file_path: str, workspace_path: str) -> str | None:
    """
    Convert a file path to a Python module path.
    
    /zango/zango_project/workspaces/assesshq/backend/assessments/tools.py
    → backend.assessments.tools
    
    The exact conversion depends on how Zango adds workspace paths to sys.path.
    This function should align with Zango's module loading convention.
    """
    # Implementation depends on Zango's sys.path setup
    # Typically: workspace_path is on sys.path, so we compute relative to it
    rel_path = os.path.relpath(file_path, workspace_path)
    # "backend/assessments/tools.py" → "backend.assessments.tools"
    module_path = rel_path.replace(os.sep, ".").replace(".py", "")
    return module_path


def sync_tools_to_db() -> dict:
    """
    Synchronize TOOL_REGISTRY with the AppLLMTool database table.
    
    Returns:
        {"created": int, "updated": int, "deactivated": int}
    
    Steps:
    1. Load all existing AppLLMTool records into a dict keyed by name
    2. For each tool in TOOL_REGISTRY:
       a. If exists in DB:
          - Compare schema_hash. If different:
            - Update: description, parameters_schema, python_path, section,
              safety, requires_confirmation, timeout_seconds, rate_limit,
              return_type, has_display_func, schema_hash, is_active=True
          - If same schema_hash but is_active=False:
            - Re-activate (code was re-added)
       b. If not in DB:
          - Create new AppLLMTool record with all fields from ToolMeta
    3. For AppLLMTool records where name is NOT in TOOL_REGISTRY:
       - Set is_active=False (code was removed)
       - Do NOT delete — record may be referenced by historical invocation logs
    4. Update last_synced_at on all touched records
    
    This function is called:
    - On app startup (after autodiscover_tools)
    - On manual sync from the panel (POST /api/v1/ai/tools/sync/)
    - After code deployments
    """
    from zango.ai.models.tool import AppLLMTool
    
    stats = {"created": 0, "updated": 0, "deactivated": 0}
    
    existing = {t.name: t for t in AppLLMTool.objects.all()}
    discovered_names = set()
    
    for name, func in TOOL_REGISTRY.items():
        meta = func._tool_meta
        discovered_names.add(name)
        
        if name in existing:
            tool_record = existing[name]
            needs_update = (
                tool_record.schema_hash != meta.schema_hash
                or not tool_record.is_active
                or tool_record.description != meta.description
                or tool_record.section != meta.section
                or tool_record.safety != meta.safety.value
                or tool_record.requires_confirmation != meta.requires_confirmation
            )
            if needs_update:
                tool_record.description = meta.description
                tool_record.section = meta.section
                tool_record.safety = meta.safety.value
                tool_record.requires_confirmation = meta.requires_confirmation
                tool_record.timeout_seconds = meta.timeout_seconds
                tool_record.rate_limit_rpm = meta.rate_limit
                tool_record.parameters_schema = meta.parameters_schema
                tool_record.python_path = meta.python_path
                tool_record.return_type = meta.return_type
                tool_record.has_display_func = meta.display_func is not None
                tool_record.schema_hash = meta.schema_hash
                tool_record.is_active = True
                tool_record.save()
                stats["updated"] += 1
        else:
            AppLLMTool.objects.create(
                name=name,
                description=meta.description,
                section=meta.section,
                safety=meta.safety.value,
                requires_confirmation=meta.requires_confirmation,
                timeout_seconds=meta.timeout_seconds,
                rate_limit_rpm=meta.rate_limit,
                parameters_schema=meta.parameters_schema,
                python_path=meta.python_path,
                return_type=meta.return_type,
                has_display_func=meta.display_func is not None,
                schema_hash=meta.schema_hash,
                is_active=True,
            )
            stats["created"] += 1
    
    # Deactivate tools no longer in code
    stale_names = set(existing.keys()) - discovered_names
    if stale_names:
        count = AppLLMTool.objects.filter(
            name__in=stale_names, is_active=True
        ).update(is_active=False)
        stats["deactivated"] = count
    
    return stats


def get_tool_function(name: str) -> Callable:
    """
    Look up a tool function by name.
    
    Raises ToolNotFound if the name is not in TOOL_REGISTRY.
    """
    func = TOOL_REGISTRY.get(name)
    if func is None:
        from zango.ai.exceptions import ToolNotFound
        raise ToolNotFound(f"Tool '{name}' not found in registry")
    return func


def get_all_tool_metas() -> list:
    """Return ToolMeta for all registered tools."""
    return [func._tool_meta for func in TOOL_REGISTRY.values()]
```

---

### 4. `zango/ai/tools/executor.py`

```python
"""
Executes tool functions with safety wrapping.

## Responsibilities
- Validate tool input against the JSON Schema
- Apply timeout enforcement
- Call the function
- Serialize the return value to JSON-safe format
- Capture and sanitize errors
- Return a structured ToolResult

## Error Philosophy
The executor NEVER raises exceptions to the caller. All outcomes are captured
in ToolResult. The agent pipeline decides how to handle errors:
- For tool_use agents: feed the error back to the LLM as a tool result
  (the LLM may retry or work around it)
- For critical failures: abort the invocation

## Timeout Enforcement
Use threading (not signal) for timeout because:
- signal.alarm only works in the main thread
- Celery workers run in worker threads
- threading.Timer + concurrent.futures.ThreadPoolExecutor is portable

## Implementation
"""

import json
import time
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from typing import Any

import jsonschema

logger = logging.getLogger("zango.ai.tools")


@dataclass
class ToolResult:
    """Outcome of a tool execution attempt."""
    output: Any               # The function's return value (JSON-serializable)
    status: str               # "success", "error", "timeout", "validation_error"
    execution_time_ms: int    # Wall time in milliseconds
    error_message: str | None = None   # Sanitized error message (safe to show to LLM)
    error_traceback: str | None = None # Full traceback (for internal logging only, never sent to LLM)


# Thread pool for tool execution with timeout
_executor_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="tool-exec")


class ToolExecutor:
    """
    Executes registered tool functions with safety wrapping.
    
    Usage (called by the agent pipeline):
        executor = ToolExecutor()
        result = executor.execute("get_recent_topics", {"employee_id": 42, "hours": 48})
    """
    
    def execute(self, tool_name: str, tool_input: dict) -> ToolResult:
        """
        Execute a tool function by name with the given input.
        
        Steps:
        1. Look up function in TOOL_REGISTRY
        2. Validate tool_input against parameters_schema
        3. Execute function with timeout
        4. Serialize return value
        5. Return ToolResult
        
        Never raises — all outcomes captured in ToolResult.
        """
        start_time = time.monotonic()
        
        # Step 1: Look up function
        from zango.ai.tools.registry import get_tool_function
        try:
            func = get_tool_function(tool_name)
        except Exception as e:
            return ToolResult(
                output=None,
                status="error",
                execution_time_ms=0,
                error_message=f"Tool '{tool_name}' not found in registry",
            )
        
        meta = func._tool_meta
        
        # Step 2: Validate input against schema
        validation_error = self._validate_input(tool_input, meta.parameters_schema)
        if validation_error:
            elapsed = int((time.monotonic() - start_time) * 1000)
            return ToolResult(
                output=None,
                status="validation_error",
                execution_time_ms=elapsed,
                error_message=f"Invalid input: {validation_error}",
            )
        
        # Step 3: Execute with timeout
        try:
            future = _executor_pool.submit(func, **tool_input)
            raw_result = future.result(timeout=meta.timeout_seconds)
        except FuturesTimeoutError:
            elapsed = int((time.monotonic() - start_time) * 1000)
            logger.warning(
                f"Tool '{tool_name}' timed out after {meta.timeout_seconds}s",
                extra={"tool_input": tool_input},
            )
            return ToolResult(
                output=None,
                status="timeout",
                execution_time_ms=elapsed,
                error_message=f"Tool execution timed out after {meta.timeout_seconds}s",
            )
        except Exception as e:
            elapsed = int((time.monotonic() - start_time) * 1000)
            tb = traceback.format_exc()
            logger.error(
                f"Tool '{tool_name}' raised {type(e).__name__}: {e}",
                extra={"tool_input": tool_input},
                exc_info=True,
            )
            return ToolResult(
                output=None,
                status="error",
                execution_time_ms=elapsed,
                error_message=f"Tool execution failed: {type(e).__name__}: {str(e)[:500]}",
                error_traceback=tb,
            )
        
        # Step 4: Serialize return value
        elapsed = int((time.monotonic() - start_time) * 1000)
        try:
            serialized = self._serialize_output(raw_result)
        except Exception as e:
            return ToolResult(
                output=str(raw_result)[:2000],
                status="error",
                execution_time_ms=elapsed,
                error_message=f"Tool returned non-serializable value: {type(e).__name__}",
            )
        
        return ToolResult(
            output=serialized,
            status="success",
            execution_time_ms=elapsed,
        )
    
    def _validate_input(self, tool_input: dict, schema: dict) -> str | None:
        """
        Validate tool_input against the JSON Schema.
        Returns None on success, error message string on failure.
        
        Uses jsonschema.validate(). Catches ValidationError and returns 
        a human-readable message.
        """
        try:
            jsonschema.validate(instance=tool_input, schema=schema)
            return None
        except jsonschema.ValidationError as e:
            return e.message
        except Exception as e:
            return f"Schema validation error: {str(e)}"
    
    def _serialize_output(self, value: Any) -> Any:
        """
        Ensure the return value is JSON-serializable.
        
        Handles common Django/Python types:
        - QuerySet → list
        - Model instance → str(instance)
        - datetime → .isoformat()
        - Decimal → float
        - set → list
        - bytes → base64 string
        - Everything else → attempt json.dumps, fall back to str()
        
        Truncates large outputs to 50KB to prevent bloating the LLM context.
        """
        import datetime
        from decimal import Decimal
        
        if value is None:
            return None
        
        if isinstance(value, (str, int, float, bool)):
            return value
        
        if isinstance(value, Decimal):
            return float(value)
        
        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.isoformat()
        
        if isinstance(value, set):
            return list(value)
        
        if isinstance(value, bytes):
            import base64
            return base64.b64encode(value).decode('ascii')
        
        # Try JSON round-trip to ensure serializability
        try:
            json_str = json.dumps(value, default=str)
            if len(json_str) > 50000:
                # Truncate large outputs
                return json.loads(json_str[:50000] + '..."')
            return json.loads(json_str)
        except (TypeError, ValueError):
            return str(value)[:2000]
```

---

### 5. `zango/ai/tools/confirmation.py`

```python
"""
Confirmation resolution pipeline for tool calls with side effects.

## Three Execution Contexts

1. interactive — User is present (request/response or chat)
   Confirmable tools pause execution, return to frontend for approval.

2. background — No user present (Celery task, cron job)
   Policy-driven: auto_approve, deny_all, per_tool_policy, or queue_for_human.

3. system — Internal framework calls (housekeeping, summarization)
   Always auto-approve.

## Resolution Flow

resolve_tool_call() is called by the agent pipeline when it encounters a 
tool call from the LLM. It returns one of three outcomes:
- ('execute', None) → execute immediately
- ('confirm', AppLLMToolConfirmation) → pause and wait for human
- ('deny', reason_string) → skip this tool call, tell LLM it was denied

## Resume Flow

resume_after_confirmation() is called when a human approves/denies a 
pending confirmation (via the panel API). It:
1. Loads the saved pipeline state
2. Executes or skips the tool based on the decision
3. Resumes the agent pipeline from where it paused
4. This may trigger further LLM calls

## Implementation
"""

from datetime import timedelta
from django.utils import timezone
from typing import Tuple, Optional

from zango.ai.models.confirmation import AppLLMToolConfirmation


def resolve_tool_call(
    agent,              # AppLLMAgent instance
    tool_meta,          # ToolMeta from the decorated function
    tool_input: dict,   # What the LLM wants to pass to the tool
    execution_context: str,  # "interactive", "background", "system"
    invocation,         # AppLLMInvocation instance (for FK reference)
    round_number: int,  # Current tool-use round
    pipeline_state: dict,  # Serialized pipeline state for resume
) -> Tuple[str, Optional[AppLLMToolConfirmation], Optional[str]]:
    """
    Decide whether to execute, confirm, or deny a tool call.
    
    Returns:
        ('execute', None, None)                          → proceed immediately
        ('confirm', AppLLMToolConfirmation, None)        → pause and wait
        ('deny', None, "reason string")                  → skip
    """
    from zango.ai.tools.decorator import ToolSafety
    from zango.ai.models.agent import AppLLMAgentToolConfig
    
    # Step 1: Read-only tools never need confirmation
    if tool_meta.safety == ToolSafety.READ_ONLY:
        return ('execute', None, None)
    
    # Step 2: Tool doesn't require confirmation
    if not tool_meta.requires_confirmation:
        return ('execute', None, None)
    
    # Step 3: System context always auto-approves
    if execution_context == 'system':
        return ('execute', None, None)
    
    # Step 4: Interactive context — always pause for human
    if execution_context == 'interactive':
        confirmation = _create_confirmation(
            agent, tool_meta, tool_input, invocation, round_number,
            pipeline_state,
        )
        return ('confirm', confirmation, None)
    
    # Step 5: Background context — policy-driven
    if execution_context == 'background':
        policy = agent.background_confirmation_policy
        
        if policy == 'auto_approve':
            # Log as auto-approved but execute immediately
            return ('execute', None, None)
        
        if policy == 'deny_all':
            return ('deny', None, 'background_policy_deny_all')
        
        if policy == 'queue':
            confirmation = _create_confirmation(
                agent, tool_meta, tool_input, invocation, round_number,
                pipeline_state,
            )
            _notify_admins_of_pending_confirmation(confirmation)
            return ('confirm', confirmation, None)
        
        if policy == 'policy':
            # Look up per-tool config for this agent
            try:
                agent_tool_config = AppLLMAgentToolConfig.objects.get(
                    agent=agent,
                    tool__name=tool_meta.name,
                )
            except AppLLMAgentToolConfig.DoesNotExist:
                return ('deny', None, 'no_background_policy_for_tool')
            
            if agent_tool_config.auto_approve_in_background:
                # Check conditions if any
                if agent_tool_config.auto_approve_conditions:
                    if _check_conditions(agent_tool_config.auto_approve_conditions, tool_input):
                        return ('execute', None, None)
                    else:
                        return ('deny', None, 'auto_approve_conditions_not_met')
                else:
                    return ('execute', None, None)
            else:
                return ('deny', None, 'tool_policy_deny_in_background')
    
    # Fallback: deny unknown contexts
    return ('deny', None, f'unknown_execution_context:{execution_context}')


def _create_confirmation(
    agent, tool_meta, tool_input, invocation, round_number, pipeline_state,
) -> AppLLMToolConfirmation:
    """
    Create a pending confirmation record.
    
    Steps:
    1. Generate display text (call tool's display function if available)
    2. Create AppLLMToolConfirmation record
    3. Set expiry based on agent.confirmation_expiry_seconds
    4. Return the confirmation object
    """
    from zango.ai.models.tool import AppLLMTool
    
    # Get display text
    display_text = ""
    if tool_meta.display_func:
        try:
            display_text = tool_meta.display_func(**tool_input)
        except Exception as e:
            display_text = f"(Display function error: {e})"
    
    if not display_text:
        # Fallback: generate from tool name and input
        import json
        display_text = f"Execute {tool_meta.name} with: {json.dumps(tool_input, indent=2)[:500]}"
    
    # Get tool DB record
    tool_record = None
    try:
        tool_record = AppLLMTool.objects.get(name=tool_meta.name)
    except AppLLMTool.DoesNotExist:
        pass
    
    confirmation = AppLLMToolConfirmation.objects.create(
        invocation=invocation,
        tool=tool_record,
        tool_name=tool_meta.name,
        tool_input=tool_input,
        tool_input_display=display_text,
        pipeline_state=pipeline_state,
        round_number=round_number,
        status='pending',
        expires_at=timezone.now() + timedelta(seconds=agent.confirmation_expiry_seconds),
    )
    
    return confirmation


def _check_conditions(conditions: dict, tool_input: dict) -> bool:
    """
    Check if tool_input satisfies auto-approve conditions.
    
    Conditions format:
    {
        "max_severity": "moderate",          # tool_input["severity"] must be <= this
        "only_for_sections": ["assessments"], # tool_input values checked against allowed lists
        "max_count": 5,                       # numeric upper bounds
    }
    
    Condition checking rules:
    - "max_<field>": The value of tool_input[field] must be <= conditions[max_<field>]
      For string comparisons, uses ordinal: "mild" < "moderate" < "severe"
    - "only_for_<field>": tool_input[field] must be in conditions[only_for_<field>]
    - "equals_<field>": tool_input[field] must exactly equal conditions[equals_<field>]
    
    All conditions must pass (AND logic). If a condition references a field
    not in tool_input, the condition is skipped (not failed).
    
    Returns True if all conditions pass, False if any fails.
    """
    severity_order = {"mild": 1, "moderate": 2, "severe": 3}
    
    for key, expected in conditions.items():
        if key.startswith("max_"):
            field = key[4:]
            actual = tool_input.get(field)
            if actual is None:
                continue
            # String severity comparison
            if isinstance(actual, str) and actual in severity_order:
                if severity_order.get(actual, 99) > severity_order.get(expected, 99):
                    return False
            # Numeric comparison
            elif isinstance(actual, (int, float)):
                if actual > expected:
                    return False
        
        elif key.startswith("only_for_"):
            field = key[9:]
            actual = tool_input.get(field)
            if actual is None:
                continue
            if actual not in expected:
                return False
        
        elif key.startswith("equals_"):
            field = key[7:]
            actual = tool_input.get(field)
            if actual is None:
                continue
            if actual != expected:
                return False
    
    return True


def _notify_admins_of_pending_confirmation(confirmation):
    """
    Send notification to admins about a pending confirmation.
    
    Implementation options (in order of preference):
    1. If Slack integration is configured: send Slack message to admin channel
    2. If email is configured: send email to admin users
    3. Always: the panel shows pending confirmations count in the badge
    
    This is a best-effort notification — if it fails, the confirmation
    still exists in the DB and will show in the panel.
    """
    import logging
    logger = logging.getLogger("zango.ai.tools")
    logger.info(
        f"Pending tool confirmation: {confirmation.tool_name} "
        f"(invocation={confirmation.invocation_id}, expires={confirmation.expires_at})"
    )
    # TODO: Implement Slack/email notification
    # For now, panel badge is the notification mechanism


def resume_after_confirmation(
    confirmation_id: int,
    decision: str,          # "approved" or "denied"
    decided_by_user=None,   # The user who made the decision
    denial_reason: str = "",
):
    """
    Resume a paused agent pipeline after confirmation decision.
    
    Called from:
    - Panel API: POST /api/v1/ai/confirmations/{id}/decide/
    - Celery task: resume_agent_after_confirmation
    
    Steps:
    1. Load AppLLMToolConfirmation
    2. Validate status is 'pending' and not expired
    3. Update confirmation with decision
    4. If approved:
       a. Execute the tool via ToolExecutor
       b. Load pipeline_state
       c. Resume agent pipeline from saved state
    5. If denied:
       a. Create a tool result with denial message
       b. Resume agent pipeline — LLM sees denial and continues
    6. Return the final AgentResult (from resumed pipeline)
    
    Raises:
    - ConfirmationNotFound if ID doesn't exist
    - ConfirmationAlreadyDecided if status != 'pending'
    - ConfirmationExpired if expires_at < now
    """
    confirmation = AppLLMToolConfirmation.objects.select_related(
        'invocation', 'invocation__agent', 'tool'
    ).get(id=confirmation_id)
    
    # Validate state
    if confirmation.status != 'pending':
        from zango.ai.exceptions import ZangoAIError
        raise ZangoAIError(
            f"Confirmation {confirmation_id} is already {confirmation.status}"
        )
    
    if confirmation.expires_at < timezone.now():
        confirmation.status = 'expired'
        confirmation.decided_at = timezone.now()
        confirmation.save(update_fields=['status', 'decided_at'])
        from zango.ai.exceptions import ZangoAIError
        raise ZangoAIError(f"Confirmation {confirmation_id} has expired")
    
    # Record decision
    confirmation.status = decision  # "approved" or "denied"
    confirmation.decided_by_user = decided_by_user
    confirmation.decided_at = timezone.now()
    confirmation.denial_reason = denial_reason
    confirmation.save()
    
    # Resume pipeline
    from zango.ai.agents.pipeline import AgentPipeline
    pipeline = AgentPipeline()
    
    if decision == 'approved':
        # Execute the tool
        from zango.ai.tools.executor import ToolExecutor
        executor = ToolExecutor()
        tool_result = executor.execute(
            confirmation.tool_name,
            confirmation.tool_input,
        )
    else:
        # Create denied result
        from zango.ai.tools.executor import ToolResult
        tool_result = ToolResult(
            output={"error": f"Tool call denied by user: {denial_reason}"},
            status="denied",
            execution_time_ms=0,
            error_message=f"Denied: {denial_reason}",
        )
    
    # Resume the pipeline from saved state
    return pipeline.resume_from_state(
        invocation=confirmation.invocation,
        pipeline_state=confirmation.pipeline_state,
        tool_name=confirmation.tool_name,
        tool_result=tool_result,
        confirmation=confirmation,
    )
```

---

### 6. `zango/ai/models/tool.py`

```python
"""
Database models for tool management.

AppLLMTool: DB mirror of registered @tool functions. Synced from code on startup.
AppLLMToolCall: Log entry for each tool execution within an agent invocation.
"""

from django.db import models



class AppLLMTool(models.Model):
    """
    DB representation of a registered @tool function.
    
    Source of truth is CODE (the @tool decorator).
    DB records exist so the panel can:
    - Display all available tools with schemas
    - Attach/detach tools from agents
    - Track per-tool usage statistics
    - Show tool safety classifications
    
    Admins CANNOT create tools from the panel — tools are code-defined only.
    Admins CAN: view tools, attach/detach from agents, view call history.
    """
    
    # Identity (synced from @tool decorator)
    name = models.CharField(max_length=100, unique=True,
        help_text="The tool name as defined in @tool(name=...)")
    description = models.TextField(
        help_text="Tool description shown to the LLM and in the panel")
    section = models.CharField(max_length=50, default="general",
        help_text="Grouping category for panel UI: 'assessments', 'notifications', etc.")
    
    # JSON Schema for parameters — exactly what gets sent to the LLM
    parameters_schema = models.JSONField(
        help_text="JSON Schema describing the tool's input parameters")
    
    # Code reference
    python_path = models.CharField(max_length=255,
        help_text="Dotted import path: 'assessments.tools.flag_weak_area'")
    
    # Safety classification
    safety = models.CharField(max_length=20, choices=[
        ('read_only', 'Read Only — no side effects'),
        ('write', 'Write — modifies database'),
        ('external', 'External — calls external services'),
    ], default='read_only')
    
    # Execution controls
    requires_confirmation = models.BooleanField(default=False,
        help_text="If True, execution needs human approval before running")
    timeout_seconds = models.IntegerField(default=30,
        help_text="Max execution time before the tool call is killed")
    rate_limit_rpm = models.IntegerField(null=True, blank=True,
        help_text="Max calls per minute across all agents. Null = unlimited.")
    
    # Return type (for panel display, not enforced)
    return_type = models.CharField(max_length=100, null=True, blank=True,
        help_text="Return type annotation: 'dict', 'list[str]', etc.")
    
    # Display function availability
    has_display_func = models.BooleanField(default=False,
        help_text="True if a @tool_name.display function is registered")
    
    # Sync tracking
    is_active = models.BooleanField(default=True,
        help_text="False if @tool code was removed. Record kept for historical logs.")
    schema_hash = models.CharField(max_length=64,
        help_text="Hash of parameters_schema for change detection during sync")
    last_synced_at = models.DateTimeField(auto_now=True)
    
    # Usage stats (updated via signals or periodic aggregation)
    total_calls = models.IntegerField(default=0)
    total_errors = models.IntegerField(default=0)
    total_timeouts = models.IntegerField(default=0)
    avg_execution_ms = models.IntegerField(default=0,
        help_text="Rolling average execution time in milliseconds")
    last_called_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['section', 'name']
        indexes = [
            models.Index(fields=['is_active', 'section']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.section})"


class AppLLMToolCall(models.Model):
    """
    Log entry for each tool call within an agent invocation.
    One invocation may have multiple tool calls across multiple rounds.
    
    This is a CHILD record of AppLLMInvocation. The invocation is the 
    unit of audit; tool calls are the details within it.
    """
    
    # Parent invocation
    invocation = models.ForeignKey(
        'AppLLMInvocation', on_delete=models.CASCADE,
        related_name='tool_calls',
        help_text="The agent invocation this tool call is part of")
    
    # Tool reference
    tool = models.ForeignKey(
        AppLLMTool, on_delete=models.SET_NULL, null=True,
        help_text="FK to the tool record. Null if tool was removed after the call.")
    tool_name = models.CharField(max_length=100,
        help_text="Denormalized tool name — preserved even if tool record is deleted")
    
    # What the LLM requested
    tool_input = models.JSONField(
        help_text="The arguments the LLM passed to the tool")
    
    # What the function returned
    tool_output = models.JSONField(null=True, blank=True,
        help_text="The tool function's return value. Null if tool wasn't executed.")
    
    # Execution metadata
    round_number = models.IntegerField(
        help_text="Which tool-use round this call was part of (1, 2, 3...)")
    execution_time_ms = models.IntegerField(null=True, blank=True,
        help_text="How long the tool function took to execute")
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('error', 'Error — function raised exception'),
        ('timeout', 'Timeout — exceeded timeout_seconds'),
        ('validation_error', 'Validation Error — input failed schema validation'),
        ('denied', 'Denied — blocked by confirmation policy'),
        ('pending', 'Pending — awaiting confirmation'),
    ])
    error_message = models.TextField(null=True, blank=True,
        help_text="Error message if status is error/timeout/validation_error")
    error_traceback = models.TextField(null=True, blank=True,
        help_text="Full Python traceback for debugging. Never sent to LLM.")
    
    # Confirmation tracking
    confirmation = models.ForeignKey(
        'AppLLMToolConfirmation', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tool_call',
        help_text="Link to confirmation record if this tool required confirmation")
    confirmation_decision = models.CharField(max_length=20, null=True, blank=True,
        choices=[
            ('auto_approved', 'Auto-approved (no confirmation needed)'),
            ('auto_approved_by_policy', 'Auto-approved by agent policy'),
            ('approved', 'Approved by human'),
            ('denied', 'Denied by human'),
            ('denied_by_policy', 'Denied by agent policy'),
            ('expired', 'Confirmation expired'),
        ],
        help_text="How the confirmation was resolved, if applicable")
    confirmation_decided_by = models.CharField(max_length=255, null=True, blank=True,
        help_text="Who/what made the confirmation decision. "
                  "User email, or 'policy:agent.background_policy.per_tool'")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['invocation', 'round_number', 'created_at']
        indexes = [
            models.Index(fields=['invocation', 'round_number']),
            models.Index(fields=['tool_name', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.tool_name} (round {self.round_number}, {self.status})"
```

---

### 7. `zango/ai/models/confirmation.py`

```python
"""
Tool confirmation model for pause/resume flow.
"""

from django.db import models


class AppLLMToolConfirmation(models.Model):
    """
    Created when a tool with requires_confirmation=True is invoked.
    
    Stores the pipeline state so the agent can resume from exactly 
    where it paused after the confirmation decision.
    """
    
    # Parent invocation
    invocation = models.ForeignKey(
        'AppLLMInvocation', on_delete=models.CASCADE,
        related_name='confirmations',
        help_text="The agent invocation that triggered this confirmation")
    
    # Tool details
    tool = models.ForeignKey(
        'AppLLMTool', on_delete=models.SET_NULL, null=True)
    tool_name = models.CharField(max_length=100)
    tool_input = models.JSONField(
        help_text="The arguments the LLM wants to pass to the tool")
    tool_input_display = models.TextField(blank=True, default="",
        help_text="Human-readable description from the tool's @display function. "
                  "Shown in the panel instead of raw JSON when available.")
    
    # Pipeline state for resume
    pipeline_state = models.JSONField(
        help_text="Serialized state of the agent pipeline at the point of pause. "
                  "Contains: messages so far, accumulated usage, round number, "
                  "other pending tool calls in this round, the assistant response "
                  "that triggered tools. Used to resume execution exactly.")
    round_number = models.IntegerField(
        help_text="The tool-use round when this confirmation was triggered")
    
    # Decision
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Awaiting decision'),
        ('approved', 'Approved by human'),
        ('denied', 'Denied by human'),
        ('auto_approved', 'Auto-approved (no confirmation was required)'),
        ('auto_approved_by_policy', 'Auto-approved by agent background policy'),
        ('expired', 'Expired without decision'),
    ], default='pending')
    
    decided_by_user = models.ForeignKey(
        'appauth.AppUserModel', null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="The user who approved/denied. Null for auto/policy decisions.")
    decided_by_policy = models.CharField(max_length=200, blank=True, default="",
        help_text="Which policy rule made the decision. "
                  "e.g., 'agent.background_policy.per_tool.auto_approve_conditions'")
    decided_at = models.DateTimeField(null=True, blank=True)
    denial_reason = models.TextField(blank=True, default="",
        help_text="Reason provided when denying the tool call")
    
    # Expiry
    expires_at = models.DateTimeField(
        help_text="Auto-deny/expire after this time. "
                  "Based on agent.confirmation_expiry_seconds.")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['invocation']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Confirmation for {self.tool_name} ({self.status})"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expires_at < timezone.now()
    
    @property
    def seconds_remaining(self):
        from django.utils import timezone
        delta = self.expires_at - timezone.now()
        return max(0, int(delta.total_seconds()))
```

---

### 8. `zango/ai/api/tool_serializers.py`

```python
"""
DRF serializers for the tools subsystem.
"""

from rest_framework import serializers
from zango.ai.models.tool import AppLLMTool, AppLLMToolCall
from zango.ai.models.confirmation import AppLLMToolConfirmation


class AppLLMToolListSerializer(serializers.ModelSerializer):
    """For the tools list view — compact summary."""
    agents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AppLLMTool
        fields = [
            'id', 'name', 'description', 'section', 'safety',
            'requires_confirmation', 'timeout_seconds', 'rate_limit_rpm',
            'return_type', 'has_display_func', 'is_active',
            'total_calls', 'total_errors', 'total_timeouts',
            'avg_execution_ms', 'last_called_at', 'last_synced_at',
            'agents_count',
        ]
    
    def get_agents_count(self, obj):
        """How many agents have this tool attached."""
        return obj.appllmagenttoolconfig_set.count()


class AppLLMToolDetailSerializer(serializers.ModelSerializer):
    """
    For tool detail view — includes full schema and agent list.
    """
    agents = serializers.SerializerMethodField()
    parameters_schema_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AppLLMTool
        fields = [
            'id', 'name', 'description', 'section', 'safety',
            'requires_confirmation', 'timeout_seconds', 'rate_limit_rpm',
            'parameters_schema', 'parameters_schema_display',
            'python_path', 'return_type', 'has_display_func',
            'is_active', 'schema_hash', 'last_synced_at',
            'total_calls', 'total_errors', 'total_timeouts',
            'avg_execution_ms', 'last_called_at',
            'agents',
        ]
    
    def get_agents(self, obj):
        """List of agents using this tool."""
        configs = obj.appllmagenttoolconfig_set.select_related('agent').all()
        return [
            {
                'agent_id': c.agent.id,
                'agent_name': c.agent.name,
                'agent_display_name': c.agent.display_name,
                'auto_approve_in_background': c.auto_approve_in_background,
                'auto_approve_conditions': c.auto_approve_conditions,
            }
            for c in configs
        ]
    
    def get_parameters_schema_display(self, obj):
        """
        Convert JSON Schema to a human-readable parameter list for the panel.
        
        Returns: [
            {"name": "employee_id", "type": "integer", "required": true, 
             "description": "The employee's database ID"},
            {"name": "days", "type": "integer", "required": false,
             "description": "Days to look back", "default": 7},
        ]
        """
        schema = obj.parameters_schema
        properties = schema.get('properties', {})
        required = set(schema.get('required', []))
        
        params = []
        for name, prop in properties.items():
            params.append({
                'name': name,
                'type': prop.get('type', 'string'),
                'required': name in required,
                'description': prop.get('description', ''),
                'enum': prop.get('enum'),
            })
        return params


class AppLLMToolCallListSerializer(serializers.ModelSerializer):
    """For tool call log list view."""
    invocation_id = serializers.CharField(source='invocation.id')
    agent_name = serializers.CharField(
        source='invocation.agent_name', default='')
    
    class Meta:
        model = AppLLMToolCall
        fields = [
            'id', 'invocation_id', 'agent_name',
            'tool_name', 'round_number',
            'tool_input', 'tool_output',
            'status', 'error_message',
            'execution_time_ms',
            'confirmation_decision', 'confirmation_decided_by',
            'created_at',
        ]


class AppLLMToolCallDetailSerializer(serializers.ModelSerializer):
    """Full detail for a single tool call."""
    
    class Meta:
        model = AppLLMToolCall
        fields = '__all__'


class AppLLMToolConfirmationListSerializer(serializers.ModelSerializer):
    """For pending confirmations list in the panel."""
    agent_name = serializers.CharField(
        source='invocation.agent_name', default='')
    seconds_remaining = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = AppLLMToolConfirmation
        fields = [
            'id', 'tool_name', 'tool_input', 'tool_input_display',
            'status', 'round_number', 'agent_name',
            'expires_at', 'seconds_remaining',
            'decided_by_user', 'decided_by_policy',
            'decided_at', 'denial_reason',
            'created_at',
        ]


class AppLLMToolConfirmationDetailSerializer(serializers.ModelSerializer):
    """Full detail for a confirmation."""
    agent_name = serializers.CharField(
        source='invocation.agent_name', default='')
    invocation_id = serializers.IntegerField(source='invocation.id')
    seconds_remaining = serializers.IntegerField(read_only=True)
    tool_safety = serializers.CharField(
        source='tool.safety', default='')
    
    class Meta:
        model = AppLLMToolConfirmation
        fields = [
            'id', 'invocation_id', 'agent_name',
            'tool_name', 'tool_safety',
            'tool_input', 'tool_input_display',
            'round_number',
            'status', 'expires_at', 'seconds_remaining',
            'decided_by_user', 'decided_by_policy',
            'decided_at', 'denial_reason',
            'created_at',
        ]
        # Exclude pipeline_state from API responses — it can be huge
        # and is internal implementation detail


class ConfirmationDecisionSerializer(serializers.Serializer):
    """Input serializer for POST /api/v1/ai/confirmations/{id}/decide/"""
    decision = serializers.ChoiceField(choices=['approved', 'denied'])
    reason = serializers.CharField(required=False, default="", allow_blank=True)
```

---

### 9. `zango/ai/api/tool_views.py`

```python
"""
REST API views for tool management and tool call logs.
All views are scoped to the current tenant (app).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from zango.ai.models.tool import AppLLMTool, AppLLMToolCall
from zango.ai.api.tool_serializers import (
    AppLLMToolListSerializer,
    AppLLMToolDetailSerializer,
    AppLLMToolCallListSerializer,
)


class ToolListView(APIView):
    """
    GET /api/v1/ai/tools/
    
    List all registered tools (from DB, synced from code).
    
    Query parameters:
    - section: filter by section (e.g., "assessments")
    - safety: filter by safety level ("read_only", "write", "external")
    - is_active: filter by active status ("true"/"false")
    - search: search by name or description
    
    Returns tools sorted by section, then name.
    Each tool includes: name, description, section, safety, requires_confirmation,
    parameters count, usage stats, number of agents using it.
    """
    
    def get(self, request):
        queryset = AppLLMTool.objects.all()
        
        # Filters
        section = request.query_params.get('section')
        if section:
            queryset = queryset.filter(section=section)
        
        safety = request.query_params.get('safety')
        if safety:
            queryset = queryset.filter(safety=safety)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search)
            )
        
        serializer = AppLLMToolListSerializer(queryset, many=True)
        return Response({"success": True, "tools": serializer.data})


class ToolDetailView(APIView):
    """
    GET /api/v1/ai/tools/{id}/
    
    Tool detail with full schema, parameter display, and list of agents using it.
    """
    
    def get(self, request, tool_id):
        tool = get_object_or_404(AppLLMTool, id=tool_id)
        serializer = AppLLMToolDetailSerializer(tool)
        return Response({"success": True, "tool": serializer.data})


class ToolCallsView(APIView):
    """
    GET /api/v1/ai/tools/{id}/calls/
    
    Recent tool call log entries for a specific tool. Paginated.
    
    Query parameters:
    - status: filter by status ("success", "error", "timeout", "denied")
    - page: page number (default 1)
    - page_size: items per page (default 25, max 100)
    """
    
    def get(self, request, tool_id):
        tool = get_object_or_404(AppLLMTool, id=tool_id)
        queryset = AppLLMToolCall.objects.filter(
            tool=tool
        ).select_related('invocation').order_by('-created_at')
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 25)), 100)
        offset = (page - 1) * page_size
        
        total = queryset.count()
        calls = queryset[offset:offset + page_size]
        
        serializer = AppLLMToolCallListSerializer(calls, many=True)
        return Response({
            "success": True,
            "calls": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            }
        })


class ToolSyncView(APIView):
    """
    POST /api/v1/ai/tools/sync/
    
    Force a tool sync — re-runs autodiscover + sync_tools_to_db.
    Useful after deploying new code.
    
    Returns sync stats: {"created": N, "updated": N, "deactivated": N}
    """
    
    def post(self, request):
        from zango.ai.tools.registry import autodiscover_tools, sync_tools_to_db
        
        # Determine workspace path for this tenant
        # Implementation depends on how Zango resolves tenant workspace paths
        workspace_path = self._get_workspace_path(request)
        
        autodiscover_tools(workspace_path)
        stats = sync_tools_to_db()
        
        return Response({
            "success": True,
            "message": "Tool sync complete",
            "stats": stats,
        })
    
    def _get_workspace_path(self, request):
        """
        Get the workspace path for the current tenant.
        Implementation depends on Zango's tenant resolution.
        """
        # TODO: Implement based on Zango's tenant workspace resolution
        pass


class ToolSectionsView(APIView):
    """
    GET /api/v1/ai/tools/sections/
    
    Returns distinct sections with tool counts per section.
    Used for the section filter dropdown in the panel.
    
    Returns: [
        {"section": "assessments", "count": 5, "active_count": 5},
        {"section": "notifications", "count": 3, "active_count": 2},
    ]
    """
    
    def get(self, request):
        from django.db.models import Count, Q
        
        sections = AppLLMTool.objects.values('section').annotate(
            count=Count('id'),
            active_count=Count('id', filter=Q(is_active=True)),
        ).order_by('section')
        
        return Response({
            "success": True,
            "sections": list(sections),
        })
```

---

### 10. `zango/ai/api/confirmation_views.py`

```python
"""
REST API views for tool confirmation management.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from zango.ai.models.confirmation import AppLLMToolConfirmation
from zango.ai.api.tool_serializers import (
    AppLLMToolConfirmationListSerializer,
    AppLLMToolConfirmationDetailSerializer,
    ConfirmationDecisionSerializer,
)


class ConfirmationListView(APIView):
    """
    GET /api/v1/ai/confirmations/
    
    List confirmations. Default: pending only.
    
    Query parameters:
    - status: "pending" (default), "approved", "denied", "expired", "all"
    - tool_name: filter by tool name
    - page, page_size: pagination
    """
    
    def get(self, request):
        queryset = AppLLMToolConfirmation.objects.select_related(
            'invocation', 'tool'
        ).all()
        
        status_filter = request.query_params.get('status', 'pending')
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        tool_name = request.query_params.get('tool_name')
        if tool_name:
            queryset = queryset.filter(tool_name=tool_name)
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 25)), 100)
        offset = (page - 1) * page_size
        
        total = queryset.count()
        confirmations = queryset[offset:offset + page_size]
        
        serializer = AppLLMToolConfirmationListSerializer(confirmations, many=True)
        return Response({
            "success": True,
            "confirmations": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
            }
        })


class ConfirmationDetailView(APIView):
    """
    GET /api/v1/ai/confirmations/{id}/
    
    Full confirmation detail including tool input, display text,
    and decision info.
    """
    
    def get(self, request, confirmation_id):
        confirmation = get_object_or_404(
            AppLLMToolConfirmation.objects.select_related('invocation', 'tool'),
            id=confirmation_id,
        )
        serializer = AppLLMToolConfirmationDetailSerializer(confirmation)
        return Response({"success": True, "confirmation": serializer.data})


class ConfirmationDecideView(APIView):
    """
    POST /api/v1/ai/confirmations/{id}/decide/
    
    Approve or deny a pending tool confirmation.
    
    Body: {
        "decision": "approved" or "denied",
        "reason": "optional denial reason"
    }
    
    On success:
    - Updates the confirmation record
    - If approved: executes the tool and resumes the agent pipeline
    - If denied: resumes pipeline with denial message to LLM
    - Returns the final AgentResult from the resumed pipeline
    
    Errors:
    - 400 if confirmation is not pending
    - 400 if confirmation has expired
    - 404 if not found
    """
    
    def post(self, request, confirmation_id):
        serializer = ConfirmationDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        decision = serializer.validated_data['decision']
        reason = serializer.validated_data.get('reason', '')
        
        from zango.ai.tools.confirmation import resume_after_confirmation
        
        try:
            result = resume_after_confirmation(
                confirmation_id=confirmation_id,
                decision=decision,
                decided_by_user=request.user if hasattr(request, 'user') else None,
                denial_reason=reason,
            )
            return Response({
                "success": True,
                "message": f"Tool call {decision}",
                "result": {
                    "content": result.content if result else None,
                    "status": result.status if result else None,
                    "invocation_id": result.invocation_id if result else None,
                }
            })
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PendingConfirmationsCountView(APIView):
    """
    GET /api/v1/ai/confirmations/pending-count/
    
    Returns just the count of pending confirmations.
    Used for the badge number in the panel nav.
    """
    
    def get(self, request):
        from django.utils import timezone
        count = AppLLMToolConfirmation.objects.filter(
            status='pending',
            expires_at__gt=timezone.now(),
        ).count()
        return Response({"success": True, "count": count})
```

---

### 11. URL Routing (add to `zango/ai/api/urls.py`)

```python
"""
Add these URL patterns to the AI framework URL configuration.
"""

from django.urls import path
from zango.ai.api.tool_views import (
    ToolListView,
    ToolDetailView,
    ToolCallsView,
    ToolSyncView,
    ToolSectionsView,
)
from zango.ai.api.confirmation_views import (
    ConfirmationListView,
    ConfirmationDetailView,
    ConfirmationDecideView,
    PendingConfirmationsCountView,
)

urlpatterns = [
    # ... existing provider/agent/prompt URLs ...
    
    # Tools
    path('v1/ai/tools/', ToolListView.as_view(), name='ai-tool-list'),
    path('v1/ai/tools/sync/', ToolSyncView.as_view(), name='ai-tool-sync'),
    path('v1/ai/tools/sections/', ToolSectionsView.as_view(), name='ai-tool-sections'),
    path('v1/ai/tools/<int:tool_id>/', ToolDetailView.as_view(), name='ai-tool-detail'),
    path('v1/ai/tools/<int:tool_id>/calls/', ToolCallsView.as_view(), name='ai-tool-calls'),
    
    # Confirmations
    path('v1/ai/confirmations/', ConfirmationListView.as_view(), name='ai-confirmation-list'),
    path('v1/ai/confirmations/pending-count/', PendingConfirmationsCountView.as_view(), name='ai-confirmation-pending-count'),
    path('v1/ai/confirmations/<int:confirmation_id>/', ConfirmationDetailView.as_view(), name='ai-confirmation-detail'),
    path('v1/ai/confirmations/<int:confirmation_id>/decide/', ConfirmationDecideView.as_view(), name='ai-confirmation-decide'),
]
```

---

### 12. Celery Tasks (tool-related)

```python
"""
Add these to zango/ai/tasks.py
"""

from celery import shared_task


@shared_task
def expire_pending_confirmations():
    """
    Periodic task — run every 60 seconds via Celery Beat.
    
    Finds confirmations where:
    - status == 'pending'
    - expires_at < now
    
    For each:
    1. Set status = 'expired', decided_at = now
    2. Resume the agent pipeline with a 'denied' tool result
       (message: "Tool call expired — no decision was made in time")
    
    This ensures paused pipelines don't hang forever.
    """
    from django.utils import timezone
    from zango.ai.models.confirmation import AppLLMToolConfirmation
    
    expired = AppLLMToolConfirmation.objects.filter(
        status='pending',
        expires_at__lt=timezone.now(),
    )
    
    count = 0
    for confirmation in expired:
        confirmation.status = 'expired'
        confirmation.decided_at = timezone.now()
        confirmation.save(update_fields=['status', 'decided_at'])
        
        # Resume pipeline with expiry
        try:
            from zango.ai.tools.confirmation import resume_after_confirmation
            resume_after_confirmation(
                confirmation_id=confirmation.id,
                decision='denied',
                denial_reason='Confirmation expired',
            )
        except Exception:
            pass  # Log but don't crash the periodic task
        
        count += 1
    
    return f"Expired {count} confirmations"


@shared_task
def update_tool_usage_stats():
    """
    Periodic task — run every 5 minutes via Celery Beat.
    
    Aggregates AppLLMToolCall records to update usage stats on AppLLMTool:
    - total_calls, total_errors, total_timeouts
    - avg_execution_ms (rolling average)
    - last_called_at
    
    Uses a 24-hour window for avg_execution_ms to keep it responsive.
    """
    from django.utils import timezone
    from django.db.models import Count, Avg, Q, Max
    from zango.ai.models.tool import AppLLMTool, AppLLMToolCall
    
    cutoff_24h = timezone.now() - timezone.timedelta(hours=24)
    
    for tool in AppLLMTool.objects.filter(is_active=True):
        calls = AppLLMToolCall.objects.filter(tool=tool)
        
        stats = calls.aggregate(
            total=Count('id'),
            errors=Count('id', filter=Q(status='error')),
            timeouts=Count('id', filter=Q(status='timeout')),
            last_called=Max('created_at'),
        )
        
        avg_ms = calls.filter(
            status='success',
            created_at__gte=cutoff_24h,
        ).aggregate(avg=Avg('execution_time_ms'))['avg']
        
        tool.total_calls = stats['total'] or 0
        tool.total_errors = stats['errors'] or 0
        tool.total_timeouts = stats['timeouts'] or 0
        tool.avg_execution_ms = int(avg_ms) if avg_ms else 0
        tool.last_called_at = stats['last_called']
        tool.save(update_fields=[
            'total_calls', 'total_errors', 'total_timeouts',
            'avg_execution_ms', 'last_called_at',
        ])
```

---

## FRONTEND (App Panel UI)

The tools UI lives within the AI Framework section of the App Panel, 
accessible via the "Tools" tab (add after Agents tab in the tab bar).

### Design Reference
Follow the EXACT same design patterns established in the existing AI framework 
design files at:
`/Users/kc-zelthy/Documents/bms-temp/deploy/zango_project/ai_framework_designs/`

Specifically:
- `shared-styles.css` — all shared styles (sidebar, header, tabs, cards)
- `03-ai-agents.html` — agent config page (similar config panel pattern)
- `06-ai-invocation-logs.html` — invocation logs (table pattern, expand detail pattern)

### File to Create
`/Users/kc-zelthy/Documents/bms-temp/deploy/zango_project/ai_framework_designs/07-ai-tools.html`

### Page Structure

#### Tab Bar
Add a "Tools" tab to the existing tab bar (between "Prompts" and "Guardrails"):
```
Dashboard | Providers | Agents | Prompts | [Tools] | Guardrails | Invocation Logs
```
The Tools tab shows a badge with the count of active tools.

#### Section Header Card
```
Tools
Code-defined functions that agents can call during LLM interactions.
Tools are registered via @tool decorator in code and synced to the panel automatically.

Active Tools: 12  |  Sections: 4  |  Confirmable: 3  |  Pending Confirmations: 2
```
The "Pending Confirmations" stat should be highlighted in orange if > 0.

#### Filter Row
```
[Search by name or description...]  [Section: All ▼]  [Safety: All ▼]  [Status: Active ▼]  [Sync Tools ↻]
```
"Sync Tools" button triggers POST /api/v1/ai/tools/sync/

#### Tools Table (Main View)

Columns:
| Tool Name | Section | Description | Safety | Confirm? | Params | Agents | Calls | Avg Time | Status |
|-----------|---------|-------------|--------|----------|--------|--------|-------|----------|--------|

Where:
- **Tool Name**: Monospace font, links to detail. Shows python_path underneath in small gray text.
- **Section**: Badge/chip style (assessments=purple, notifications=blue, analytics=green)
- **Description**: First ~80 chars, truncated with ellipsis
- **Safety**: Color-coded badge:
  - read_only → green badge "READ"
  - write → orange badge "WRITE" 
  - external → red badge "EXTERNAL"
- **Confirm?**: "Yes ⚠️" (orange) or "No" (gray)
- **Params**: Count of parameters from schema (e.g., "3 params")
- **Agents**: Number of agents using this tool (e.g., "2 agents", links to agent list)
- **Calls**: Total call count (abbreviated: "1.2k")
- **Avg Time**: Average execution time (e.g., "45ms", "1.2s"). Color: green < 100ms, yellow 100-500ms, red > 500ms
- **Status**: Green dot "Active" or gray dot "Inactive"

Show 8 example rows covering:
1. get_employee_score_history — read_only, assessments, no confirmation, 45ms
2. get_recent_topics — read_only, assessments, no confirmation, 12ms  
3. flag_weak_area — write, assessments, requires confirmation, 31ms
4. send_slack_notification — external, notifications, requires confirmation, 280ms
5. get_department_benchmarks — read_only, analytics, no confirmation, 95ms
6. search_knowledge_base — read_only, rag, no confirmation, 340ms
7. update_difficulty_band — write, analytics, no confirmation, 22ms
8. generate_report_pdf — external, reports, requires confirmation, 2.1s (inactive)

#### Expanded Tool Detail (Click on a row)

When clicking on row 3 (flag_weak_area), show an expanded detail panel with:

**Left Column:**
- Tool metadata card:
  - Name: flag_weak_area
  - Section: assessments
  - Safety: WRITE
  - Python Path: assessments.tools.flag_weak_area
  - Return Type: dict
  - Timeout: 30s
  - Rate Limit: —
  - Requires Confirmation: Yes
  - Display Function: Yes ✓
  - Schema Hash: a1b2c3d4
  - Last Synced: 27 Mar 2026, 09:00:15

- Parameters panel (rendered from JSON Schema):
  ```
  ┌─────────────┬─────────┬──────────┬────────────────────────────────────┐
  │ Parameter   │ Type    │ Required │ Description                        │
  ├─────────────┼─────────┼──────────┼────────────────────────────────────┤
  │ employee_id │ integer │ ✓        │ The employee's database ID         │
  │ topic       │ string  │ ✓        │ The specific topic to flag         │
  │ section     │ string  │ ✓        │ Which section this topic belongs to│
  │ severity    │ string  │          │ How weak: mild, moderate, severe   │
  │             │         │          │ Default: "moderate"                │
  │             │         │          │ Enum: mild, moderate, severe       │
  └─────────────┴─────────┴──────────┴────────────────────────────────────┘
  ```

**Right Column:**
- Agents using this tool:
  ```
  ┌──────────────────────────────┬───────────────┬─────────────────────────┐
  │ Agent                        │ Background    │ Conditions              │
  ├──────────────────────────────┼───────────────┼─────────────────────────┤
  │ assessment-question-generator│ Auto-approve  │ severity ≤ moderate     │
  │ weak-area-analyzer           │ Deny          │ —                       │
  └──────────────────────────────┴───────────────┴─────────────────────────┘
  ```

- Recent calls (last 5):
  ```
  ┌────────────┬────────┬───────────────────────────┬────────┬────────┬─────────────┐
  │ Time       │ Round  │ Input (truncated)         │ Status │ Time   │ Confirmation│
  ├────────────┼────────┼───────────────────────────┼────────┼────────┼─────────────┤
  │ 10:42:18   │ R2     │ {employee_id:42, topic... │ ✓ OK   │ 31ms   │ auto-approved│
  │ 10:38:05   │ R1     │ {employee_id:15, topic... │ ✓ OK   │ 28ms   │ approved    │
  │ 10:35:11   │ R2     │ {employee_id:8, topic:... │ ✗ deny │ 0ms    │ denied      │
  │ 09:15:42   │ R1     │ {employee_id:42, topic... │ ✓ OK   │ 35ms   │ auto-approved│
  │ 09:12:30   │ R1     │ {employee_id:22, topic... │ ✓ OK   │ 29ms   │ auto-approved│
  └────────────┴────────┴───────────────────────────┴────────┴────────┴─────────────┘
  ```

- Raw JSON Schema (collapsible, dark code block):
  ```json
  {
    "type": "object",
    "properties": {
      "employee_id": {"type": "integer", "description": "The employee's database ID"},
      "topic": {"type": "string", "description": "The specific topic to flag"},
      "section": {"type": "string", "description": "Which section this topic belongs to"},
      "severity": {"type": "string", "description": "How weak", "enum": ["mild","moderate","severe"]}
    },
    "required": ["employee_id", "topic", "section"]
  }
  ```

#### Pending Confirmations Banner

If there are pending confirmations (count > 0), show a banner at the top of the 
tools page (below section header, above filter row):

```
⚠️ 2 Pending Tool Confirmations                                    [View All →]
┌──────────────────────────────┬───────────────────────────────┬──────────┬──────────────────┐
│ send_slack_notification      │ "Send Slack notification to   │ 4m 12s   │ [Approve] [Deny] │
│ EXTERNAL · manager-digest    │  #engineering-managers..."    │ remaining │                  │
├──────────────────────────────┼───────────────────────────────┼──────────┼──────────────────┤
│ update_employee_record       │ "Update John Smith's weak     │ 1m 45s   │ [Approve] [Deny] │
│ WRITE · weak-area-analyzer   │  area record for ICH E6..."  │ remaining │                  │
└──────────────────────────────┴───────────────────────────────┴──────────┴──────────────────┘
```

Each confirmation shows:
- Tool name + safety badge
- Agent name that triggered it
- Display text (from @tool.display function)
- Time remaining before expiry
- Approve / Deny buttons

---

## TESTING REQUIREMENTS

### Backend Unit Tests
- `test_decorator.py`:
  - Schema generation from various type hints (str, int, list[str], Optional, etc.)
  - ToolParam description, default, enum extraction
  - Display function registration via @tool_name.display
  - Python path extraction
  - Schema hash computation

- `test_registry.py`:
  - Tool registration via @tool decorator
  - autodiscover_tools with mock workspace
  - sync_tools_to_db: create, update (schema change), deactivate (code removed)
  - get_tool_function: found, not found

- `test_executor.py`:
  - Successful execution with return value
  - Timeout enforcement
  - Exception handling (sanitized error message)
  - Input validation against schema (valid, invalid)
  - Return value serialization (datetime, Decimal, QuerySet, etc.)
  - Large output truncation

- `test_confirmation.py`:
  - resolve_tool_call: all 5 execution contexts × all policy combinations
  - Condition checking: max_severity, only_for_sections, equals
  - _create_confirmation: display function called, fallback to JSON
  - resume_after_confirmation: approved path, denied path, expired path

### Backend Integration Tests
- Create tool in code → sync → verify DB record matches
- Agent with tools → invoke → LLM returns tool_use → tool executes → verify AppLLMToolCall logged
- Confirmation flow: interactive context → confirm → API approve → pipeline resumes → complete
- Confirmation expiry: create → wait → periodic task expires → pipeline resumes with denial
- Update tool code (change schema) → resync → verify DB updated, agents still work

### Frontend Tests
- Open tools page → verify all tools listed with correct data
- Click tool row → verify expanded detail shows parameters, agents, recent calls
- Click Approve on pending confirmation → verify tool executes
- Click Deny → verify denial logged
- Sync button → verify toast notification on success
- Filter by section, safety, active status → verify table filters correctly

## DEPENDENCIES

No new dependencies beyond what Phase 1 and Phase 2 already require.
- `jsonschema>=4.20.0` — already added in Phase 2 for output schema validation
```

---

That's the complete tools implementation prompt covering both backend (decorator → registry → executor → confirmation → models → API) and frontend (panel UI design spec for the tools page with all component details).