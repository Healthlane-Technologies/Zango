"""Facts about the app, gathered for the run prompt.

Read straight off disk and out of the tenant schema. Deliberately does NOT
construct a ``Workspace`` or import any workspace module: the runner must
stay clean of pluginbase state (see the plan's "Stale modules" section), and
a run must still be possible when the app's own code is currently broken —
which is exactly when you would ask an agent to fix it.
"""

from __future__ import annotations

import json
import os

from dataclasses import dataclass, field


@dataclass
class AppContext:
    app_name: str = ""
    workspace_path: str = ""
    schema_name: str = ""
    primary_domain: str = ""
    packages: list = field(default_factory=list)
    modules: list = field(default_factory=list)
    roles: list = field(default_factory=list)
    app_settings_version: str = ""
    workspace_exists: bool = False
    appbuilder_config_url: str = ""
    appbuilder_token: str = ""
    appbuilder_reason: str = ""
    frontend_build_allowed: bool = False
    frontend_exists: bool = False


def _read_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:  # noqa: BLE001 - a broken workspace must not block a run
        return {}


def workspaces_root() -> str:
    from django.conf import settings

    return os.path.join(str(settings.BASE_DIR), "workspaces")


def workspace_path_for(tenant_name: str) -> str:
    return os.path.join(workspaces_root(), tenant_name)


def build_app_context(tenant) -> AppContext:
    """Collect the run context. Never raises."""
    path = workspace_path_for(tenant.name)
    ctx = AppContext(
        app_name=tenant.name,
        workspace_path=path,
        schema_name=getattr(tenant, "schema_name", "") or "",
        workspace_exists=os.path.isdir(path),
    )

    try:
        import shutil

        from django.conf import settings as dj

        ctx.frontend_build_allowed = bool(
            getattr(dj, "AGENT_MODE_ALLOW_FRONTEND_BUILD", False)
        ) and bool(shutil.which("node"))
        ctx.frontend_exists = os.path.isdir(os.path.join(path, "frontend"))
    except Exception:  # noqa: BLE001
        pass

    app_settings = _read_json(os.path.join(path, "settings.json"))
    ctx.app_settings_version = str(app_settings.get("version") or "")
    ctx.modules = [
        {"name": m.get("name", ""), "path": m.get("path", "")}
        for m in (app_settings.get("modules") or [])
        if isinstance(m, dict)
    ]

    manifest = _read_json(os.path.join(path, "manifest.json"))
    for pkg in manifest.get("packages") or []:
        if isinstance(pkg, dict):
            ctx.packages.append(
                {"name": pkg.get("name", ""), "version": str(pkg.get("version", ""))}
            )

    try:
        domains = list(tenant.domains.all())
        primary = next((d for d in domains if getattr(d, "is_primary", False)), None)
        chosen = primary or (domains[0] if domains else None)
        if chosen is not None:
            ctx.primary_domain = chosen.domain
    except Exception:  # noqa: BLE001
        pass

    try:
        from .appbuilder import build_access

        access = build_access(tenant, app_settings)
        ctx.appbuilder_config_url = access.config_base_url
        ctx.appbuilder_token = access.token
        ctx.appbuilder_reason = access.reason
    except Exception:  # noqa: BLE001
        pass

    try:
        from zango.apps.appauth.models import UserRoleModel

        ctx.roles = list(
            UserRoleModel.objects.filter(is_active=True).values_list("name", flat=True)
        )
    except Exception:  # noqa: BLE001
        pass

    return ctx
