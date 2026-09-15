"""Mint the AppBuilder configuration credential for a run.

Registering routes and menus is not optional polish: a CRUD view with no
AppBuilder route never appears in the app's navigation, so the feature the
agent just built is unreachable. The interactive skill calls this step
mandatory for every new page.

The credential is a signed platform-user id, consumed by
``zango.apps.dynamic_models.permissions.get_platform_user``:

    user_id = signing.loads(token, max_age=1800)

Three properties make it safe to hand to an agent, and they are why this is
back in scope after the rest of Capability 3 was cut:

* **No secret is involved.** It is minted with ``signing.dumps(user_id)``;
  there is no password, no session and no cookie jar.
* **It is app-scoped, not platform-scoped.** It authenticates against the
  app's own views via ``is_platform_user``. It does **not** authenticate the
  ``/api/v1/apps/...`` platform admin API, so it cannot create or delete
  apps, users or secrets.
* **It expires in 30 minutes**, enforced framework-side.

That TTL is shorter than the run ceiling, so a long run can outlive its
token — see ``TOKEN_MAX_AGE_SECONDS``.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass


logger = logging.getLogger("zango.agent_mode")

# Fixed framework-side in dynamic_models/permissions.py.
TOKEN_MAX_AGE_SECONDS = 1800


@dataclass
class AppBuilderAccess:
    config_base_url: str = ""
    token: str = ""
    available: bool = False
    reason: str = ""


def _primary_domain(tenant) -> str:
    try:
        domains = list(tenant.domains.all())
    except Exception:  # noqa: BLE001
        return ""
    primary = next((d for d in domains if getattr(d, "is_primary", False)), None)
    chosen = primary or (domains[0] if domains else None)
    return chosen.domain if chosen else ""


def _appbuilder_route(workspace_settings: dict) -> str:
    for route in workspace_settings.get("package_routes") or []:
        if route.get("package") == "appbuilder":
            return (route.get("re_path") or "").lstrip("^")
    return ""


def build_access(
    tenant, workspace_settings: dict, scheme: str = "http"
) -> AppBuilderAccess:
    """Mint the config URL + token, or explain why it is unavailable.

    Mirrors ``package_utils.get_package_configuration_url``, but builds the
    URL from the domain directly — that helper needs a ``request``, which a
    Celery task does not have.
    """
    from django.core import signing

    from zango.apps.shared.platformauth.models import PlatformUserModel

    route = _appbuilder_route(workspace_settings)
    if not route:
        return AppBuilderAccess(
            reason="the appbuilder package is not registered in package_routes"
        )

    domain = _primary_domain(tenant)
    if not domain:
        return AppBuilderAccess(
            reason=(
                "this app has no domain configured, so its AppBuilder config "
                "API has no address. Set one in App Settings."
            )
        )

    user = (
        PlatformUserModel.objects.filter(is_superadmin=True, is_active=True)
        .order_by("id")
        .first()
    )
    if user is None:
        return AppBuilderAccess(reason="no active platform superadmin to sign for")

    try:
        token = signing.dumps(user.id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent_mode: could not mint appbuilder token")
        return AppBuilderAccess(reason=f"{type(exc).__name__}: {exc}")

    return AppBuilderAccess(
        config_base_url=f"{scheme}://{domain}/{route}configure",
        token=token,
        available=True,
    )
