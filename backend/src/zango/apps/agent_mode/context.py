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
    theme: dict = field(default_factory=dict)


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


def app_front_door(app_settings: dict) -> str:
    """The path the app's UI is actually served from.

    Zango serves the appbuilder React shell at ``/app/`` — the generated
    ``app.html`` hardcodes ``data-base-path="/app/"`` and an initializer at
    ``/app/initializer/``. That path is split across two files, which is easy
    to get wrong: ``settings.json`` mounts the ``app`` module, and the module's
    own ``urls.py`` puts the view under it. Both real layouts land on ``/app/``:

        settings.json ``^``      + urls.py ``^app/``  ->  /app/
        settings.json ``^app/``  + urls.py ``/``      ->  /app/

    So the front door is the module's mount point with ``app/`` underneath it,
    unless the mount already ends there.
    """
    routes = (app_settings or {}).get("app_routes") or []
    routes = [r for r in routes if isinstance(r, dict)]
    chosen = next((r for r in routes if r.get("module") == "app"), None)
    if chosen is None:
        chosen = routes[0] if routes else None

    mount = ""
    if chosen is not None:
        mount = str(chosen.get("re_path") or "").strip().lstrip("^").rstrip("$")
    mount = mount.strip("/")

    if not mount:
        return "/app/"
    if mount.split("/")[-1] == "app":
        return f"/{mount}/"
    return f"/{mount}/app/"


def app_access(tenant, *, request=None, app_settings=None) -> dict:
    """Where a person can actually open this app.

    Tenants are resolved strictly by hostname, so without a domain row there
    is no reachable URL — say so rather than inventing one. Scheme and port
    are carried from the caller's own request, which is what makes the link
    work on a dev server running off the default port.
    """
    domain = ""
    try:
        domains = list(tenant.domains.all())
        primary = next((d for d in domains if getattr(d, "is_primary", False)), None)
        chosen = primary or (domains[0] if domains else None)
        if chosen is not None:
            domain = chosen.domain or ""
    except Exception:  # noqa: BLE001
        domain = ""

    if not domain:
        return {"domain": "", "url": "", "path": "/"}

    if app_settings is None:
        app_settings = _read_json(
            os.path.join(workspace_path_for(tenant.name), "settings.json")
        )
    path = app_front_door(app_settings)

    scheme, port = "https", ""
    if request is not None:
        try:
            scheme = "https" if request.is_secure() else "http"
            host = request.get_host()
            if ":" in host:
                port = ":" + host.rsplit(":", 1)[1]
        except Exception:  # noqa: BLE001
            scheme, port = "https", ""

    return {
        "domain": domain,
        "url": f"{scheme}://{domain}{port}{path}",
        "path": path,
    }


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
        # Must match what the Bash guard actually permits, which resolves from
        # the platform settings row (env is only its fallback). Reading the
        # Django setting directly here skipped that row, so an operator who
        # enabled "Allow custom React builds" in the UI still got a run context
        # saying Node was unavailable: the guard allowed npm while the prompt
        # told the agent not to build, and the agent obeyed the prompt.
        from .config import frontend_build_enabled

        ctx.frontend_build_allowed = frontend_build_enabled()
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

    try:
        # The app's own active theme. The agent needs these values literally
        # for the login page: it renders before authentication, so
        # `useAppContext()` is not available there and there is no runtime
        # source for the palette. Without this the agent hard-codes a hex it
        # guessed or copied, which then stops matching the moment the app is
        # re-themed.
        from zango.apps.shared.tenancy.models import ThemesModel
        from zango.apps.shared.tenancy.utils import DEFAULT_THEME_CONFIG

        theme = (
            ThemesModel.objects.filter(tenant=tenant, is_active=True)
            .values_list("config", flat=True)
            .first()
        )
        ctx.theme = theme or DEFAULT_THEME_CONFIG
    except Exception:  # noqa: BLE001
        pass

    return ctx
