"""LogConnector protocol and the common datatypes returned by every connector.

Concrete connectors (CloudWatchConnector, future DynamoDBConnector, etc.)
implement this protocol so the API / frontend code stays connector-agnostic.

Read-only by design: nothing here can mutate the upstream log store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set, runtime_checkable


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"  # connector couldn't parse a level from the line


class CursorDirection(str, Enum):
    BACKWARD = "backward"  # paginate to older lines
    FORWARD = "forward"  # paginate to newer lines (tail)


# ---------------------------------------------------------------------------
# Datatypes
# ---------------------------------------------------------------------------


@dataclass
class Cursor:
    """Opaque-to-the-caller pagination state.

    Connectors are free to put whatever they need in `token` (a CloudWatch
    nextToken, a timestamp string, base64-encoded compound state). The
    direction tells the connector whether the next page is earlier or later.
    """

    token: str
    direction: CursorDirection


@dataclass
class LogStream:
    """A sub-stream within a log source. Mirrors the CloudWatch log stream
    concept; for connectors that don't have sub-streams, return a single
    LogStream with `name='default'`."""

    name: str
    last_event_ts: Optional[datetime] = None
    first_event_ts: Optional[datetime] = None
    retention_in_days: Optional[int] = None


@dataclass
class LogFilters:
    """All filters the view layer is allowed to push down to a connector.

    Connectors that don't support a given filter are free to ignore it,
    but they should document which ones are honored.
    """

    # Time window — required at the view layer; default to "1h ago" upstream.
    since: datetime
    until: Optional[datetime] = None

    # Free-text search; connector decides whether to translate to a native
    # filter pattern or post-filter client-side.
    q: str = ""

    # Native filter syntax (e.g. CloudWatch filter pattern). When set, takes
    # precedence over `q` for the heavy lifting; `q` may still apply on top.
    pattern: str = ""

    # Level pills selected in the UI.
    levels: Set[LogLevel] = field(default_factory=set)

    # When non-empty: restrict to these sub-streams. Empty = group-wide.
    streams: Optional[List[str]] = None

    # The tenant whose lines should be returned. None = no tenant filter
    # (platform-admin cross-tenant view). Set by the API layer based on the
    # current app context. The connector translates this to its native form
    # — for CloudWatch verbose format that's a `[<app>:` prefix in the
    # filter pattern; for JSON it's `{ $.app_name = "<app>" }`.
    app_name: Optional[str] = None

    # Hard cap on lines per page; connector may return fewer.
    limit: int = 200


@dataclass
class LogLine:
    """One log entry. The connector is responsible for parsing whatever
    upstream format it sees into this shape."""

    ts: datetime
    message: str
    stream: str

    level: LogLevel = LogLevel.UNKNOWN
    structured: Optional[Dict[str, Any]] = None
    cursor_token: str = ""

    def to_dict(self) -> dict:
        return {
            "ts": self.ts.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "stream": self.stream,
            "structured": self.structured,
            "cursor_token": self.cursor_token,
        }


@dataclass
class LogPage:
    lines: List[LogLine]
    next_cursor: Optional[Cursor] = None

    @property
    def has_more(self) -> bool:
        return self.next_cursor is not None


@dataclass
class FacetSet:
    """What the UI needs to populate filter dropdowns."""

    levels: Set[LogLevel] = field(default_factory=set)
    streams: List[LogStream] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class LogConnector(Protocol):
    """The interface every concrete connector implements.

    Implementations should be cheap to construct and lazy in their resource
    acquisition (e.g. boto3 clients created on first call, not in __init__).
    """

    def list_streams(self, *, since: datetime) -> List[LogStream]:
        """Return sub-streams with events since `since`."""
        ...

    def fetch(self, *, filters: LogFilters, page: Optional[Cursor]) -> LogPage:
        """Return a bounded page of lines matching `filters`.

        `page=None` means "first page in the requested direction" — typically
        the most recent N lines for forward, oldest-of-window for backward.
        """
        ...

    def facets(self) -> FacetSet:
        """Cheap (cached) summary for filter UI."""
        ...

    def deep_link(self, *, filters: LogFilters) -> Optional[str]:
        """Native UI URL pre-filtered with the same filters, if the upstream
        has one. Connectors without a console UI return None."""
        ...
