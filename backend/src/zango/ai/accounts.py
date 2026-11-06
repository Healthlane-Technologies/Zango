"""
Connecting an app's AI account (``AppLLMProvider``) to working credentials.

Two ways, both ending with an account that can call the AI:

- ``link_platform(provider, account)``: use a ``PlatformAIAccount`` that the platform
  admin set up once (Platform → Settings → AI accounts). No key is copied; the app
  reads the platform account's credentials at call time, so a key rotation there
  reaches every linked app.
- ``connect_own(provider, slug, config, ...)``: the app's own key, checked live first.

Either way the account stops being a placeholder, its model list is replaced, and the
agents on it whose model the new service doesn't offer move to the new default model.
Must be called inside the app's tenant context.
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from zango.ai.encryption import encrypt_config


def check_credentials(
    slug: str, config: dict, model: str | None = None
) -> tuple[bool, str, list[dict]]:
    """Check a config against the live service. Returns (ok, error, models).

    Lists the models (which proves the key for services with a models API), then
    makes the service's own minimal check call, with ``model`` when given.
    """
    from zango.ai.providers.registry import get_provider_class

    cls = get_provider_class(slug)
    try:
        models = cls.fetch_models(config) or []
    except ValueError as exc:
        return False, str(exc), []
    except Exception:  # noqa: BLE001 — some services can't list models; fall back
        models = []
    try:
        ok, err = cls(
            {**config, **({"default_model": model} if model else {})}
        ).validate_config()
    except Exception as exc:  # noqa: BLE001
        return False, str(exc), []
    if not ok:
        return False, err or "The service refused these credentials.", []
    return True, "", models or list(getattr(cls, "supported_models", []) or [])


def _replace_models(provider, models: list[dict]) -> None:
    from zango.apps.ai.models.provider import AppLLMProviderModel

    provider.enabled_models.all().delete()
    seen = set()
    for m in models:
        mid = m.get("id")
        if not mid or mid in seen:
            continue
        seen.add(mid)
        AppLLMProviderModel.objects.create(
            provider=provider,
            model_id=mid,
            display_name=m.get("name") or mid,
            is_enabled=True,
        )


def _move_agents(provider, model_ids: list[str], default_model: str) -> int:
    """Agents on this account whose model is no longer offered get the new default."""
    from zango.apps.ai.models import AppLLMAgent

    if not model_ids or not default_model:
        return 0
    stale = AppLLMAgent.objects.filter(provider=provider).exclude(model__in=model_ids)
    return stale.update(model=default_model)


def _pick(model: str | None, ids: list[str], fallback: str) -> str:
    if model and (not ids or model in ids):
        return model
    return fallback or (ids[0] if ids else (model or ""))


@transaction.atomic
def link_platform(provider, account, model: str | None = None) -> dict:
    """Point ``provider`` at a platform AI account. Returns {default_model, moved}."""
    models = list(account.model_list or [])
    if not models:
        cls = account.provider_class()
        models = list(getattr(cls, "supported_models", []) or [])
    ids = [m["id"] for m in models if m.get("id")]
    default_model = _pick(model or provider.default_model, ids, account.default_model)

    provider.source = provider.SOURCE_PLATFORM
    provider.platform_account_uuid = account.uuid
    provider.provider_slug = account.provider_slug
    provider.config_encrypted = encrypt_config({})
    provider.default_model = default_model
    provider.is_placeholder = False
    provider.is_enabled = True
    provider.is_validated = True
    provider.last_validated_at = timezone.now()
    provider.validation_error = None
    cap = account.app_monthly_budget_usd  # a ceiling for every app on this account
    if cap is not None and (
        provider.monthly_budget_usd is None or provider.monthly_budget_usd > cap
    ):
        provider.monthly_budget_usd = cap
    provider.save()
    _replace_models(provider, models)
    return {
        "default_model": default_model,
        "moved": _move_agents(provider, ids, default_model),
    }


@transaction.atomic
def connect_own(
    provider, slug: str, config: dict, default_model: str, models: list[dict]
) -> dict:
    """Give ``provider`` its own (already checked) credentials."""
    ids = [m["id"] for m in models if m.get("id")]
    default_model = _pick(default_model, ids, "")

    provider.source = provider.SOURCE_OWN
    provider.platform_account_uuid = None
    provider.provider_slug = slug
    provider.config_encrypted = encrypt_config(config)
    provider.default_model = default_model
    provider.is_placeholder = False
    provider.is_enabled = True
    provider.is_validated = True
    provider.last_validated_at = timezone.now()
    provider.validation_error = None
    provider.save()
    _replace_models(provider, models)
    return {
        "default_model": default_model,
        "moved": _move_agents(provider, ids, default_model),
    }


def apps_linked_to(account_uuid) -> list[dict]:
    """Apps whose AI accounts use this platform account: [{uuid, name, providers}]."""
    from django_tenants.utils import schema_context

    from zango.apps.ai.models import AppLLMProvider
    from zango.apps.shared.tenancy.models import TenantModel

    out = []
    for t in TenantModel.objects.exclude(schema_name="public"):
        try:
            with schema_context(t.schema_name):
                names = list(
                    AppLLMProvider.objects.filter(
                        source=AppLLMProvider.SOURCE_PLATFORM,
                        platform_account_uuid=account_uuid,
                    ).values_list("name", flat=True)
                )
        except Exception:  # noqa: BLE001 — an app mid-migration has no table yet
            continue
        if names:
            out.append({"uuid": str(t.uuid), "name": t.name, "providers": names})
    return out
