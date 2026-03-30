"""
Celery tasks for async LLM completions.
"""

import logging

from celery import shared_task

logger = logging.getLogger("zango.ai")


@shared_task(bind=True, name="zango.ai.async_llm_complete")
def async_llm_complete(
    self,
    provider_name,
    messages,
    model,
    tools=None,
    temperature=1.0,
    max_tokens=4096,
    system=None,
    triggered_by="celery",
    **kwargs,
):
    """
    Execute an LLM completion asynchronously via Celery.
    Messages and tools should already be serialized as dicts.
    """
    from zango.ai import get_provider
    from zango.ai.providers.base import LLMMessage, LLMToolDef

    try:
        client = get_provider(provider_name)

        # Reconstruct LLMMessage objects from serialized dicts
        llm_messages = [
            LLMMessage(role=m["role"], content=m["content"]) for m in messages
        ]

        llm_tools = None
        if tools:
            llm_tools = [
                LLMToolDef(
                    name=t["name"],
                    description=t["description"],
                    input_schema=t["input_schema"],
                )
                for t in tools
            ]

        response = client.complete(
            messages=llm_messages,
            model=model,
            tools=llm_tools,
            temperature=temperature,
            max_tokens=max_tokens,
            system=system,
            triggered_by=triggered_by,
            **kwargs,
        )

        return {
            "content": response.content,
            "stop_reason": response.stop_reason,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cost_usd": response.cost_usd,
            "model": response.model,
            "latency_ms": response.latency_ms,
        }

    except Exception as e:
        logger.error(f"Async LLM completion failed: {e}")
        raise


@shared_task(name="zango.ai.expire_pending_confirmations")
def expire_pending_confirmations():
    """
    Periodic task — run every 60 seconds.
    Expires pending confirmations past their expiry time.
    """
    from django.utils import timezone

    from zango.apps.ai.models.confirmation import AppLLMToolConfirmation

    expired = AppLLMToolConfirmation.objects.filter(
        status="pending", expires_at__lt=timezone.now()
    )

    count = 0
    for confirmation in expired:
        confirmation.status = "expired"
        confirmation.decided_at = timezone.now()
        confirmation.save(update_fields=["status", "decided_at"])
        count += 1

    if count:
        logger.info(f"Expired {count} pending tool confirmations")
    return f"Expired {count} confirmations"


@shared_task(name="zango.ai.update_tool_usage_stats")
def update_tool_usage_stats():
    """
    Periodic task — run every 5 minutes.
    Aggregates AppLLMToolCall records to update usage stats on AppLLMTool.
    """
    from datetime import timedelta

    from django.db.models import Avg, Count, Max, Q
    from django.utils import timezone

    from zango.apps.ai.models.tool import AppLLMTool, AppLLMToolCall

    cutoff_24h = timezone.now() - timedelta(hours=24)

    for tool_record in AppLLMTool.objects.filter(is_active=True):
        calls = AppLLMToolCall.objects.filter(tool=tool_record)

        stats = calls.aggregate(
            total=Count("id"),
            errors=Count("id", filter=Q(status="error")),
            timeouts=Count("id", filter=Q(status="timeout")),
            last_called=Max("created_at"),
        )

        avg_ms = calls.filter(
            status="success", created_at__gte=cutoff_24h
        ).aggregate(avg=Avg("execution_time_ms"))["avg"]

        tool_record.total_calls = stats["total"] or 0
        tool_record.total_errors = stats["errors"] or 0
        tool_record.total_timeouts = stats["timeouts"] or 0
        tool_record.avg_execution_ms = int(avg_ms) if avg_ms else 0
        tool_record.last_called_at = stats["last_called"]
        tool_record.save(
            update_fields=[
                "total_calls", "total_errors", "total_timeouts",
                "avg_execution_ms", "last_called_at",
            ]
        )
