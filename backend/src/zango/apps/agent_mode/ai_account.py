"""
The app's AI account for App Studio builds (AI agents plan, Step 4 and Step 5).

A spec with AI helpers needs one AI account (spec ``ai.provider``, Zango name
``app-llm`` by default) before the build's ``zango_platform.py ai`` step can create
agents on it. The build never has a key, so the account is created here through the
ORM in the app's schema, one of two ways:

- **Platform default set up** (Platform → Settings → AI accounts): the account links
  to it and works at once. The spec's model is kept when that account offers it,
  otherwise the account's default model is used.
- **No platform default**: a placeholder with the spec's service and model and no key
  (``is_placeholder``). The creator connects it later in App → AI → Providers (their
  own key, or a platform account); every helper then works without a rebuild.

An account that already exists is left alone, except a placeholder, which is linked
to the platform default as soon as one exists.
"""

import logging


logger = logging.getLogger(__name__)

SUBSCRIPTION_NOTE = (
    "Created by App Studio for this app's AI helpers. Uses the local Claude subscription "
    "login (AGENT_MODE_AUTH=subscription); for local testing only."
)
LINKED_NOTE = (
    "Created by App Studio for this app's AI helpers. Uses a platform AI account."
)
PLACEHOLDER_NOTE = (
    "Created by App Studio for this app's AI helpers. Add a key to switch them on."
)


def _via(provider) -> str:
    acc = provider.platform_account()
    return acc.name if acc is not None else ""


def ensure_ai_account(app_name: str, ai: dict) -> dict:
    """Create (or link) the spec's AI account.

    Returns ``{"status": "created" | "linked" | "exists" | "none", "name",
    "connected", "via"}``; ``via`` names the platform account it uses, if any.
    """
    agents = (ai or {}).get("agents") or []
    prov = (ai or {}).get("provider") or {}
    name = prov.get("name") or "app-llm"
    if not agents:
        return {"status": "none", "name": name, "connected": False, "via": ""}

    from django_tenants.utils import tenant_context

    from zango.apps.shared.tenancy.models import TenantModel

    tenant = TenantModel.objects.get(name=app_name)
    with tenant_context(tenant):
        from zango.ai.accounts import connect_own, link_platform
        from zango.ai.encryption import encrypt_config
        from zango.ai.providers import registry
        from zango.apps.ai.models import AppLLMProvider
        from zango.apps.ai.models.provider import AppLLMProviderModel
        from zango.apps.shared.platform_settings.models import PlatformAIAccount

        default = PlatformAIAccount.default()
        have = AppLLMProvider.objects.filter(name=name).first()

        # AGENT_MODE_AUTH=subscription (DEBUG): like Build with AI, the local Claude login
        # beats everything for new and waiting accounts, so local tests use the real AI
        # without an API key. Accounts with a key or a platform link are left alone.
        from zango.ai.providers.claude_subscription import SLUG as SUB
        from zango.ai.providers.claude_subscription import ClaudeSubscriptionProvider

        if ClaudeSubscriptionProvider.available() and (
            have is None or have.is_placeholder or have.provider_slug == SUB
        ):
            if have is None:
                have = AppLLMProvider.objects.create(
                    name=name,
                    description=SUBSCRIPTION_NOTE,
                    provider_slug=SUB,
                    config_encrypted=encrypt_config({}),
                    default_model=prov.get("model") or "",
                    monthly_budget_usd=prov.get("monthly_budget_usd"),
                    is_enabled=True,
                )
                status = "created"
            else:
                status = "exists" if have.provider_slug == SUB else "linked"
            if status != "exists":
                # the CLI takes the spec's model id (aliases included) as it is
                want = prov.get("model") or have.default_model
                models = list(ClaudeSubscriptionProvider.supported_models)
                if want and want not in {m["id"] for m in models}:
                    models.insert(0, {"id": want, "name": want})
                connect_own(have, SUB, {}, want, models)
            return {
                "status": status,
                "name": name,
                "connected": True,
                "via": "your Claude subscription (local testing)",
            }

        if have is not None:
            # P2 builds made placeholders before the flag existed: no key, never checked
            waiting = have.is_placeholder or (
                have.description == PLACEHOLDER_NOTE and not have.is_validated
            )
            if waiting and default is not None:
                link_platform(have, default, prov.get("model"))
                logger.info(
                    "agent_mode: AI account %s of %s linked to platform account %s",
                    name,
                    app_name,
                    default.name,
                )
                return {
                    "status": "linked",
                    "name": name,
                    "connected": True,
                    "via": default.name,
                }
            return {
                "status": "exists",
                "name": name,
                "connected": have.is_connected,
                "via": _via(have),
            }
        if default is not None:
            account = AppLLMProvider.objects.create(
                name=name,
                description=LINKED_NOTE,
                provider_slug=default.provider_slug,
                config_encrypted=encrypt_config({}),
                default_model=default.default_model,
                monthly_budget_usd=prov.get("monthly_budget_usd"),
                is_enabled=True,
            )
            link_platform(account, default, prov.get("model"))
            logger.info(
                "agent_mode: AI account %s for %s linked to platform account %s",
                name,
                app_name,
                default.name,
            )
            return {
                "status": "created",
                "name": name,
                "connected": True,
                "via": default.name,
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
        return {"status": "created", "name": name, "connected": False, "via": ""}
