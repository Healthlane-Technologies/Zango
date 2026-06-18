"""
Celery tasks for async LLM completions.
"""

import logging

from celery import shared_task


logger = logging.getLogger("zango.ai")

_tool_stats_skip_tenants: set = set()



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


@shared_task(name="zango.ai.update_tool_usage_stats")
def update_tool_usage_stats():
    """
    Periodic task — run daily at 2 AM.
    Aggregates AppLLMToolCall records to update usage stats on AppLLMTool.
    avg_execution_ms is computed over the last 24 hours of successful calls.
    Runs across all active tenants.
    """
    from datetime import timedelta

    from django.db.models import Avg, Count, Max, Q
    from django.utils import timezone
    from django_tenants.utils import schema_context

    from zango.apps.shared.tenancy.models import TenantModel

    cutoff_24h = timezone.now() - timedelta(hours=24)

    for tenant in TenantModel.objects.exclude(schema_name="public"):
        try:
            with schema_context(tenant.schema_name):
                from zango.apps.ai.models.tool import AppLLMTool, AppLLMToolCall

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
                            "total_calls",
                            "total_errors",
                            "total_timeouts",
                            "avg_execution_ms",
                            "last_called_at",
                        ]
                    )
        except Exception as e:
            if tenant.schema_name not in _tool_stats_skip_tenants:
                logger.error(f"update_tool_usage_stats failed for tenant {tenant.schema_name}: {e}")
                _tool_stats_skip_tenants.add(tenant.schema_name)
