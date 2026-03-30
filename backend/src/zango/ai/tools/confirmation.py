"""
Confirmation resolution pipeline for tool calls with side effects.

Three execution contexts:
- interactive: User present → confirmable tools pause for human approval
- background: No user → policy-driven (auto_approve, deny_all, queue)
- system: Internal calls → always auto-approve
"""

import json
import logging
from datetime import timedelta
from typing import Optional, Tuple

from django.utils import timezone

logger = logging.getLogger("zango.ai.tools")


def resolve_tool_call(
    agent,
    tool_meta,
    tool_input: dict,
    execution_context: str,
    invocation=None,
    round_number: int = 1,
    pipeline_state: dict = None,
) -> Tuple[str, Optional[object], Optional[str]]:
    """
    Decide whether to execute, confirm, or deny a tool call.

    Returns:
        ('execute', None, None)                    → proceed immediately
        ('confirm', AppLLMToolConfirmation, None)   → pause and wait
        ('deny', None, "reason string")             → skip
    """
    from zango.ai.tools.decorator import ToolSafety

    # Read-only tools never need confirmation
    if tool_meta.safety == ToolSafety.READ_ONLY:
        return ("execute", None, None)

    # Tool doesn't require confirmation
    if not tool_meta.requires_confirmation:
        return ("execute", None, None)

    # System context always auto-approves
    if execution_context == "system":
        return ("execute", None, None)

    # Interactive context — pause for human
    if execution_context == "interactive":
        confirmation = _create_confirmation(
            agent, tool_meta, tool_input, invocation, round_number, pipeline_state
        )
        return ("confirm", confirmation, None)

    # Background context — policy-driven
    if execution_context == "background":
        policy = getattr(agent, "background_confirmation_policy", "deny_all")

        if policy == "auto_approve":
            return ("execute", None, None)

        if policy == "deny_all":
            return ("deny", None, "background_policy_deny_all")

        if policy == "queue":
            confirmation = _create_confirmation(
                agent, tool_meta, tool_input, invocation, round_number, pipeline_state
            )
            return ("confirm", confirmation, None)

    # Fallback: deny unknown contexts
    return ("deny", None, f"unknown_execution_context:{execution_context}")


def _create_confirmation(
    agent, tool_meta, tool_input, invocation, round_number, pipeline_state
):
    """Create a pending confirmation record."""
    from zango.apps.ai.models.confirmation import AppLLMToolConfirmation
    from zango.apps.ai.models.tool import AppLLMTool

    # Generate display text
    display_text = ""
    if tool_meta.display_func:
        try:
            display_text = tool_meta.display_func(**tool_input)
        except Exception as e:
            display_text = f"(Display function error: {e})"

    if not display_text:
        display_text = (
            f"Execute {tool_meta.name} with: {json.dumps(tool_input, indent=2)[:500]}"
        )

    # Get tool DB record
    tool_record = None
    try:
        tool_record = AppLLMTool.objects.get(name=tool_meta.name)
    except AppLLMTool.DoesNotExist:
        pass

    expiry_seconds = getattr(agent, "confirmation_expiry_seconds", 300)

    confirmation = AppLLMToolConfirmation.objects.create(
        invocation=invocation,
        tool=tool_record,
        tool_name=tool_meta.name,
        tool_input=tool_input,
        tool_input_display=display_text,
        pipeline_state=pipeline_state or {},
        round_number=round_number,
        status="pending",
        expires_at=timezone.now() + timedelta(seconds=expiry_seconds),
    )

    logger.info(
        f"Pending tool confirmation: {tool_meta.name} "
        f"(invocation={getattr(invocation, 'id', None)}, expires={confirmation.expires_at})"
    )

    return confirmation


def resume_after_confirmation(
    confirmation_id: int,
    decision: str,
    decided_by_user=None,
    denial_reason: str = "",
):
    """
    Resume a paused pipeline after confirmation decision.

    For now, executes/skips the tool and returns the ToolResult.
    Full pipeline resume (multi-round) is a future enhancement.
    """
    from zango.apps.ai.models.confirmation import AppLLMToolConfirmation
    from zango.ai.tools.executor import ToolExecutor, ToolResult

    confirmation = AppLLMToolConfirmation.objects.select_related(
        "invocation", "tool"
    ).get(id=confirmation_id)

    # Validate state
    if confirmation.status != "pending":
        from zango.ai.exceptions import ZangoAIError

        raise ZangoAIError(
            f"Confirmation {confirmation_id} is already {confirmation.status}"
        )

    if confirmation.expires_at < timezone.now():
        confirmation.status = "expired"
        confirmation.decided_at = timezone.now()
        confirmation.save(update_fields=["status", "decided_at"])
        from zango.ai.exceptions import ZangoAIError

        raise ZangoAIError(f"Confirmation {confirmation_id} has expired")

    # Record decision
    confirmation.status = decision
    confirmation.decided_by_user = str(decided_by_user) if decided_by_user else ""
    confirmation.decided_at = timezone.now()
    confirmation.denial_reason = denial_reason
    confirmation.save()

    if decision == "approved":
        executor = ToolExecutor()
        return executor.execute(confirmation.tool_name, confirmation.tool_input)
    else:
        return ToolResult(
            output={"error": f"Tool call denied: {denial_reason}"},
            status="denied",
            execution_time_ms=0,
            error_message=f"Denied: {denial_reason}",
        )
