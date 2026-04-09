"""
The @tool decorator and supporting classes.

Registers Python functions as LLM-callable tools with auto-generated JSON Schema.
"""

import hashlib
import inspect
import json
import typing
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, get_args, get_origin, get_type_hints

# Sentinel for "no default provided"
_MISSING = object()


class ToolSafety(Enum):
    READ_ONLY = "read_only"  # Only reads data, no side effects
    WRITE = "write"  # Modifies data in the database
    EXTERNAL = "external"  # Calls external services


class ToolParam:
    """
    Parameter descriptor providing metadata for LLM schema generation.

    Usage:
        @tool(name="get_scores", description="Get employee scores")
        def get_scores(
            employee_id: int = ToolParam(description="The employee's database ID"),
            days: int = ToolParam(description="Days to look back", default=7),
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
    rate_limit: int | None
    parameters_schema: dict
    python_path: str
    return_type: str | None
    display_func: Callable | None
    schema_hash: str


class _ToolDecorator:
    """
    Wrapper returned by @tool that supports the .display sub-decorator.
    """

    def __init__(self, func: Callable, meta: ToolMeta):
        self._func = func
        self._meta = meta
        self._tool_meta = meta
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def display(self, display_func: Callable) -> Callable:
        """Register a display function for confirmation UI."""
        self._meta.display_func = display_func
        self._func._tool_meta = self._meta
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
        name: Unique tool name (snake_case). What the LLM sees and calls.
        description: What this tool does. Written FOR the LLM.
        section: Grouping for panel UI (e.g., "assessments", "notifications").
        safety: READ_ONLY, WRITE, or EXTERNAL.
        requires_confirmation: If True, execution needs human approval.
        timeout_seconds: Max execution time before kill.
        rate_limit: Max calls per minute. None = unlimited.
    """

    def decorator(func: Callable) -> _ToolDecorator:
        hints = get_type_hints(func)
        sig = inspect.signature(func)

        schema = _build_parameters_schema(func, hints, sig)

        return_type = None
        if "return" in hints:
            return_type = _type_to_string(hints["return"])

        python_path = f"{func.__module__}.{func.__qualname__}"

        schema_hash = hashlib.sha256(
            json.dumps(schema, sort_keys=True).encode()
        ).hexdigest()[:16]

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
            display_func=None,
            schema_hash=schema_hash,
        )

        func._tool_meta = meta

        return _ToolDecorator(func, meta)

    return decorator


def _build_parameters_schema(func, hints, sig) -> dict:
    """Build a JSON Schema for the function's parameters."""
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        python_type = hints.get(param_name, str)

        tool_param = None
        if isinstance(param.default, ToolParam):
            tool_param = param.default

        prop = _python_type_to_json_schema(python_type)

        if tool_param:
            prop["description"] = tool_param.description
        else:
            prop["description"] = param_name.replace("_", " ")

        if tool_param and tool_param.enum:
            prop["enum"] = tool_param.enum

        properties[param_name] = prop

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
    """Convert a Python type annotation to a JSON Schema type definition."""
    origin = get_origin(python_type)
    args = get_args(python_type)

    # Handle X | None (UnionType in Python 3.10+)
    try:
        import types

        if isinstance(python_type, types.UnionType):
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                return _python_type_to_json_schema(non_none_args[0])
    except AttributeError:
        pass

    # typing.Optional / typing.Union
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

    # dict[K, V]
    if origin is dict:
        return {"type": "object"}

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
    """Convert a type annotation to a human-readable string."""
    origin = get_origin(python_type)
    args = get_args(python_type)

    if origin is list and args:
        return f"list[{_type_to_string(args[0])}]"
    if origin is dict and args:
        return f"dict[{_type_to_string(args[0])}, {_type_to_string(args[1])}]"

    if hasattr(python_type, "__name__"):
        return python_type.__name__

    return str(python_type)
