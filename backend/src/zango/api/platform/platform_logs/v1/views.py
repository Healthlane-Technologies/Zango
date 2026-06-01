"""Platform Logs API — v1.

In-app endpoints (gated by IsPlatformUserAllowedApp via app_uuid):
    GET /api/v1/apps/<app_uuid>/logs/components/
    GET /api/v1/apps/<app_uuid>/logs/<component>/
    GET /api/v1/apps/<app_uuid>/logs/<component>/tail/
    GET /api/v1/apps/<app_uuid>/logs/<component>/streams/
    GET /api/v1/apps/<app_uuid>/logs/<component>/facets/
    GET /api/v1/apps/<app_uuid>/logs/<component>/deep-link/

Platform admin endpoints (gated by IsSuperAdminPlatformUser):
    GET/POST /api/v1/platform/logs/connectors/
    POST     /api/v1/platform/logs/connectors/test/

All responses go through get_api_response() so the frontend's useApi
hook can unwrap {success, response} consistently.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from zango.apps.platform_logs import connectors as connector_registry
from zango.apps.platform_logs.connectors.base import (
    Cursor,
    CursorDirection,
    LogFilters,
    LogLevel,
)
from zango.apps.platform_logs.connectors.exceptions import (
    ConnectorConfigError,
    ConnectorError,
    ConnectorNotFound,
    ConnectorThrottled,
    ConnectorUnauthorized,
)
from zango.apps.platform_logs.models import (
    Component,
    ConnectorType,
    LogConnectorConfig,
)
from zango.apps.shared.tenancy.models import TenantModel
from zango.core.api.utils import get_api_response
from zango.core.permissions import (
    IsPlatformUserAllowedApp,
    IsSuperAdminPlatformUser,
)

from .serializers import (
    LogConnectorConfigSerializer,
    LogPageSerializer,
    LogStreamSerializer,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Throttles
# ---------------------------------------------------------------------------


class LogBrowseThrottle(UserRateThrottle):
    rate = "30/min"
    scope = "platform_logs.browse"


class LogTailThrottle(UserRateThrottle):
    rate = "60/min"
    scope = "platform_logs.tail"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _current_environment() -> str:
    return getattr(settings, "ENV", "local")


def _ok(payload, status_code: int = 200):
    return get_api_response(True, payload, status_code)


def _err(message, status_code: int = 400, **extra):
    response = {"message": str(message)}
    response.update(extra)
    return get_api_response(False, response, status_code)


def _get_connector_for(component: str):
    """Resolve (env, component) → connector instance.

    Returns (cfg, connector) on success or raises a tuple-friendly value via
    the caller's _handle_connector_errors wrapper. For 404-style misses,
    raises ConnectorNotFound which the wrapper translates to a 404 envelope.
    """
    if component not in {c.value for c in Component}:
        raise ConnectorNotFound(f"Unknown component '{component}'.")

    try:
        cfg = LogConnectorConfig.objects.get(
            environment=_current_environment(),
            component=component,
            is_active=True,
        )
    except LogConnectorConfig.DoesNotExist as exc:
        raise ConnectorNotFound(
            f"No active connector configured for environment "
            f"'{_current_environment()}' × component '{component}'."
        ) from exc

    return cfg, connector_registry.build(cfg)


def _tenant_schema_for(app_uuid) -> str:
    tenant = get_object_or_404(TenantModel, uuid=app_uuid)
    return tenant.schema_name


def _parse_filters(request, *, default_window: timedelta) -> LogFilters:
    now = datetime.now(timezone.utc)
    since = _parse_iso(request.GET.get("since")) or (now - default_window)
    until = _parse_iso(request.GET.get("until"))

    levels: Set[LogLevel] = set()
    for piece in (request.GET.get("levels", "") or "").split(","):
        piece = piece.strip().lower()
        if not piece:
            continue
        try:
            levels.add(LogLevel(piece))
        except ValueError:
            pass

    streams_raw = request.GET.get("streams", "") or ""
    streams: Optional[List[str]] = (
        [s.strip() for s in streams_raw.split(",") if s.strip()]
        if streams_raw
        else None
    )

    try:
        limit = max(1, min(int(request.GET.get("limit", 200)), 500))
    except (TypeError, ValueError):
        limit = 200

    return LogFilters(
        since=since,
        until=until,
        q=request.GET.get("q", "") or "",
        pattern=request.GET.get("pattern", "") or "",
        levels=levels,
        streams=streams,
        limit=limit,
    )


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _handle_connector_errors(fn):
    def wrapper(self, request, *args, **kwargs):
        try:
            return fn(self, request, *args, **kwargs)
        except ConnectorNotFound as exc:
            return _err(exc, status_code=404)
        except ConnectorUnauthorized as exc:
            return _err(exc, status_code=403)
        except ConnectorThrottled as exc:
            resp = _err(
                "Upstream throttled. Try again shortly.",
                status_code=503,
                retry_after=int(exc.retry_after_seconds),
            )
            resp["Retry-After"] = str(int(exc.retry_after_seconds))
            return resp
        except ConnectorConfigError as exc:
            return _err(exc, status_code=400)
        except ConnectorError as exc:
            logger.exception("platform_logs: upstream connector error: %s", exc)
            return _err(f"Upstream connector error: {exc}", status_code=502)

    return wrapper


# ---------------------------------------------------------------------------
# In-app views
# ---------------------------------------------------------------------------


class ComponentListView(APIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    def get(self, request, app_uuid):
        env = _current_environment()
        configured = set(
            LogConnectorConfig.objects.filter(
                environment=env, is_active=True
            ).values_list("component", flat=True)
        )
        components = [
            {"key": c.value, "label": c.label, "configured": c.value in configured}
            for c in Component
        ]
        return _ok({"environment": env, "components": components})


class LogBrowseView(APIView):
    permission_classes = (IsPlatformUserAllowedApp,)
    throttle_classes = (LogBrowseThrottle,)

    @_handle_connector_errors
    def get(self, request, app_uuid, component):
        cfg, connector = _get_connector_for(component)
        filters = _parse_filters(request, default_window=timedelta(hours=1))
        filters.app_name = _tenant_schema_for(app_uuid)

        before = request.GET.get("before")
        page = (
            Cursor(token=before, direction=CursorDirection.BACKWARD)
            if before
            else None
        )
        log_page = connector.fetch(filters=filters, page=page)
        return _ok(LogPageSerializer(log_page).data)


class LogTailView(APIView):
    permission_classes = (IsPlatformUserAllowedApp,)
    throttle_classes = (LogTailThrottle,)

    @_handle_connector_errors
    def get(self, request, app_uuid, component):
        cfg, connector = _get_connector_for(component)
        filters = _parse_filters(request, default_window=timedelta(minutes=5))
        filters.app_name = _tenant_schema_for(app_uuid)

        after = request.GET.get("after")
        page = (
            Cursor(token=after, direction=CursorDirection.FORWARD)
            if after
            else None
        )
        log_page = connector.fetch(filters=filters, page=page)
        return _ok(LogPageSerializer(log_page).data)


class StreamListView(APIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    @_handle_connector_errors
    def get(self, request, app_uuid, component):
        cfg, connector = _get_connector_for(component)
        since = _parse_iso(request.GET.get("since")) or (
            datetime.now(timezone.utc) - timedelta(hours=24)
        )
        streams = connector.list_streams(since=since)
        return _ok({"streams": LogStreamSerializer(streams, many=True).data})


class FacetsView(APIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    @_handle_connector_errors
    def get(self, request, app_uuid, component):
        cfg, connector = _get_connector_for(component)
        facets = connector.facets()
        return _ok(
            {
                "levels": sorted(lv.value for lv in facets.levels),
                "streams": LogStreamSerializer(facets.streams, many=True).data,
            }
        )


class DeepLinkView(APIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    @_handle_connector_errors
    def get(self, request, app_uuid, component):
        cfg, connector = _get_connector_for(component)
        filters = _parse_filters(request, default_window=timedelta(hours=1))
        filters.app_name = _tenant_schema_for(app_uuid)
        url = connector.deep_link(filters=filters)
        if not url:
            return _err(
                "This connector does not provide a deep-link.", status_code=404
            )
        return _ok({"url": url})


# ---------------------------------------------------------------------------
# Platform admin views
# ---------------------------------------------------------------------------


class ConnectorListUpsertView(APIView):
    permission_classes = (IsSuperAdminPlatformUser,)

    def get(self, request):
        env = request.query_params.get("environment") or _current_environment()
        rows = LogConnectorConfig.objects.filter(environment=env)
        return _ok(
            {
                "environment": env,
                "rows": LogConnectorConfigSerializer(rows, many=True).data,
                "available_types": list(connector_registry.available_types()),
                "components": [c.value for c in Component],
            }
        )

    def post(self, request):
        env = request.data.get("environment") or _current_environment()
        component = request.data.get("component")
        if not component:
            return _err("component is required.", status_code=400)

        instance = LogConnectorConfig.objects.filter(
            environment=env, component=component
        ).first()
        payload = dict(request.data)
        payload["environment"] = env

        serializer = LogConnectorConfigSerializer(
            instance, data=payload, partial=False
        )
        if not serializer.is_valid():
            return _err(
                "Validation failed.",
                status_code=400,
                errors=serializer.errors,
            )
        serializer.save()
        return _ok(serializer.data, status_code=200 if instance else 201)


class ConnectorTestView(APIView):
    permission_classes = (IsSuperAdminPlatformUser,)

    @_handle_connector_errors
    def post(self, request):
        from .serializers import PARTIAL_MASK_KEYS, SECRET_KEYS

        payload = dict(request.data)
        connector_type = payload.get("connector")
        cfg_blob = dict(payload.get("config", {}) or {})
        env = payload.get("environment")
        component = payload.get("component")

        if connector_type not in {c.value for c in ConnectorType}:
            return _err(
                f"Unknown connector type '{connector_type}'.", status_code=400
            )

        # If the user is testing edits to an existing row and left the
        # secret blank (or echoed the masked key), pull from the stored
        # row so the test uses the real saved credentials.
        if env and component:
            existing = LogConnectorConfig.objects.filter(
                environment=env, component=component
            ).first()
            if existing:
                stored = existing.config or {}
                for key in SECRET_KEYS:
                    if not cfg_blob.get(key) and stored.get(key):
                        cfg_blob[key] = stored[key]
                for key in PARTIAL_MASK_KEYS:
                    incoming = cfg_blob.get(key) or ""
                    if incoming.startswith("*") and stored.get(key):
                        cfg_blob[key] = stored[key]

        stub = LogConnectorConfig(connector=connector_type, config=cfg_blob)
        connector = connector_registry.build(stub)
        streams = connector.list_streams(
            since=datetime.now(timezone.utc) - timedelta(hours=24)
        )
        return _ok(
            {
                "ok": True,
                "stream_count": len(streams),
                "newest_event_ts": (
                    streams[0].last_event_ts.isoformat()
                    if streams and streams[0].last_event_ts
                    else None
                ),
            }
        )
