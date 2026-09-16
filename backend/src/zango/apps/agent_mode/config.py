"""Resolved Agent Mode configuration.

One place that answers "what settings apply right now", so the platform
settings UI and the runners cannot disagree. Precedence is DB row first, then
Django settings/env — an operator changing a value in the App Panel must not
need a redeploy, and a value they did not set must fall back rather than
becoming empty.

Must be read on the public schema (AgentModeSettings lives there), which in
practice means before ``connection.set_tenant``.
"""

from __future__ import annotations

import shutil

from dataclasses import dataclass


@dataclass
class AgentModeConfig:
    enabled: bool = False
    ensure_packages: bool = True
    allow_frontend_build: bool = False

    # Build agent
    model: str = ""
    effort: str = ""
    max_run_seconds: int = 1800
    max_turns: int | None = None
    max_budget_usd: float | None = None

    # Analyst agent
    analyst_model: str = ""
    analyst_effort: str = ""
    analyst_max_turns: int | None = None
    analyst_budget_usd: float | None = None

    monthly_budget_usd: float | None = None
    source: str = "env"


def _first(*values):
    """First value that was actually set."""
    for value in values:
        if value not in (None, "", 0):
            return value
    return None


def load_config() -> AgentModeConfig:
    """Resolve settings: the platform row wins, env fills the gaps."""
    from django.conf import settings as dj

    cfg = AgentModeConfig(
        enabled=bool(getattr(dj, "AGENT_MODE_ENABLED", False)),
        ensure_packages=bool(getattr(dj, "AGENT_MODE_ENSURE_PACKAGES", True)),
        allow_frontend_build=bool(
            getattr(dj, "AGENT_MODE_ALLOW_FRONTEND_BUILD", False)
        ),
        model=getattr(dj, "AGENT_MODE_MODEL", "") or "",
        effort=getattr(dj, "AGENT_MODE_EFFORT", "") or "",
        max_run_seconds=int(getattr(dj, "AGENT_MODE_MAX_RUN_SECONDS", 1800)),
        max_turns=getattr(dj, "AGENT_MODE_MAX_TURNS", 0) or None,
        max_budget_usd=getattr(dj, "AGENT_MODE_MAX_BUDGET_USD", None),
        analyst_model=getattr(dj, "AGENT_MODE_MODEL", "") or "",
        analyst_max_turns=getattr(dj, "AGENT_MODE_ANALYST_MAX_TURNS", 0) or None,
        analyst_budget_usd=getattr(dj, "AGENT_MODE_ANALYST_BUDGET_USD", None),
    )

    try:
        from zango.apps.shared.agent_mode.models import AgentModeSettings

        row = AgentModeSettings.load()
    except Exception:  # noqa: BLE001 - env-only is a valid state
        row = None

    if row is None:
        return cfg

    cfg.source = "platform_settings"
    # is_enabled is a deliberate operator choice, so it overrides env outright
    # rather than only when "set" — False here must be able to turn it off.
    cfg.enabled = bool(row.is_enabled)
    cfg.ensure_packages = bool(row.ensure_packages)
    cfg.allow_frontend_build = bool(row.allow_frontend_build)

    cfg.model = row.default_model or cfg.model
    cfg.effort = row.default_effort or cfg.effort
    cfg.max_run_seconds = _first(row.max_run_seconds, cfg.max_run_seconds) or 1800
    cfg.max_turns = _first(row.max_turns, cfg.max_turns)
    cfg.max_budget_usd = _first(row.max_budget_usd, cfg.max_budget_usd)

    # The analyst falls back to the build model when unset, so a single-model
    # setup stays simple.
    cfg.analyst_model = row.analyst_model or cfg.model
    cfg.analyst_effort = row.analyst_effort or ""
    cfg.analyst_max_turns = _first(row.analyst_max_turns, cfg.analyst_max_turns)
    cfg.analyst_budget_usd = _first(row.analyst_budget_usd, cfg.analyst_budget_usd)

    cfg.monthly_budget_usd = row.monthly_budget_usd
    return cfg


def node_available() -> bool:
    return bool(shutil.which("node"))


def frontend_build_enabled() -> bool:
    """Opted in AND Node actually present — enabling one without the other
    only produces confusing mid-run failures."""
    return load_config().allow_frontend_build and node_available()
