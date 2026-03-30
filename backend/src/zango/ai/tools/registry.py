"""
In-memory registry of all discovered @tool functions.

Lifecycle:
1. App starts → autodiscover_tools() scans workspace tools.py files
2. Importing triggers @tool decorators → TOOL_REGISTRY populated
3. sync_tools_to_db() mirrors TOOL_REGISTRY → AppLLMTool table
"""

import glob
import importlib
import logging
import os
from typing import Callable

logger = logging.getLogger("zango.ai.tools")

TOOL_REGISTRY: dict[str, Callable] = {}


def autodiscover_tools(workspace_path: str) -> int:
    """
    Scan all tools.py files in the workspace and import them directly
    using importlib.util (file-based loading — doesn't depend on sys.path).
    Returns number of newly discovered tools.
    """
    import importlib.util
    import sys

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
        # Generate a unique module name from the file path
        rel_path = os.path.relpath(file_path, workspace_path)
        module_name = "zango_tools." + rel_path.replace(os.sep, ".").replace(".py", "")

        # Skip if already loaded
        if module_name in sys.modules:
            logger.debug(f"Already loaded: {module_name}")
            continue

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                logger.info(f"Discovered tools from: {file_path}")
        except Exception as e:
            logger.warning(
                f"Failed to import tools from {file_path}: {e}",
                exc_info=True,
            )

    new_count = len(TOOL_REGISTRY) - initial_count
    logger.info(
        f"Tool autodiscovery complete: {new_count} new tools, {len(TOOL_REGISTRY)} total"
    )
    return new_count


def sync_tools_to_db() -> dict:
    """
    Synchronize TOOL_REGISTRY with the AppLLMTool database table.
    Returns: {"created": int, "updated": int, "deactivated": int}
    """
    from zango.apps.ai.models.tool import AppLLMTool

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
    """Look up a tool function by name. Raises ToolNotFound if not found."""
    func = TOOL_REGISTRY.get(name)
    if func is None:
        from zango.ai.exceptions import ToolNotFound

        raise ToolNotFound(name)
    return func


def get_all_tool_metas() -> list:
    """Return ToolMeta for all registered tools."""
    return [func._tool_meta for func in TOOL_REGISTRY.values()]
