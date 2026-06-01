"""CloudWatch Logs connector — v1.

Reads from a single CloudWatch log group via boto3. Handles 1..N streams
under the group transparently for the default browse path
(`FilterLogEvents` fans out across all of them). Streams can be explicitly
listed via `list_streams` for the stream-picker UI.

Caching:
- boto3 client is created lazily and memoized per (region, role_arn).
- `facets()` results are cached for 60s.
- `list_streams()` results are cached for 30s.

Retries:
- ThrottlingException + ServiceUnavailable get three retries with
  exponential jitter (200 ms / 600 ms / 1.4 s).

Tenant filtering:
- The connector translates `filters.app_name` into the CloudWatch filter
  pattern based on the config's `format`:
    * "verbose" → prepend `[<app>:` literal to the pattern (matches the
      bracketed prefix added by the existing TenantContextFilter)
    * "json"    → add `{ $.app_name = "<app>" }` (future)
    * "plain"   → no-op (cannot filter; documented gap)
"""

from __future__ import annotations

import logging
import random
import re
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from zango.apps.platform_logs.connectors.base import (
    Cursor,
    CursorDirection,
    FacetSet,
    LogFilters,
    LogLevel,
    LogLine,
    LogPage,
    LogStream,
)
from zango.apps.platform_logs.connectors.exceptions import (
    ConnectorConfigError,
    ConnectorError,
    ConnectorNotFound,
    ConnectorThrottled,
    ConnectorUnauthorized,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CloudWatchConfig:
    region: str
    log_group_name: str
    stream_prefix: Optional[str] = None
    fmt: str = "plain"  # "plain" | "verbose" | "json"
    role_arn: Optional[str] = None

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "CloudWatchConfig":
        required = ("region", "log_group_name")
        missing = [k for k in required if not raw.get(k)]
        if missing:
            raise ConnectorConfigError(
                f"CloudWatch connector config missing required keys: {missing}"
            )
        fmt = raw.get("format", "plain")
        if fmt not in {"plain", "verbose", "json"}:
            raise ConnectorConfigError(
                f"Unknown CloudWatch format '{fmt}'. Use 'plain', 'verbose', or 'json'."
            )
        return cls(
            region=raw["region"],
            log_group_name=raw["log_group_name"],
            stream_prefix=raw.get("stream_prefix") or None,
            fmt=fmt,
            role_arn=raw.get("role_arn") or None,
        )


# ---------------------------------------------------------------------------
# Client cache — one boto3 client per (region, role_arn)
# ---------------------------------------------------------------------------


_client_cache: Dict[Tuple[str, Optional[str]], Any] = {}
_client_lock = Lock()


def _get_client(region: str, role_arn: Optional[str]):
    key = (region, role_arn)
    client = _client_cache.get(key)
    if client is not None:
        return client

    with _client_lock:
        client = _client_cache.get(key)
        if client is not None:
            return client

        boto_cfg = BotoConfig(
            retries={"max_attempts": 1, "mode": "standard"},  # we do our own
            connect_timeout=4,
            read_timeout=12,
        )

        if role_arn:
            sts = boto3.client("sts", config=boto_cfg)
            assumed = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"zango-platform-logs-{int(time.time())}",
                DurationSeconds=3600,
            )["Credentials"]
            client = boto3.client(
                "logs",
                region_name=region,
                aws_access_key_id=assumed["AccessKeyId"],
                aws_secret_access_key=assumed["SecretAccessKey"],
                aws_session_token=assumed["SessionToken"],
                config=boto_cfg,
            )
        else:
            client = boto3.client("logs", region_name=region, config=boto_cfg)

        _client_cache[key] = client
        return client


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------


_RETRYABLE_CODES = {"ThrottlingException", "ServiceUnavailable", "TooManyRequestsException"}


def _with_retry(fn, *args, **kwargs):
    """Three attempts on retryable codes, exponential jitter (~200/600/1400ms).

    Re-raises wrapped ConnectorThrottled when the final attempt also throttles
    so the API layer can surface a Retry-After.
    """
    last_exc: Optional[ClientError] = None
    backoff = (0.2, 0.6, 1.4)
    for attempt, sleep in enumerate(backoff, start=1):
        try:
            return fn(*args, **kwargs)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code not in _RETRYABLE_CODES:
                raise _translate(exc) from exc
            last_exc = exc
            logger.warning(
                "platform_logs: CloudWatch %s (attempt %d/%d), retrying in %.2fs",
                code, attempt, len(backoff), sleep,
            )
            time.sleep(sleep + random.uniform(0, sleep * 0.25))
    # Out of attempts
    assert last_exc is not None
    raise ConnectorThrottled(
        f"CloudWatch throttled after {len(backoff)} attempts",
        retry_after_seconds=2.0,
    ) from last_exc


def _translate(exc: ClientError) -> Exception:
    code = exc.response.get("Error", {}).get("Code", "")
    msg = exc.response.get("Error", {}).get("Message", str(exc))
    if code == "ResourceNotFoundException":
        return ConnectorNotFound(msg)
    if code in {"AccessDeniedException", "UnauthorizedClientError"}:
        return ConnectorUnauthorized(msg)
    return ConnectorError(f"{code}: {msg}")


# ---------------------------------------------------------------------------
# Level parsing — plain-text & verbose Zango format
# ---------------------------------------------------------------------------

# Celery default: "[2026-06-01 08:06:00,405: INFO/MainProcess] …"
_CELERY_RE = re.compile(
    r"\[\d{4}-\d{2}-\d{2}[^\]]+:\s*(?P<lvl>DEBUG|INFO|WARNING|ERROR|CRITICAL)/"
)

# Zango verbose: "[<app>:<domain>][<asctime>] LEVEL [path:func:line] msg"
_VERBOSE_RE = re.compile(
    r"\[[^\]]+\]\[[^\]]+\]\s*(?P<lvl>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s"
)

# Stdlib default: "INFO 2026-06-01 08:06:00 mod: msg"
_STDLIB_RE = re.compile(r"^(?P<lvl>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s")


def _parse_level(message: str) -> LogLevel:
    for pat in (_VERBOSE_RE, _CELERY_RE, _STDLIB_RE):
        m = pat.search(message)
        if m:
            return LogLevel(m.group("lvl").lower())
    return LogLevel.UNKNOWN


# ---------------------------------------------------------------------------
# Connector
# ---------------------------------------------------------------------------


class CloudWatchConnector:
    """Read-only CloudWatch Logs connector. Implements LogConnector."""

    def __init__(self, raw_config: Dict[str, Any]):
        self.cfg = CloudWatchConfig.from_dict(raw_config)
        self._streams_cache: Tuple[float, List[LogStream]] = (0.0, [])
        self._facets_cache: Tuple[float, FacetSet] = (0.0, FacetSet())

    # ---- streams ------------------------------------------------------

    def list_streams(self, *, since: datetime) -> List[LogStream]:
        now = time.monotonic()
        cached_at, cached_streams = self._streams_cache
        if cached_streams and (now - cached_at) < 30:
            return cached_streams

        client = _get_client(self.cfg.region, self.cfg.role_arn)
        since_ms = int(since.timestamp() * 1000)
        kwargs: Dict[str, Any] = {
            "logGroupName": self.cfg.log_group_name,
            "orderBy": "LastEventTime",
            "descending": True,
            "limit": 50,
        }
        if self.cfg.stream_prefix:
            kwargs["logStreamNamePrefix"] = self.cfg.stream_prefix

        out: List[LogStream] = []
        token: Optional[str] = None
        for _ in range(5):  # at most 5 pages = 250 streams
            if token:
                kwargs["nextToken"] = token
            resp = _with_retry(client.describe_log_streams, **kwargs)
            for s in resp.get("logStreams", []):
                last_ts = s.get("lastEventTimestamp")
                if last_ts is None or last_ts < since_ms:
                    continue  # ordering is DESC by LastEventTime, but skip strays
                out.append(
                    LogStream(
                        name=s["logStreamName"],
                        last_event_ts=_ms_to_dt(last_ts),
                        first_event_ts=_ms_to_dt(s.get("firstEventTimestamp")),
                    )
                )
            token = resp.get("nextToken")
            if not token:
                break
            # Optimization: when descending by LastEventTime, once we cross
            # the `since` cutoff the rest is older — stop paging.
            tail = resp.get("logStreams", [])
            if tail and (tail[-1].get("lastEventTimestamp") or 0) < since_ms:
                break

        self._streams_cache = (now, out)
        return out

    # ---- fetch --------------------------------------------------------

    def fetch(
        self,
        *,
        filters: LogFilters,
        page: Optional[Cursor],
    ) -> LogPage:
        client = _get_client(self.cfg.region, self.cfg.role_arn)

        # Time bounds — page direction overrides `until`/`since` for tail.
        start_ms = int(filters.since.timestamp() * 1000)
        end_ms = int(filters.until.timestamp() * 1000) if filters.until else None

        if page is not None:
            if page.direction == CursorDirection.FORWARD:
                # Tail — advance past whatever we last saw.
                start_ms = max(start_ms, int(page.token))
                end_ms = None
            else:
                # Backward — cap end at the oldest we'd previously fetched.
                end_ms = int(page.token)

        kwargs: Dict[str, Any] = {
            "logGroupName": self.cfg.log_group_name,
            "startTime": start_ms,
            "limit": max(1, min(filters.limit, 500)),
        }
        if end_ms is not None:
            kwargs["endTime"] = end_ms
        if filters.streams:
            kwargs["logStreamNames"] = filters.streams[:100]
        elif self.cfg.stream_prefix:
            kwargs["logStreamNamePrefix"] = self.cfg.stream_prefix

        pattern = self._build_pattern(filters)
        if pattern:
            kwargs["filterPattern"] = pattern

        resp = _with_retry(client.filter_log_events, **kwargs)
        events = resp.get("events", [])

        lines: List[LogLine] = []
        newest_ms = start_ms
        oldest_ms: Optional[int] = None
        for ev in events:
            ts_ms = ev["timestamp"]
            newest_ms = max(newest_ms, ts_ms)
            oldest_ms = ts_ms if oldest_ms is None else min(oldest_ms, ts_ms)
            msg = ev["message"]
            lines.append(
                LogLine(
                    ts=_ms_to_dt(ts_ms),
                    message=msg.rstrip("\n"),
                    stream=ev.get("logStreamName", ""),
                    level=_parse_level(msg),
                    cursor_token=ev.get("eventId", ""),
                )
            )

        # Build next cursor in the direction the caller is paging.
        next_cursor: Optional[Cursor] = None
        if page is not None and page.direction == CursorDirection.BACKWARD:
            if oldest_ms and resp.get("events"):
                next_cursor = Cursor(token=str(oldest_ms - 1), direction=CursorDirection.BACKWARD)
        else:
            # Forward / first page
            if lines:
                next_cursor = Cursor(token=str(newest_ms + 1), direction=CursorDirection.FORWARD)

        return LogPage(lines=lines, next_cursor=next_cursor)

    # ---- facets -------------------------------------------------------

    def facets(self) -> FacetSet:
        now = time.monotonic()
        cached_at, cached_facets = self._facets_cache
        if (now - cached_at) < 60 and (cached_facets.levels or cached_facets.streams):
            return cached_facets

        # Streams in the last 24h.
        streams = self.list_streams(since=datetime.now(timezone.utc) - timedelta(hours=24))

        # Sample 200 recent lines to populate levels.
        sample = self.fetch(
            filters=LogFilters(
                since=datetime.now(timezone.utc) - timedelta(hours=1),
                limit=200,
            ),
            page=None,
        )
        levels = {ln.level for ln in sample.lines if ln.level != LogLevel.UNKNOWN}

        out = FacetSet(levels=levels, streams=streams)
        self._facets_cache = (now, out)
        return out

    # ---- deep link ----------------------------------------------------

    def deep_link(self, *, filters: LogFilters) -> Optional[str]:
        # Logs Insights URL format. Reference:
        # https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html
        query_parts = ["fields @timestamp, @message", "sort @timestamp desc", "limit 200"]

        clauses: List[str] = []
        if filters.app_name and self.cfg.fmt == "verbose":
            clauses.append(f'@message like /\\[{re.escape(filters.app_name)}:/')
        elif filters.app_name and self.cfg.fmt == "json":
            clauses.append(f'app_name = "{filters.app_name}"')
        if filters.levels:
            level_names = sorted(lv.value.upper() for lv in filters.levels)
            clauses.append(f"@message like /{ '|'.join(level_names) }/")
        for clause in clauses:
            query_parts.insert(-2, f"filter {clause}")

        query = "\n".join(query_parts)

        # Time window — Insights wants epoch seconds.
        end = filters.until or datetime.now(timezone.utc)
        params = {
            "queryDetail": (
                "~(end~"
                f"'{end.isoformat()}"
                "~start~"
                f"'{filters.since.isoformat()}"
                "~timeType~'ABSOLUTE~unit~'seconds"
                "~editorString~'"
                + urllib.parse.quote(query, safe="")
                + "~source~(~'"
                + urllib.parse.quote(self.cfg.log_group_name, safe="")
                + "))"
            ),
        }
        qs = urllib.parse.urlencode(params)
        return (
            f"https://{self.cfg.region}.console.aws.amazon.com/cloudwatch/home"
            f"?region={self.cfg.region}#logsV2:logs-insights${qs}"
        )

    # ---- helpers ------------------------------------------------------

    def _build_pattern(self, filters: LogFilters) -> str:
        """Build the FilterLogEvents pattern combining user input + tenant scope."""
        parts: List[str] = []

        if filters.pattern:
            parts.append(filters.pattern)

        if filters.q:
            # Free-text: wrap in quotes for CloudWatch literal match.
            parts.append(f'"{filters.q}"')

        if filters.app_name and self.cfg.fmt == "verbose":
            parts.append(f'"[{filters.app_name}:"')
        elif filters.app_name and self.cfg.fmt == "json":
            parts.append(f'{{ $.app_name = "{filters.app_name}" }}')
        # plain format: no app_name filter possible (documented gap)

        return " ".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ms_to_dt(ms: Optional[int]) -> Optional[datetime]:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
