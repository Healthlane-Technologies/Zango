"""Platform-level Build with AI configuration.

Mounted at /api/v1/platform/agent-mode/ — public schema, not app-scoped,
because the credential and model choices apply to every app.

The API key is write-only in both directions: it is accepted on save and
never returned, only a masked form. An operator can rotate it without a
redeploy, which is the point of storing it here rather than in the env.
"""

from __future__ import annotations

import logging

from django.conf import settings as dj_settings
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from zango.apps.shared.agent_mode.models import AgentModeSettings
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response


log = logging.getLogger(__name__)

# Only these may be written from the UI. Anything else is ignored rather than
# silently persisted.
_WRITABLE = (
    "is_enabled",
    "provider",
    "default_model",
    "default_effort",
    "max_run_seconds",
    "max_turns",
    "max_budget_usd",
    "analyst_model",
    "analyst_effort",
    "analyst_max_turns",
    "analyst_budget_usd",
    "monthly_budget_usd",
    "allow_frontend_build",
    "ensure_packages",
)
_BOOLS = ("is_enabled", "allow_frontend_build", "ensure_packages")
_INTS = ("max_run_seconds", "max_turns", "analyst_max_turns")
_DECIMALS = ("max_budget_usd", "analyst_budget_usd", "monthly_budget_usd")


def _jsonable(value):
    """Coerce to something `json.dumps` accepts.

    `get_api_response` serializes with a bare `json.dumps()`, so a Decimal or
    datetime field reaching it raises and the whole request 500s — which is
    how this broke every save until it was caught.
    """
    from datetime import date, datetime
    from decimal import Decimal

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _coerce(obj, _depth: int = 0):
    """Recursively make a payload json.dumps-safe.

    `get_api_response` serializes with a bare `json.dumps()`, so one stray
    Decimal anywhere in the tree 500s the request. Coercing at the boundary
    means a field added later cannot reintroduce that.
    """
    if _depth > 8:
        return obj
    if isinstance(obj, dict):
        return {k: _coerce(v, _depth + 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_coerce(v, _depth + 1) for v in obj]
    return _jsonable(obj)


def _payload(row, cfg=None):
    from zango.apps.agent_mode.config import load_config, node_available

    cfg = cfg or load_config()
    data = {
        "configured": row is not None,
        "source": cfg.source,
        # Never the key itself — only whether one exists, and a masked form.
        "has_api_key": False,
        "masked_config": {},
        "environment": {
            "node_available": node_available(),
            "env_api_key_present": bool(getattr(dj_settings, "ANTHROPIC_API_KEY", "")),
        },
        "resolved": {
            "enabled": cfg.enabled,
            "model": cfg.model or None,
            "effort": cfg.effort or None,
            "max_run_seconds": cfg.max_run_seconds,
            "max_turns": cfg.max_turns,
            "max_budget_usd": _jsonable(cfg.max_budget_usd),
            "analyst_model": cfg.analyst_model or None,
            "analyst_effort": cfg.analyst_effort or None,
            "analyst_max_turns": cfg.analyst_max_turns,
            "analyst_budget_usd": _jsonable(cfg.analyst_budget_usd),
            "allow_frontend_build": cfg.allow_frontend_build,
            "ensure_packages": cfg.ensure_packages,
        },
    }
    if row is not None:
        config = row.get_config() or {}
        data["has_api_key"] = bool(config.get("api_key"))
        data["masked_config"] = row.masked_config()
        data["settings"] = {
            field: _jsonable(getattr(row, field)) for field in _WRITABLE
        }
        data["is_validated"] = row.is_validated
        data["last_validated_at"] = (
            row.last_validated_at.isoformat() if row.last_validated_at else None
        )
    else:
        data["settings"] = None
        data["is_validated"] = False
        data["last_validated_at"] = None
    return _coerce(data)


class AgentModeSettingsView(ZangoGenericPlatformAPIView):
    """GET/POST /api/v1/platform/agent-mode/settings/"""

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        try:
            return get_api_response(True, _payload(AgentModeSettings.load()), 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: settings read failed")
            return get_api_response(False, {"message": str(exc)}, 500)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            row = AgentModeSettings.load()
            if row is None:
                row = AgentModeSettings(singleton_id=1)

            for field in _WRITABLE:
                if field not in data:
                    continue
                value = data.get(field)
                if field in _BOOLS:
                    setattr(row, field, _as_bool(value))
                elif field in _INTS:
                    setattr(row, field, int(value) if str(value).strip() else None)
                elif field in _DECIMALS:
                    setattr(row, field, value if str(value).strip() else None)
                else:
                    setattr(row, field, (value or "").strip())

            # The key is optional on every save: omitting it keeps the stored
            # one, so "edit the model, keep the key" works.
            api_key = (data.get("api_key") or "").strip()
            if api_key:
                config = row.get_config() if row.pk else {}
                config["api_key"] = api_key
                row.set_config(config)
                row.is_validated = False
                row.last_validated_at = None
            elif data.get("clear_api_key"):
                config = row.get_config() if row.pk else {}
                config.pop("api_key", None)
                row.set_config(config)
                row.is_validated = False

            row.save()
            return get_api_response(True, _payload(row), 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: settings write failed")
            return get_api_response(False, {"message": str(exc)}, 500)


class AgentModeSettingsValidateView(ZangoGenericPlatformAPIView):
    """POST /api/v1/platform/agent-mode/settings/validate/

    A one-token call, so an operator finds out the key works here rather than
    twelve minutes into a build.
    """

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        from django.utils import timezone

        from zango.apps.agent_mode.config import load_config
        from zango.apps.agent_mode.credentials import resolve_credentials

        try:
            creds = resolve_credentials()
            if not creds.is_usable:
                return get_api_response(
                    False,
                    {"message": "No API key is configured.", "valid": False},
                    200,
                )

            cfg = load_config()
            model = cfg.model or "claude-opus-5"
            try:
                import anthropic

                client = anthropic.Anthropic(api_key=creds.api_key, timeout=20)
                client.messages.create(
                    model=model,
                    max_tokens=1,
                    messages=[{"role": "user", "content": "hi"}],
                )
            except Exception as exc:  # noqa: BLE001
                message = str(exc)
                hint = (
                    "The key was rejected."
                    if "authentication" in message.lower()
                    else message
                )
                return get_api_response(
                    True,
                    {"valid": False, "message": hint[:400], "model": model},
                    200,
                )

            row = AgentModeSettings.load()
            if row is not None:
                row.is_validated = True
                row.last_validated_at = timezone.now()
                row.save(update_fields=["is_validated", "last_validated_at"])

            return get_api_response(
                True,
                {
                    "valid": True,
                    "message": f"Key works with {model}.",
                    "model": model,
                    "source": creds.source,
                },
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: validate failed")
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Build with Agent — app scaffolding
# ---------------------------------------------------------------------------


class AgentModeAvailabilityPlatformView(ZangoGenericPlatformAPIView):
    """GET /api/v1/platform/agent-mode/availability/

    The app-scoped probe with the workspace checks dropped, because this is
    asked before any app exists. Drives whether the landing page offers
    "Build with Agent" at all.
    """

    def get(self, request, *args, **kwargs):
        from zango.apps.agent_mode.availability import probe

        try:
            return get_api_response(True, probe(None), 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: platform availability probe failed")
            return get_api_response(False, {"message": str(exc)}, 500)


class AgentAppScaffoldCreateView(ZangoGenericPlatformAPIView):
    """POST /api/v1/platform/agent-mode/scaffolds/

    Takes the one-line ask and returns immediately — naming and app creation
    both happen on a worker, because the user is looking at a chat window and
    a synchronous launch would block it for a minute or more.
    """

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    MAX_PROMPT_CHARS = 10_000

    def post(self, request, *args, **kwargs):
        from django.conf import settings as dj
        from django.db import transaction

        from zango.apps.agent_mode.availability import probe
        from zango.apps.agent_mode.scaffold import state_payload
        from zango.apps.agent_mode.tasks import agent_app_scaffold
        from zango.apps.shared.agent_mode.models import AgentAppScaffold

        try:
            status_probe = probe(None)
            if not status_probe["available"]:
                return get_api_response(
                    False,
                    {
                        "message": "Build with AI is not available on this platform.",
                        "reasons": status_probe["reasons"],
                    },
                    409,
                )

            prompt = (request.data.get("prompt") or "").strip()
            if not prompt:
                return get_api_response(
                    False, {"message": "Describe what you want to build."}, 400
                )
            if len(prompt) > self.MAX_PROMPT_CHARS:
                return get_api_response(
                    False, {"message": "That description is too long."}, 400
                )

            user = getattr(request, "user", None)
            scaffold = AgentAppScaffold.objects.create(
                prompt=prompt,
                created_by_label=(getattr(user, "email", "") or str(user or ""))[:255],
            )

            def _dispatch():
                result = agent_app_scaffold.apply_async(
                    args=[str(scaffold.object_uuid)],
                    queue=getattr(dj, "AGENT_MODE_QUEUE", "") or None,
                    soft_time_limit=600,
                    time_limit=660,
                )
                AgentAppScaffold.objects.filter(pk=scaffold.pk).update(
                    celery_task_id=(result.id or "")[:64]
                )

            # ATOMIC_REQUESTS wraps this view: dispatching inline would race
            # the worker against the row's visibility.
            transaction.on_commit(_dispatch)
            return get_api_response(True, state_payload(scaffold), 201)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: scaffold create failed")
            return get_api_response(False, {"message": str(exc)}, 500)


class AgentAppScaffoldDetailView(ZangoGenericPlatformAPIView):
    """GET /api/v1/platform/agent-mode/scaffolds/<uuid>/ — one poll."""

    def get(self, request, scaffold_uuid, *args, **kwargs):
        from zango.apps.agent_mode.scaffold import state_payload
        from zango.apps.shared.agent_mode.models import AgentAppScaffold

        try:
            scaffold = AgentAppScaffold.objects.filter(
                object_uuid=scaffold_uuid
            ).first()
            if scaffold is None:
                return get_api_response(False, {"message": "not found"}, 404)
            return get_api_response(True, state_payload(scaffold), 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: scaffold detail failed")
            return get_api_response(False, {"message": str(exc)}, 500)


class AgentAppScaffoldRequirementView(ZangoGenericPlatformAPIView):
    """POST /api/v1/platform/agent-mode/scaffolds/<uuid>/requirement/

    The hand-off. Called once the app reports deployed: it opens the
    requirement conversation inside the new app, seeded with the ask the user
    already typed, and returns where to continue it. From here the flow is the
    ordinary app-scoped Agent Mode chat.
    """

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, scaffold_uuid, *args, **kwargs):
        from zango.apps.agent_mode.scaffold import (
            APP_FAILED,
            APP_READY,
            app_creation_state,
            handoff_requirement,
            state_payload,
        )
        from zango.apps.shared.agent_mode.models import AgentAppScaffold

        try:
            # Locked for the request: two tabs polling the same scaffold would
            # otherwise both see requirement_uuid unset and open two
            # conversations about the same ask.
            scaffold = (
                AgentAppScaffold.objects.select_for_update()
                .filter(object_uuid=scaffold_uuid)
                .first()
            )
            if scaffold is None:
                return get_api_response(False, {"message": "not found"}, 404)

            if not scaffold.requirement_uuid:
                state, error = app_creation_state(scaffold)
                if state == APP_FAILED:
                    return get_api_response(
                        False,
                        {
                            "message": "The app could not be created.",
                            "detail": error,
                        },
                        409,
                    )
                if state != APP_READY:
                    return get_api_response(
                        False,
                        {
                            "message": "The app is still being created.",
                            "app_state": state,
                        },
                        409,
                    )

            handoff_requirement(scaffold)
            return get_api_response(True, state_payload(scaffold), 201)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: scaffold hand-off failed")
            return get_api_response(False, {"message": str(exc)}, 500)
