"""
Public API for the tools subsystem.

Usage:
    from zango.ai.tools import tool, ToolParam, ToolSafety

    @tool(name="get_scores", description="Get employee assessment scores")
    def get_scores(
        employee_id: int = ToolParam(description="The employee's database ID"),
        days: int = ToolParam(description="Days to look back", default=7),
    ) -> dict:
        ...

Tool discovery and sync are handled by Workspace.sync_tools().
Tool execution uses dynamic import via Workspace.plugin_source.
"""

from zango.ai.tools.decorator import ToolParam, ToolSafety, tool  # noqa: F401


__all__ = ["tool", "ToolParam", "ToolSafety"]
