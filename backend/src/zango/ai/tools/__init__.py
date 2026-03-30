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
"""

from zango.ai.tools.decorator import ToolParam, ToolSafety, tool
from zango.ai.tools.registry import (
    TOOL_REGISTRY,
    autodiscover_tools,
    get_all_tool_metas,
    get_tool_function,
    sync_tools_to_db,
)
