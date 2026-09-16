"""Is Agent Mode usable right now, and if not, why?

Drives the App Settings CTA: the panel hides it rather than offering a button
that leads to a run which cannot start. Every check is cheap, read-only and
degrades to a value rather than an exception — a broker hiccup must not 500
the settings page.
"""

from __future__ import annotations

import importlib.util
import os
import shutil


def _sdk_installed() -> bool:
    try:
        return importlib.util.find_spec("claude_agent_sdk") is not None
    except Exception:  # noqa: BLE001
        return False


def _cli_path() -> str:
    """The Claude Code binary the SDK would use: bundled first, then PATH."""
    from django.conf import settings as dj

    override = getattr(dj, "AGENT_MODE_CLAUDE_BIN", "")
    if override and os.access(override, os.X_OK):
        return override
    try:
        import claude_agent_sdk
        from pathlib import Path

        bundled = Path(claude_agent_sdk.__file__).parent / "_bundled" / "claude"
        if bundled.is_file() and os.access(bundled, os.X_OK):
            return str(bundled)
    except Exception:  # noqa: BLE001
        pass
    return shutil.which("claude") or ""


def _inspect_queues(timeout: float) -> dict | None:
    try:
        from zango.config.celery import app as celery_app

        return celery_app.control.inspect(timeout=timeout).active_queues() or {}
    except Exception:  # noqa: BLE001
        return None


def _worker_online(queue: str) -> tuple[bool | None, list]:
    """Is a worker consuming `queue`?  (state, node names seen).

    None means the broker could not be reached — unknown, not offline.

    Retried once because replies are keyed by node name: two workers started
    without distinct ``-n`` share a name, one reply overwrites the other, and
    the answer flaps between polls. The retry damps that; the real fix is a
    unique ``-n``, which `worker_nodes` makes diagnosable.
    """
    nodes: list = []
    for timeout in (0.6, 1.2):
        replies = _inspect_queues(timeout)
        if replies is None:
            return None, nodes
        nodes = sorted(replies)
        for queues in replies.values():
            for entry in queues or []:
                if entry.get("name") == queue:
                    return True, nodes
        if not replies:
            return None, nodes
    return False, nodes


def probe(tenant=None) -> dict:
    """Report whether a run could start, with machine-readable reasons."""
    from django.conf import settings as dj

    from .config import load_config
    from .context import workspace_path_for
    from .credentials import resolve_credentials

    cfg = load_config()
    creds = resolve_credentials()
    cli = _cli_path()
    queue = getattr(dj, "AGENT_MODE_QUEUE", "agent_mode") or "celery"
    worker_state, worker_nodes = _worker_online(queue)
    home = getattr(dj, "AGENT_MODE_HOME", "") or ""

    workspace = workspace_path_for(tenant.name) if tenant is not None else ""
    checks = {
        "feature_enabled": cfg.enabled,
        "sdk_installed": _sdk_installed(),
        "cli_available": bool(cli),
        "credentials": creds.is_usable,
        "credential_source": creds.source or None,
        "skill_plugin_present": _skill_plugin_present(),
        "workspace_exists": bool(workspace) and os.path.isdir(workspace),
        "workspace_writable": bool(workspace) and os.access(workspace, os.W_OK),
        "home_writable": _home_writable(home),
        "worker_online": worker_state,
        "worker_nodes": worker_nodes,
        "node_available": bool(shutil.which("node")),
        "tenant_status": getattr(tenant, "status", None) if tenant else None,
        "env": getattr(dj, "ENV", ""),
    }

    reasons = []
    if not checks["feature_enabled"]:
        reasons.append("feature_disabled")
    if not checks["sdk_installed"]:
        reasons.append("sdk_not_installed")
    if not checks["cli_available"]:
        reasons.append("cli_not_found")
    if not checks["credentials"]:
        reasons.append("no_credentials")
    if not checks["skill_plugin_present"]:
        reasons.append("skill_plugin_missing")
    if not checks["workspace_exists"]:
        reasons.append("workspace_missing")
    if checks["tenant_status"] == "suspended":
        reasons.append("app_suspended")
    # worker_online is None when the broker is unreachable; only False is a
    # definite problem, and it is a warning rather than a hard block.
    if checks["worker_online"] is False:
        reasons.append("no_worker")

    return {
        "available": not reasons,
        "reasons": reasons,
        "checks": checks,
        "config": {
            "model": cfg.model or None,
            "effort": cfg.effort or None,
            "max_run_seconds": cfg.max_run_seconds,
            "max_turns": cfg.max_turns,
            "max_budget_usd": cfg.max_budget_usd,
            "analyst_model": cfg.analyst_model or None,
            "analyst_budget_usd": cfg.analyst_budget_usd,
            "permission_mode": getattr(dj, "AGENT_MODE_PERMISSION_MODE", ""),
            "queue": queue,
            "source": cfg.source,
        },
    }


def _skill_plugin_present() -> bool:
    from pathlib import Path

    from .options import SKILL_PLUGIN_DIR

    return (Path(SKILL_PLUGIN_DIR) / ".claude-plugin" / "plugin.json").is_file()


def _home_writable(home: str) -> bool:
    if not home:
        return False
    try:
        os.makedirs(home, exist_ok=True)
        return os.access(home, os.W_OK)
    except Exception:  # noqa: BLE001
        return False
