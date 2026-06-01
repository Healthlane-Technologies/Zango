"""Registry mapping ConnectorType → concrete connector factory.

Imports are deferred so that adding boto3 / future SDK deps to one connector
doesn't pay a startup cost when the project only uses a different type.

Usage:

    from zango.apps.shared.platform_logs.connectors import build
    from zango.apps.shared.platform_logs.models import LogConnectorConfig

    cfg = LogConnectorConfig.objects.get(environment="staging", component="app")
    connector = build(cfg)
    page = connector.fetch(filters=..., page=None)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict

from zango.apps.shared.platform_logs.connectors.exceptions import ConnectorConfigError
from zango.apps.shared.platform_logs.models import ConnectorType, LogConnectorConfig


if TYPE_CHECKING:
    from zango.apps.shared.platform_logs.connectors.base import LogConnector


# ---------------------------------------------------------------------------
# Lazy factories — keyed by the ConnectorType enum value (string).
# ---------------------------------------------------------------------------


def _cloudwatch_factory(cfg: LogConnectorConfig) -> "LogConnector":
    # Local import keeps boto3 out of the import graph until needed.
    from zango.apps.shared.platform_logs.connectors.cloudwatch import (
        CloudWatchConnector,
    )

    return CloudWatchConnector(cfg.config)


_REGISTRY: Dict[str, Callable[[LogConnectorConfig], "LogConnector"]] = {
    ConnectorType.CLOUDWATCH.value: _cloudwatch_factory,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build(cfg: LogConnectorConfig) -> "LogConnector":
    """Resolve a config row to a live connector instance.

    Raises ConnectorConfigError if the type isn't registered.
    """
    try:
        factory = _REGISTRY[cfg.connector]
    except KeyError as exc:
        raise ConnectorConfigError(
            f"No connector registered for type '{cfg.connector}'. "
            f"Known types: {sorted(_REGISTRY)}"
        ) from exc

    return factory(cfg)


def available_types() -> list[str]:
    """Return the connector types this build supports."""
    return sorted(_REGISTRY)
