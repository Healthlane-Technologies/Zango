"""Platform-wide general settings.

Mounted at /api/v1/platform/general/ — public schema, not app-scoped.

Everything here applies to apps **created after** it is saved. Existing apps
keep whatever they were stamped with, which is why no endpoint writes to a
tenant row.
"""

from __future__ import annotations

import logging

from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from zango.apps.shared.platform_settings.domains import (
    candidate_domains,
    is_valid_base_domain,
    normalise_base_domain,
)
from zango.apps.shared.platform_settings.models import PlatformSettings
from zango.apps.shared.tenancy.utils import (
    DATEFORMAT,
    DATETIMEFORMAT,
    DEFAULT_THEME_CONFIG,
    TIMEZONES,
)
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response


log = logging.getLogger(__name__)

_WRITABLE = (
    "auto_domain_enabled",
    "base_domain",
    "auto_domain_is_primary",
    "default_timezone",
    "default_date_format",
    "default_datetime_format",
    "default_language",
    "default_theme_config",
)
_BOOLS = ("auto_domain_enabled", "auto_domain_is_primary")


def _jsonable(value):
    """`get_api_response` serializes with a bare `json.dumps()`, so a Decimal
    or datetime reaching it raises and the request 500s."""
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


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def _serialize(row: PlatformSettings) -> dict:
    return _jsonable(
        {
            "auto_domain_enabled": row.auto_domain_enabled,
            "base_domain": row.base_domain,
            "auto_domain_is_primary": row.auto_domain_is_primary,
            "base_domain_valid": (
                is_valid_base_domain(row.base_domain) if row.base_domain else None
            ),
            "default_timezone": row.default_timezone,
            "default_date_format": row.default_date_format,
            "default_datetime_format": row.default_datetime_format,
            "default_language": row.default_language,
            "default_theme_config": row.default_theme_config or None,
            "modified_at": getattr(row, "modified_at", None),
        }
    )


def _options() -> dict:
    """Choices the UI renders, sourced from the same tuples the tenant model
    validates against — so the two cannot drift apart."""
    from django.conf import settings as dj

    return {
        "timezones": [tz for tz, _ in TIMEZONES],
        "date_formats": [{"value": v, "example": label} for v, label in DATEFORMAT],
        "datetime_formats": [
            {"value": v, "example": label} for v, label in DATETIMEFORMAT
        ],
        "languages": [
            {"value": code, "label": label}
            for code, label in getattr(dj, "LANGUAGES", []) or []
        ],
        "default_theme_config": DEFAULT_THEME_CONFIG,
    }


class PlatformGeneralSettingsView(ZangoGenericPlatformAPIView):
    """GET/POST /api/v1/platform/general/"""

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        try:
            row = PlatformSettings.load()
            data = _serialize(row)
            data["options"] = _options()
            return get_api_response(True, data, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("platform_settings: load failed")
            return get_api_response(False, {"message": str(exc)}, 500)

    def post(self, request, *args, **kwargs):
        try:
            row = PlatformSettings.load()
            payload = request.data or {}

            for field in _WRITABLE:
                if field not in payload:
                    continue
                value = payload.get(field)
                if field in _BOOLS:
                    setattr(row, field, _as_bool(value))
                elif field == "base_domain":
                    setattr(row, field, normalise_base_domain(value))
                elif field == "default_theme_config":
                    # An empty value means "fall back to the framework theme".
                    setattr(row, field, value if isinstance(value, dict) and value else None)
                else:
                    setattr(row, field, (value or "").strip() if value else "")

            # Refuse the combination that would silently do nothing: automatic
            # allocation on, with nothing to allocate under.
            if row.auto_domain_enabled and not is_valid_base_domain(row.base_domain):
                return get_api_response(
                    False,
                    {
                        "message": (
                            "Enter a valid base domain (e.g. zelthy.com) before "
                            "turning on automatic domains."
                        )
                    },
                    400,
                )

            row.save()
            data = _serialize(row)
            data["options"] = _options()
            data["message"] = "Saved. Applies to apps created from now on."
            return get_api_response(True, data, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("platform_settings: save failed")
            return get_api_response(False, {"message": str(exc)}, 500)


class SubdomainPreviewView(ZangoGenericPlatformAPIView):
    """GET /api/v1/platform/general/preview-subdomain/?base_domain=zelthy.com

    Shows what the next few apps would actually be given, so an operator can
    see the shape before committing to it.
    """

    def get(self, request, *args, **kwargs):
        try:
            base = request.GET.get("base_domain") or PlatformSettings.load().base_domain
            if not is_valid_base_domain(base):
                return get_api_response(
                    False, {"message": "Enter a valid domain, e.g. zelthy.com"}, 400
                )
            samples = list(candidate_domains(base, attempts=3))
            return get_api_response(
                True,
                {"base_domain": normalise_base_domain(base), "samples": samples},
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("platform_settings: subdomain preview failed")
            return get_api_response(False, {"message": str(exc)}, 500)
