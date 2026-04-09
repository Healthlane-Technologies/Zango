"""
Tool discovery and sync are now handled by Workspace.get_tools() and
Workspace.sync_tools() in zango.apps.dynamic_models.workspace.base,
following the same pattern as Workspace.get_tasks() and Workspace.sync_tasks().

Tool execution uses dynamic import via Workspace.plugin_source,
matching the zango_task_executor pattern.

This module is kept for backwards compatibility of imports only.
"""
