"""Platform AI accounts: AI service credentials set up once for every app.

Mounted at /api/v1/platform/ai-accounts/ (public schema, super admins only).

An app links to an account instead of holding a key of its own: App Studio links
each new app's AI helpers to the default account, and an app admin can pick any
working account in App → AI → Providers. Keys are write-only: they are accepted,
checked live and stored encrypted, and only ever returned masked.
"""

from __future__ import annotations

import logging

from rest_framework.parsers import JSONParser

from django.db import transaction
from django.utils import timezone

from zango.ai.accounts import apps_linked_to, check_credentials
from zango.ai.providers.registry import PROVIDER_REGISTRY, get_available_providers
from zango.apps.shared.platform_settings.models import PlatformAIAccount
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response
from zango.core.permissions import IsSuperAdminPlatformUser


log = logging.getLogger(__name__)


def _jsonable(value):
    from datetime import date, datetime
    from decimal import Decimal

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _status(acc: PlatformAIAccount) -> str:
    if not acc.is_enabled:
        return "off"
    return "connected" if acc.is_validated else "failing"


def _serialize(acc: PlatformAIAccount, apps: list | None = None) -> dict:
    cls = PROVIDER_REGISTRY.get(acc.provider_slug)
    out = {
        "uuid": str(acc.uuid),
        "name": acc.name,
        "description": acc.description,
        "provider_slug": acc.provider_slug,
        "service_name": getattr(cls, "display_name", acc.provider_slug),
        "default_model": acc.default_model,
        "models": acc.model_list or [],
        "app_monthly_budget_usd": acc.app_monthly_budget_usd,
        "is_default": acc.is_default,
        "is_enabled": acc.is_enabled,
        "is_validated": acc.is_validated,
        "status": _status(acc),
        "last_validated_at": acc.last_validated_at,
        "validation_error": acc.validation_error,
        "masked_config": acc.masked_config(),
        "created_at": acc.created_at,
        "modified_at": acc.modified_at,
    }
    if apps is not None:
        out["apps"] = apps
    return _jsonable(out)


def _err(message: str, status: int = 400, **extra):
    return get_api_response(False, {"message": message, **extra}, status)


def _merge_secrets(config: dict, saved: dict, secrets: list[str]) -> dict:
    """Blank or masked secrets keep the saved value."""
    out = dict(config or {})
    for name in secrets:
        v = out.get(name)
        if (v is None or v == "" or "****" in str(v)) and saved.get(name):
            out[name] = saved[name]
    return out


def _pick_models(fetched: list[dict], wanted: list | None) -> list[dict]:
    if not wanted:
        return fetched
    keep = set(wanted)
    return [m for m in fetched if m.get("id") in keep] or fetched


def _needs_config(slug: str) -> bool:
    fields = getattr(PROVIDER_REGISTRY.get(slug), "config_fields", []) or []
    return any(
        f.get("required") and f.get("options_from") != "supported_models"
        for f in fields
    )


def _budget(value):
    if value in (None, ""):
        return None
    from decimal import Decimal, InvalidOperation

    try:
        d = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("Monthly budget must be a number.")
    if d < 0:
        raise ValueError("Monthly budget can't be negative.")
    return d


class _Base(ZangoGenericPlatformAPIView):
    permission_classes = (IsSuperAdminPlatformUser,)
    parser_classes = [JSONParser]

    def _get(self, account_uuid):
        return PlatformAIAccount.objects.filter(uuid=account_uuid).first()


class PlatformAIAccountsView(_Base):
    """GET  /api/v1/platform/ai-accounts/  accounts + the services that can be added
    POST /api/v1/platform/ai-accounts/  {name, provider_slug, config, default_model,
         model_ids?, description?, app_monthly_budget_usd?, is_default?}"""

    def get(self, request, *args, **kwargs):
        try:
            accounts = list(PlatformAIAccount.objects.all())
            counts = {}
            if request.GET.get("usage") != "0":
                for a in accounts:
                    counts[str(a.uuid)] = apps_linked_to(a.uuid)
            rows = [_serialize(a, counts.get(str(a.uuid))) for a in accounts]
            return get_api_response(
                True, {"accounts": rows, "services": get_available_providers()}, 200
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("ai_accounts: list failed")
            return _err(str(exc), 500)

    def post(self, request, *args, **kwargs):
        d = request.data or {}
        name = (d.get("name") or "").strip()
        slug = (d.get("provider_slug") or "").strip()
        config = d.get("config") or {}
        model = (d.get("default_model") or "").strip()
        if not name:
            return _err("Give the account a name.")
        if PlatformAIAccount.objects.filter(name=name).exists():
            return _err(f"An account called '{name}' already exists.")
        if slug not in PROVIDER_REGISTRY:
            return _err(f"Unknown AI service '{slug}'.")
        if not isinstance(config, dict) or (_needs_config(slug) and not config):
            return _err("Enter the credentials for this service.")
        try:
            budget = _budget(d.get("app_monthly_budget_usd"))
        except ValueError as exc:
            return _err(str(exc))

        ok, error, fetched = check_credentials(slug, config, model or None)
        if not ok:
            return _err(error, 400, error_type="auth_error")
        models = _pick_models(fetched, d.get("model_ids"))
        ids = [m["id"] for m in models]
        if not model or (ids and model not in ids):
            model = ids[0] if ids else model

        try:
            with transaction.atomic():
                first = not PlatformAIAccount.objects.exists()
                acc = PlatformAIAccount(
                    name=name,
                    description=(d.get("description") or "").strip(),
                    provider_slug=slug,
                    default_model=model,
                    model_list=models,
                    app_monthly_budget_usd=budget,
                    is_default=bool(d.get("is_default")) or first,
                    is_enabled=True,
                    is_validated=True,
                    last_validated_at=timezone.now(),
                )
                acc.set_config(config)
                acc.save()
            return get_api_response(
                True, {"account": _serialize(acc, []), "message": "Connected."}, 201
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("ai_accounts: create failed")
            return _err(str(exc), 500)


class PlatformAIAccountCheckView(_Base):
    """POST /api/v1/platform/ai-accounts/check/
    {provider_slug, config, account_uuid?, default_model?} → {models}. Saves nothing;
    with account_uuid, blank or masked secrets use that account's saved ones."""

    def post(self, request, *args, **kwargs):
        d = request.data or {}
        slug = (d.get("provider_slug") or "").strip()
        config = d.get("config") or {}
        if slug not in PROVIDER_REGISTRY:
            return _err(f"Unknown AI service '{slug}'.")
        if d.get("account_uuid"):
            acc = self._get(d["account_uuid"])
            if acc is None:
                return _err("Account not found.", 404)
            config = _merge_secrets(config, acc.get_config(), acc.secret_fields())
        if not isinstance(config, dict) or (_needs_config(slug) and not config):
            return _err("Enter the credentials for this service.")
        ok, error, models = check_credentials(
            slug, config, d.get("default_model") or None
        )
        if not ok:
            return _err(error, 400, error_type="auth_error")
        return get_api_response(True, {"models": _jsonable(models)}, 200)


class PlatformAIAccountDetailView(_Base):
    """GET / PUT / DELETE /api/v1/platform/ai-accounts/<uuid>/"""

    def get(self, request, account_uuid, *args, **kwargs):
        acc = self._get(account_uuid)
        if acc is None:
            return _err("Account not found.", 404)
        return get_api_response(
            True, {"account": _serialize(acc, apps_linked_to(acc.uuid))}, 200
        )

    def put(self, request, account_uuid, *args, **kwargs):
        acc = self._get(account_uuid)
        if acc is None:
            return _err("Account not found.", 404)
        d = request.data or {}
        try:
            if "name" in d:
                name = (d.get("name") or "").strip()
                if not name:
                    return _err("Give the account a name.")
                if (
                    PlatformAIAccount.objects.exclude(pk=acc.pk)
                    .filter(name=name)
                    .exists()
                ):
                    return _err(f"An account called '{name}' already exists.")
                acc.name = name
            if "description" in d:
                acc.description = (d.get("description") or "").strip()
            if "app_monthly_budget_usd" in d:
                acc.app_monthly_budget_usd = _budget(d.get("app_monthly_budget_usd"))
            if "is_enabled" in d:
                acc.is_enabled = bool(d.get("is_enabled"))
            if "is_default" in d:
                acc.is_default = bool(d.get("is_default"))
            if acc.is_default and not acc.is_enabled:
                return _err("Switch the account on before making it the default.")

            model = (d.get("default_model") or acc.default_model or "").strip()
            fetched = None
            if isinstance(d.get("config"), dict) and d["config"]:
                config = _merge_secrets(
                    d["config"], acc.get_config(), acc.secret_fields()
                )
                ok, error, fetched = check_credentials(
                    acc.provider_slug, config, model or None
                )
                if not ok:
                    return _err(error, 400, error_type="auth_error")
                acc.set_config(config)
                acc.is_validated = True
                acc.last_validated_at = timezone.now()
                acc.validation_error = ""
            if "model_ids" in d or fetched is not None:
                pool = fetched or acc.model_list or []
                if "model_ids" in d and d.get("models"):
                    pool = d["models"]  # the list the UI loaded, so ids can be added
                acc.model_list = _pick_models(pool, d.get("model_ids"))
            ids = acc.model_ids()
            if model and (not ids or model in ids):
                acc.default_model = model
            elif ids:
                acc.default_model = ids[0]
            acc.save()
            return get_api_response(
                True,
                {
                    "account": _serialize(acc, apps_linked_to(acc.uuid)),
                    "message": "Saved.",
                },
                200,
            )
        except ValueError as exc:
            return _err(str(exc))
        except Exception as exc:  # noqa: BLE001
            log.exception("ai_accounts: update failed")
            return _err(str(exc), 500)

    def delete(self, request, account_uuid, *args, **kwargs):
        acc = self._get(account_uuid)
        if acc is None:
            return _err("Account not found.", 404)
        apps = apps_linked_to(acc.uuid)
        if apps:
            return _err(
                f"{len(apps)} app(s) use this account. Switch them to another account, "
                "or turn this one off instead.",
                409,
                error_code="ACCOUNT_IN_USE",
                apps=apps,
            )
        was_default = acc.is_default
        acc.delete()
        if was_default:
            nxt = PlatformAIAccount.objects.filter(
                is_enabled=True, is_validated=True
            ).first()
            if nxt is not None:
                nxt.is_default = True
                nxt.save()
        return get_api_response(True, {"message": "Deleted."}, 200)


class PlatformAIAccountValidateView(_Base):
    """POST /api/v1/platform/ai-accounts/<uuid>/validate/  re-check the saved key."""

    def post(self, request, account_uuid, *args, **kwargs):
        acc = self._get(account_uuid)
        if acc is None:
            return _err("Account not found.", 404)
        ok, error, _ = check_credentials(
            acc.provider_slug, acc.get_config(), acc.default_model or None
        )
        acc.is_validated = ok
        acc.last_validated_at = timezone.now()
        acc.validation_error = "" if ok else error
        acc.save()
        if not ok:
            return _err(error, 400, error_type="auth_error", account=_serialize(acc))
        return get_api_response(
            True, {"account": _serialize(acc), "message": "The key works."}, 200
        )
