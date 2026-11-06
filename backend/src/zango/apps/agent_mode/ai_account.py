"""
The app's AI account for App Studio builds (AI agents plan, Step 4 and Step 5).

A spec with AI helpers needs one AI account (spec ``ai.provider``, Zango name
``app-llm`` by default) before the build's ``zango_platform.py ai`` step can create
agents on it. The build never has a key, and the provider API checks keys live, so
the account is created here through the ORM in the app's schema: the service and
model the spec names, an empty config, not validated. The creator adds the key later
in App → AI → Providers; every helper then works without a rebuild.

An account that already exists (a rebuild, or one the creator set up) is left alone.
"""

import logging


logger = logging.getLogger(__name__)

PLACEHOLDER_NOTE = (
    "Created by App Studio for this app's AI helpers. Add a key to switch them on."
)


def ensure_ai_account(app_name: str, ai: dict) -> dict:
    """Create the spec's AI account if the app has none by that name.

    Returns ``{"status": "created" | "exists" | "none", "name", "connected"}``;
    ``connected`` is False while the account has no checked key.
    """
    agents = (ai or {}).get("agents") or []
    prov = (ai or {}).get("provider") or {}
    name = prov.get("name") or "app-llm"
    if not agents:
        return {"status": "none", "name": name, "connected": False}

    from django_tenants.utils import tenant_context

    from zango.apps.shared.tenancy.models import TenantModel

    tenant = TenantModel.objects.get(name=app_name)
    with tenant_context(tenant):
        from zango.ai.encryption import encrypt_config
        from zango.ai.providers import registry
        from zango.apps.ai.models import AppLLMProvider
        from zango.apps.ai.models.provider import AppLLMProviderModel

        have = AppLLMProvider.objects.filter(name=name).first()
        if have is not None:
            return {
                "status": "exists",
                "name": name,
                "connected": bool(
                    have.is_validated and not getattr(have, "is_placeholder", False)
                ),
            }
        slug = prov.get("kind") or "anthropic"
        cls = registry.PROVIDER_REGISTRY.get(slug)
        if cls is None:
            raise ValueError(
                f"AI service {slug!r} is not available in this Zango (installed: "
                f"{', '.join(sorted(registry.PROVIDER_REGISTRY)) or 'none'})"
            )
        supported = list(getattr(cls, "supported_models", []) or [])
        model = prov.get("model") or (supported[0]["id"] if supported else "")
        fields = {
            "name": name,
            "description": PLACEHOLDER_NOTE,
            "provider_slug": slug,
            "config_encrypted": encrypt_config({}),
            "default_model": model,
            "monthly_budget_usd": prov.get("monthly_budget_usd"),
            # enabled so agents can be created on it (the agent API refuses a disabled
            # account); not validated, so the runtime treats it as "not connected"
            "is_enabled": True,
            "is_validated": False,
        }
        if any(f.name == "is_placeholder" for f in AppLLMProvider._meta.get_fields()):
            fields["is_placeholder"] = True
        account = AppLLMProvider.objects.create(**fields)
        ids = {m["id"] for m in supported}
        for m in supported:
            AppLLMProviderModel.objects.create(
                provider=account,
                model_id=m["id"],
                display_name=m.get("name") or m["id"],
                is_enabled=True,
            )
        if model and model not in ids:
            AppLLMProviderModel.objects.create(
                provider=account, model_id=model, display_name=model, is_enabled=True
            )
        logger.info(
            "agent_mode: AI account %s (%s, %s) created as a placeholder for %s",
            name,
            slug,
            model,
            app_name,
        )
        return {"status": "created", "name": name, "connected": False}
