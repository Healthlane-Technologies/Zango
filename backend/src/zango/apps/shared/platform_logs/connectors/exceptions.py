"""Errors raised by log connectors.

Designed to map cleanly to HTTP responses at the API layer:
    ConnectorNotFound       → 404
    ConnectorThrottled      → 503 with Retry-After
    ConnectorConfigError    → 400
    ConnectorError (any)    → 502
"""

from __future__ import annotations


class ConnectorError(Exception):
    """Base error for any failure inside a connector."""


class ConnectorConfigError(ConnectorError):
    """The config dict is missing fields, malformed, or fails validation."""


class ConnectorNotFound(ConnectorError):
    """The target resource (log group, stream, etc.) does not exist."""


class ConnectorThrottled(ConnectorError):
    """The backing service throttled the connector. Caller should back off."""

    def __init__(self, message: str, retry_after_seconds: float = 5.0):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class ConnectorUnauthorized(ConnectorError):
    """The connector lacks IAM permissions for the call it made."""
