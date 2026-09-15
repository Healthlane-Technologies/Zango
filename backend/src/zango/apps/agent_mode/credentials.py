"""Platform Anthropic credential resolution and secret redaction.

The key travels exactly one route: ``resolve_credentials()`` ->
``ClaudeAgentOptions.env["ANTHROPIC_API_KEY"]``. It is never placed in a
Celery payload, never stored on an AgentRun row, and never returned by an
API path (see ``AgentModeSettings.masked_config``).

``redact()`` is the last line of defence: every event message and every
string leaf of an event payload passes through it before insert, so an
agent that echoes its own environment cannot leak the key into a
transcript the panel will happily render.
"""

from __future__ import annotations

import re

from dataclasses import dataclass, field


REDACTED = "***REDACTED***"

# Shape-based fallbacks, for keys we were never told about.
_SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"sk-[A-Za-z0-9_\-]{32,}"),
]

# Exact secrets registered for this process (the live key).
_REGISTERED: set[str] = set()

# Anything shorter is too collision-prone to blind-replace across all output.
_MIN_REGISTER_LEN = 12


@dataclass(frozen=True)
class AgentCredentials:
    """Resolved credentials for one run. Never logged, never serialized."""

    provider: str = "anthropic"
    api_key: str = ""
    extra_env: dict = field(default_factory=dict)
    # "platform_settings" | "env" | "" — safe to surface in the availability probe.
    source: str = ""

    @property
    def is_usable(self) -> bool:
        return bool(self.api_key)


def register_secret(value: str) -> None:
    """Register an exact secret for redaction. Idempotent."""
    if value and len(value) >= _MIN_REGISTER_LEN:
        _REGISTERED.add(value)


def clear_registered_secrets() -> None:
    """Test hook — drop registered secrets."""
    _REGISTERED.clear()


def redact(text):
    """Replace registered secrets and secret-shaped tokens. Never raises."""
    if not isinstance(text, str) or not text:
        return text
    try:
        # Longest first, so a prefix of another secret can't leave a tail behind.
        for secret in sorted(_REGISTERED, key=len, reverse=True):
            if secret in text:
                text = text.replace(secret, REDACTED)
        for pattern in _SECRET_PATTERNS:
            text = pattern.sub(REDACTED, text)
    except Exception:  # noqa: BLE001 - redaction must never break a run
        return REDACTED
    return text


def redact_obj(obj, _depth: int = 0):
    """Recursively redact string leaves of a JSON-ish structure."""
    if _depth > 12:
        return obj
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: redact_obj(v, _depth + 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact_obj(v, _depth + 1) for v in obj]
    return obj


def resolve_credentials() -> AgentCredentials:
    """Resolve the platform Anthropic credential.

    Precedence: the encrypted public-schema AgentModeSettings row (so a
    platform admin can rotate without a redeploy), then Django settings /
    environment as the bootstrap path.

    Must be called BEFORE ``connection.set_tenant(...)`` — AgentModeSettings
    lives in the public schema.
    """
    from django.conf import settings

    try:
        from zango.apps.shared.agent_mode.models import AgentModeSettings

        row = AgentModeSettings.load()
        if row is not None:
            config = row.get_config() or {}
            api_key = (config.get("api_key") or "").strip()
            if api_key:
                register_secret(api_key)
                return AgentCredentials(
                    provider=row.provider or "anthropic",
                    api_key=api_key,
                    extra_env={
                        k: str(v) for k, v in (config.get("extra_env") or {}).items()
                    },
                    source="platform_settings",
                )
    except Exception:  # noqa: BLE001 - fall through to env
        pass

    api_key = (getattr(settings, "ANTHROPIC_API_KEY", "") or "").strip()
    if api_key:
        register_secret(api_key)
        return AgentCredentials(api_key=api_key, source="env")

    return AgentCredentials()
