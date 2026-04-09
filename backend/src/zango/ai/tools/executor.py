"""
Executes tool functions with safety wrapping: validation, timeout, serialization.
Never raises — all outcomes captured in ToolResult.

Tools are dynamically imported from the tenant's workspace via plugin_source,
following the same pattern as zango_task_executor for Celery tasks.
"""

import datetime
import json
import logging
import signal
import time
import traceback
import threading
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


class _ToolTimeoutError(Exception):
    pass


class ToolExecutor:
    """
    Executes tool functions by dynamically importing them from the tenant's
    workspace, following the same pattern as zango_task_executor.

    Usage:
        executor = ToolExecutor()
        result = executor.execute("get_recent_topics", {"employee_id": 42, "hours": 48})
    """

    def execute(self, tool_name: str, tool_input: dict) -> ToolResult:
        """Execute a tool function by name. Never raises."""
        start_time = time.monotonic()

        # Step 1: Look up tool record from DB (tenant-scoped via connection.tenant)
        try:
            from zango.apps.ai.models.tool import AppLLMTool

            tool_record = AppLLMTool.objects.get(name=tool_name, is_active=True)
        except Exception:
            return ToolResult(
                output=None,
                status="error",
                execution_time_ms=0,
                error_message=f"Tool '{tool_name}' not found in database",
            )

        # Step 2: Dynamic import from tenant workspace (same as zango_task_executor)
        try:
            from django.db import connection

            from zango.apps.dynamic_models.workspace.base import Workspace

            ws = Workspace(connection.tenant, request=None, as_systemuser=True)

            module_path, func_name = tool_record.python_path.rsplit(".", 1)
            module = ws.plugin_source.load_plugin(module_path)
            func = getattr(module, func_name)
        except Exception as e:
            elapsed = int((time.monotonic() - start_time) * 1000)
            logger.error(
                f"Tool '{tool_name}' import failed: {e}", exc_info=True
            )
            return ToolResult(
                output=None,
                status="error",
                execution_time_ms=elapsed,
                error_message=f"Tool import failed: {type(e).__name__}: {str(e)[:500]}",
            )

        # Step 3: Validate input against schema from DB
        validation_error = self._validate_input(
            tool_input, tool_record.parameters_schema
        )
        if validation_error:
            elapsed = int((time.monotonic() - start_time) * 1000)
            return ToolResult(
                output=None,
                status="validation_error",
                execution_time_ms=elapsed,
                error_message=f"Invalid input: {validation_error}",
            )

        # Step 4: Execute synchronously with timeout
        timeout_seconds = tool_record.timeout_seconds
        try:
            raw_result = self._execute_with_timeout(
                func, tool_input, timeout_seconds
            )
        except _ToolTimeoutError:
            elapsed = int((time.monotonic() - start_time) * 1000)
            logger.warning(
                f"Tool '{tool_name}' timed out after {timeout_seconds}s"
            )
            return ToolResult(
                output=None,
                status="timeout",
                execution_time_ms=elapsed,
                error_message=f"Tool execution timed out after {timeout_seconds}s",
            )
        except Exception as e:
            elapsed = int((time.monotonic() - start_time) * 1000)
            tb = traceback.format_exc()
            logger.error(
                f"Tool '{tool_name}' raised {type(e).__name__}: {e}",
                exc_info=True,
            )
            return ToolResult(
                output=None,
                status="error",
                execution_time_ms=elapsed,
                error_message=f"Tool execution failed: {type(e).__name__}: {str(e)[:500]}",
                error_traceback=tb,
            )

        # Step 5: Serialize return value
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

    def _execute_with_timeout(self, func, tool_input, timeout_seconds):
        """
        Execute func synchronously with timeout enforcement.

        Uses signal.SIGALRM when running in the main thread (gunicorn sync
        workers, celery workers). Falls back to no timeout enforcement in
        non-main threads, relying on the outer framework's timeout instead.
        """
        if threading.current_thread() is threading.main_thread():
            def _timeout_handler(signum, frame):
                raise _ToolTimeoutError()

            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_seconds)
            try:
                return func(**tool_input)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        else:
            logger.debug(
                "Tool executing in non-main thread — timeout not enforced"
            )
            return func(**tool_input)

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
