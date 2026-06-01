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
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
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


def _get_connector_for(component: str):
    """Look up the LogConnectorConfig for the current env × component, then
    instantiate the connector. Returns (cfg, connector) or raises 404."""
    if component not in {c.value for c in Component}:
        from rest_framework.exceptions import NotFound

        raise NotFound(f"Unknown component '{component}'.")

    try:
        cfg = LogConnectorConfig.objects.get(
            environment=_current_environment(),
            component=component,
            is_active=True,
        )
    except LogConnectorConfig.DoesNotExist as exc:
        from rest_framework.exceptions import NotFound

        raise NotFound(
            f"No active connector configured for environment "
            f"'{_current_environment()}' × component '{component}'."
        ) from exc

    return cfg, connector_registry.build(cfg)


def _tenant_schema_for(app_uuid) -> str:
    """Resolve an app UUID to the tenant's schema name (used as app_name filter)."""
    tenant = get_object_or_404(TenantModel, uuid=app_uuid)
    return tenant.schema_name


def _parse_filters(request, *, default_window: timedelta) -> LogFilters:
    """Translate query params into a LogFilters."""
    now = datetime.now(timezone.utc)
    since = _parse_iso(request.GET.get("since")) or (now - default_window)
    until = _parse_iso(request.GET.get("until"))

    levels_raw = request.GET.get("levels", "")
    levels: Set[LogLevel] = set()
    for piece in levels_raw.split(","):
        piece = piece.strip().lower()
        if not piece:
            continue
        try:
            levels.add(LogLevel(piece))
        except ValueError:
            pass

    streams_raw = request.GET.get("streams", "")
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
        # Accept both naive and aware; treat naive as UTC.
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _handle_connector_errors(fn):
    """Wrap a view method so connector exceptions become proper HTTP responses."""

    def wrapper(self, request, *args, **kwargs):
        try:
            return fn(self, request, *args, **kwargs)
        except ConnectorNotFound as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ConnectorUnauthorized as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ConnectorThrottled as exc:
            resp = Response(
                {"detail": "Upstream throttled. Try again shortly."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
            resp["Retry-After"] = str(int(exc.retry_after_seconds))
            return resp
        except ConnectorConfigError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectorError as exc:
            logger.exception("platform_logs: upstream connector error: %s", exc)
            return Response(
                {"detail": f"Upstream connector error: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    return wrapper


# ---------------------------------------------------------------------------
# In-app views — gated by IsPlatformUserAllowedApp
# ---------------------------------------------------------------------------


class ComponentListView(APIView):
    """List the components that have an active connector for the current env."""

    permission_classes = (IsPlatformUserAllowedApp,)

    def get(self, request, app_uuid):
        env = _current_environment()
        configured = set(
            LogConnectorConfig.objects.filter(
                environment=env, is_active=True
            ).values_list("component", flat=True)
        )
        components = [
            {
                "key": c.value,
                "label": c.label,
                "configured": c.value in configured,
            }
            for c in Component
        ]
        return Response({"environment": env, "components": components})


class LogBrowseView(APIView):
    """Backward (historical) cursor pagination."""

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
        return Response(LogPageSerializer(log_page).data)


class LogTailView(APIView):
    """Forward (live tail) cursor pagination."""

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
        return Response(LogPageSerializer(log_page).data)


class StreamListView(APIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    @_handle_connector_errors
    def get(self, request, app_uuid, component):
        cfg, connector = _get_connector_for(component)
        since = _parse_iso(request.GET.get("since")) or (
            datetime.now(timezone.utc) - timedelta(hours=24)
        )
        streams = connector.list_streams(since=since)
        return Response({"streams": LogStreamSerializer(streams, many=True).data})


class FacetsView(APIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    @_handle_connector_errors
    def get(self, request, app_uuid, component):
        cfg, connector = _get_connector_for(component)
        facets = connector.facets()
        return Response(
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
            return Response(
                {"detail": "This connector does not provide a deep-link."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"url": url})


# ---------------------------------------------------------------------------
# Platform admin views — gated by IsSuperAdminPlatformUser
# ---------------------------------------------------------------------------


class ConnectorListUpsertView(APIView):
    """GET → list all configs.  POST → upsert by (environment, component)."""

    permission_classes = (IsSuperAdminPlatformUser,)

    def get(self, request):
        env = request.query_params.get("environment") or _current_environment()
        rows = LogConnectorConfig.objects.filter(environment=env)
        return Response(
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
            return Response(
                {"detail": "component is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = LogConnectorConfig.objects.filter(
            environment=env, component=component
        ).first()
        payload = dict(request.data)
        payload["environment"] = env
        serializer = LogConnectorConfigSerializer(instance, data=payload, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_200_OK if instance else status.HTTP_201_CREATED,
        )


class ConnectorTestView(APIView):
    """Live-fire test: build the connector from the payload, call
    list_streams, and return whether it worked."""

    permission_classes = (IsSuperAdminPlatformUser,)

    @_handle_connector_errors
    def post(self, request):
        payload = dict(request.data)
        connector_type = payload.get("connector")
        cfg_blob = payload.get("config", {})
        if connector_type not in {c.value for c in ConnectorType}:
            return Response(
                {"detail": f"Unknown connector type '{connector_type}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stub = LogConnectorConfig(connector=connector_type, config=cfg_blob)
        connector = connector_registry.build(stub)
        streams = connector.list_streams(
            since=datetime.now(timezone.utc) - timedelta(hours=24)
        )
        return Response(
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
