"""
Executes tool functions with safety wrapping: validation, timeout, serialization.
Never raises — all outcomes captured in ToolResult.
"""

import datetime
import json
import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import jsonschema

logger = logging.getLogger("zango.ai.tools")


@dataclass
class ToolResult:
    """Outcome of a tool execution attempt."""

    output: Any  # The function's return value (JSON-serializable)
    status: str  # "success", "error", "timeout", "validation_error", "denied"
    execution_time_ms: int  # Wall time in milliseconds
    error_message: str | None = None
    error_traceback: str | None = None  # For internal logging only


_executor_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="tool-exec")


class ToolExecutor:
    """
    Executes registered tool functions with safety wrapping.

    Usage:
        executor = ToolExecutor()
        result = executor.execute("get_recent_topics", {"employee_id": 42, "hours": 48})
    """

    def _ensure_tools_discovered(self):
        """Trigger autodiscovery if the TOOL_REGISTRY is empty."""
        from zango.ai.tools.registry import TOOL_REGISTRY, autodiscover_tools

        if TOOL_REGISTRY:
            return

        try:
            import os

            from django.apps import apps as django_apps
            from django.conf import settings
            from django.db import connection

            # Resolve tenant name from the current schema
            # set_app_schema_path sets connection.schema_name via schema_context
            schema_name = connection.schema_name
            tenant_model = django_apps.get_model("tenancy", "TenantModel")
            tenant = tenant_model.objects.using("default").get(schema_name=schema_name)
            workspace_path = os.path.join(
                settings.BASE_DIR, "workspaces", tenant.name
            )
            autodiscover_tools(workspace_path)
            logger.info(
                f"Lazy tool autodiscovery for '{tenant.name}': "
                f"{len(TOOL_REGISTRY)} tools loaded"
            )
        except Exception as e:
            logger.error(f"Lazy tool autodiscovery failed: {e}", exc_info=True)

    def execute(self, tool_name: str, tool_input: dict) -> ToolResult:
        """Execute a tool function by name. Never raises."""
        start_time = time.monotonic()

        # Step 1: Look up function (with lazy autodiscovery fallback)
        from zango.ai.tools.registry import get_tool_function

        try:
            func = get_tool_function(tool_name)
        except Exception:
            # Registry might be empty — try autodiscovery and retry
            self._ensure_tools_discovered()
            try:
                func = get_tool_function(tool_name)
            except Exception:
                return ToolResult(
                    output=None,
                    status="error",
                    execution_time_ms=0,
                    error_message=f"Tool '{tool_name}' not found in registry",
                )

        meta = func._tool_meta

        # Step 2: Validate input
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
        # Wrap the function to ensure Django DB connections are usable in the thread pool.
        # Pooled threads can hold stale/closed connections from previous executions.
        def _run_in_thread(**kwargs):
            from django.db import close_old_connections
            close_old_connections()
            try:
                return func(**kwargs)
            finally:
                close_old_connections()

        try:
            future = _executor_pool.submit(_run_in_thread, **tool_input)
            raw_result = future.result(timeout=meta.timeout_seconds)
        except FuturesTimeoutError:
            elapsed = int((time.monotonic() - start_time) * 1000)
            logger.warning(f"Tool '{tool_name}' timed out after {meta.timeout_seconds}s")
            return ToolResult(
                output=None,
                status="timeout",
                execution_time_ms=elapsed,
                error_message=f"Tool execution timed out after {meta.timeout_seconds}s",
            )
        except Exception as e:
            elapsed = int((time.monotonic() - start_time) * 1000)
            tb = traceback.format_exc()
            logger.error(f"Tool '{tool_name}' raised {type(e).__name__}: {e}", exc_info=True)
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
        """Validate tool_input against JSON Schema. Returns None on success."""
        try:
            jsonschema.validate(instance=tool_input, schema=schema)
            return None
        except jsonschema.ValidationError as e:
            return e.message
        except Exception as e:
            return f"Schema validation error: {str(e)}"

    def _serialize_output(self, value: Any) -> Any:
        """Ensure return value is JSON-serializable. Truncates large outputs."""
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

            return base64.b64encode(value).decode("ascii")

        # Try JSON round-trip
        try:
            json_str = json.dumps(value, default=str)
            if len(json_str) > 50000:
                return json.loads(json_str[:50000])
            return json.loads(json_str)
        except (TypeError, ValueError):
            return str(value)[:2000]
