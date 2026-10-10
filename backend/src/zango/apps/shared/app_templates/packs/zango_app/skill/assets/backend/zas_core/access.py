"""
Who may see and do what. Implements references/contracts.md sections 3-5.

Every table request and every detail fetch goes through scope_queryset(), so
row rules hold no matter which URL a user edits.
"""

import logging
import re
import uuid as _uuid

from . import expr as zx
from . import spec as zs

logger = logging.getLogger(__name__)

TABLE_ACTIONS = ("get_table_data", "export_table")


def role_name(request=None):
    if request is not None and getattr(request, "_zas_role_name", None):
        return request._zas_role_name
    try:
        from zango.core.utils import get_current_role
        role = get_current_role()
        return role.name if role else None
    except Exception:
        return None


def role_obj(name):
    from zango.apps.appauth.models import UserRoleModel
    return UserRoleModel.objects.filter(name=name).last()


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


def access_for(entity_code, role=None, request=None):
    """The access block for one role: {"actions": [...], "rows": ...} or None."""
    E = zs.entity(entity_code)
    role = role or role_name(request)
    acc = E.get("access_resolved") or {}
    a = acc.get(role)
    if not a or a.get("none"):
        return None
    return a


def can(entity_code, action, role=None, request=None):
    a = access_for(entity_code, role, request)
    return bool(a and action in a["actions"])


def bound_uuid(request, role=None):
    """object_uuid of the record bound to the current login for this role (app_user)."""
    user = getattr(request, "user", None)
    objs = getattr(user, "app_objects", None) or {}
    role = role or role_name(request)
    r = role_obj(role) if role else None
    if not r:
        return None
    return objs.get(str(r.id))


def user_record_resolver(request):
    """For expressions: current_user.<entity code> -> the bound record of that entity."""
    def resolve(attr):
        ents = zs.entities()
        E = ents.get(attr)
        if not E or not E.get("app_user"):
            return getattr(getattr(request, "user", None), attr, None)
        uid = bound_uuid(request, E["app_user"].get("role"))
        if not uid:
            return None
        return zs.model(attr).objects.filter(object_uuid=uid).first()
    return resolve


def expr_ctx(request, **extra):
    ctx = {"request": request, "user_record": user_record_resolver(request)}
    ctx.update(extra)
    return ctx


def scope_queryset(entity_code, qs, request, role=None):
    """Apply the role's `rows` rule. A role with no access gets nothing."""
    role = role or role_name(request)
    E = zs.entity(entity_code)
    if not E.get("access"):  # spec has no access block: open
        return qs
    a = access_for(entity_code, role)
    if a is None:
        return qs.none()
    rows = a.get("rows")
    if rows in (None, "all"):
        return qs
    if rows == "created_by_me":
        return qs.filter(created_by=getattr(request, "user", None))
    if isinstance(rows, dict):
        if "own" in rows:
            owner = _owner(E, rows["own"])
            uid = bound_uuid(request, (owner or {}).get("app_user", {}).get("role", role))
            if not uid:
                return qs.none()
            lookup = "object_uuid" if rows["own"] == "id" else rows["own"].replace(".", "__") + "__object_uuid"
            return qs.filter(**{lookup: uid})
        if "ast" in rows and rows["ast"]:
            return qs.filter(zx.to_q(rows["ast"], qs.model, expr_ctx(request)))
        if "text" in rows:
            fn = f"{entity_code}__rows__{_slug(role)}"
            f = zs.hook(E["module"], fn)
            if f is None:
                logger.error("zas: rows hook %s missing - returning no rows for %s", fn, role)
                return qs.none()
            return f(request, qs)
    logger.error("zas: unreadable rows rule %r on %s", rows, entity_code)
    return qs.none()


def in_scope(entity_code, obj, request):
    """True if the viewer's `rows` rule includes `obj`. The crud row-action and workflow
    endpoints load objects by uuid without any scoping, so every write path checks this."""
    if obj is None or getattr(obj, "pk", None) is None:
        return False
    if not zs.entity(entity_code).get("access"):
        return True
    return scope_queryset(entity_code, type(obj).objects.filter(pk=obj.pk), request).exists()


def _owner(E, own):
    if own == "id":
        return E
    cur = E
    for part in own.split("."):
        f = next((x for x in cur["fields"] if x["key"] == part), None)
        if not f or f["type"] != "link":
            return None
        cur = zs.entity(f["to"])
    return cur


def clean_uuid(value):
    if value is None:
        return None
    value = str(value).strip().strip("/")
    try:
        return str(_uuid.UUID(value))
    except ValueError:
        return False


def parent_filter(entity_code, qs, request):
    """Narrow to one parent when a 360 tab asks (?<hero>_uuid=). Table requests only."""
    E = zs.entity(entity_code)
    for param, info in (E.get("parents") or {}).items():
        raw = request.GET.get(param)
        if raw is None:
            continue
        uid = clean_uuid(raw)
        if not uid:
            return qs.none()
        qs = qs.filter(**{info["lookup"]: uid})
    return qs


def request_action(request):
    return request.GET.get("action") if request is not None else None
