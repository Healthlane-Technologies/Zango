"""
Celery tasks for async LLM completions.
"""

from celery import shared_task
from loguru import logger


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

    from django_tenants.utils import schema_context

    from django.db.models import Avg, Count, Max, Q
    from django.utils import timezone

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
            logger.error(
                f"Error updating tool usage stats for tenant {tenant.schema_name}: {e}"
            )
            raise


@shared_task(name="zango.ai.refresh_bedrock_pricing")
def refresh_bedrock_pricing(provider_id=None):
    """Refresh AWS Bedrock cost rates from the live Price List API.

    Runs off the request path (daily beat + on provider create/validate). The
    public price list is fetched **once** using the platform-level
    ``settings.AWS_*`` credentials, then fanned out to every tenant's enabled
    Bedrock providers by writing ``AppLLMProviderModel`` override rows.

    Rows whose ``pricing_source`` is ``"manual"`` (an admin-set enterprise rate)
    are never overwritten. If the pricing API is unavailable or the credentials
    lack ``pricing:GetProducts``, ``fetch_bedrock_rates`` returns ``{}`` and this
    task exits without writing anything.

    Args:
        provider_id: When given, only that provider is refreshed (used by the
            create/validate trigger). The fetch itself is still global.
    """
    from django_tenants.utils import schema_context

    from django.utils import timezone

    from zango.ai.bedrock_pricing import fetch_bedrock_rates
    from zango.apps.shared.tenancy.models import TenantModel

    # 1. Fetch once — global, settings creds, tenant-independent.
    rates_by_region = fetch_bedrock_rates()
    if not rates_by_region:
        logger.info(
            "[refresh_bedrock_pricing] no live rates available "
            "(missing/unauthorised AWS credentials or empty price list) — nothing written."
        )
        return

    now = timezone.now()
    updated = 0

    # 2. Fan out across tenant schemas.
    for tenant in TenantModel.objects.exclude(schema_name="public"):
        try:
            with schema_context(tenant.schema_name):
                updated += _apply_rates_for_tenant(rates_by_region, now, provider_id)
        except Exception as e:
            logger.error(
                f"[refresh_bedrock_pricing] tenant {tenant.schema_name} failed: {e}"
            )
            # Keep going — one bad tenant should not abort the whole refresh.

    logger.info(f"[refresh_bedrock_pricing] updated {updated} model rate row(s).")


def _apply_rates_for_tenant(rates_by_region, now, provider_id=None):
    """Write fetched rates onto AppLLMProviderModel rows for one tenant schema.

    Returns the number of rows updated. Only touches Bedrock providers, only
    models we have a rate for, and never overwrites a ``manual`` override.
    """
    from zango.apps.ai.models.provider import AppLLMProvider, AppLLMProviderModel

    providers = AppLLMProvider.objects.filter(provider_slug="bedrock", is_enabled=True)
    if provider_id is not None:
        providers = providers.filter(id=provider_id)

    updated = 0
    for provider in providers:
        region = provider._decrypt_config().get("aws_region", "us-east-1")
        region_rates = rates_by_region.get(region)
        if not region_rates:
            continue

        for bare_id, rate in region_rates.items():
            input_rate = rate.get("input_per_mtok")
            output_rate = rate.get("output_per_mtok")
            if input_rate is None and output_rate is None:
                continue

            row, _ = AppLLMProviderModel.objects.get_or_create(
                provider=provider,
                model_id=bare_id,
                defaults={"display_name": bare_id},
            )
            # Never clobber an admin-set enterprise rate.
            if row.pricing_source == AppLLMProviderModel.PRICING_SOURCE_MANUAL:
                continue

            if input_rate is not None:
                row.input_cost_per_mtok_override = input_rate
            if output_rate is not None:
                row.output_cost_per_mtok_override = output_rate
            row.pricing_source = AppLLMProviderModel.PRICING_SOURCE_AWS_LIVE
            row.rates_updated_at = now
            row.save(
                update_fields=[
                    "input_cost_per_mtok_override",
                    "output_cost_per_mtok_override",
                    "pricing_source",
                    "rates_updated_at",
                ]
            )
            updated += 1

    return updated
