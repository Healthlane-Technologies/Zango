"""
Login provisioning for entities with an `app_user` block.

A record that owns a login gets an AppUserModel with the spec's role, mapped by
app_objects[str(role.id)] = str(record.object_uuid). That mapping is what
`rows: {own: ...}` scoping reads (access.bound_uuid). Adapted from the
psp-app-generator UserManager: idempotent, reuses an existing user on the same
email/mobile, and never raises (a login problem must not roll back the record).

Wiring (automatic, no generated code needed):
  create_on: create        -> ZasFormMixin.save() after the record is created
  create_on: <expression>  -> ZasWorkflowMixin after every transition, and on create
Hooks can call provision(), set_active() directly (e.g. hold → disable login).
"""

import logging
import secrets

from . import spec as zs

logger = logging.getLogger(__name__)

_PWD_SPECIALS = "@$!#%*?&"


def generate_password(length=16):
    lower, upper, digits = "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789"
    alphabet = lower + upper + digits + _PWD_SPECIALS
    length = max(length, 12)
    chars = [secrets.choice(lower), secrets.choice(upper), secrets.choice(digits), secrets.choice(_PWD_SPECIALS)]
    chars += [secrets.choice(alphabet) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    if not chars[0].isalpha():  # Zango: the first character must be a letter
        i = next(i for i, c in enumerate(chars) if c.isalpha())
        chars[0], chars[i] = chars[i], chars[0]
    return "".join(chars)


def _cfg(entity_code):
    return (zs.entity(entity_code).get("app_user")) or None


def _contact(obj, cfg):
    def get(k):
        f = cfg.get(k)
        v = getattr(obj, f, None) if f else None
        return str(v) if v not in (None, "") else None
    return get("name") or str(obj), get("email"), get("mobile")


def find_user(obj, entity_code):
    from zango.apps.appauth.models import AppUserModel, UserRoleModel
    cfg = _cfg(entity_code)
    if not cfg:
        return None
    role = UserRoleModel.objects.filter(name=cfg["role"]).last()
    if not role:
        return None
    return AppUserModel.objects.filter(app_objects__contains={str(role.id): str(obj.object_uuid)}).first()


def provision(obj, entity_code, request=None):
    """Ensure the login exists and is mapped to obj. Returns the AppUserModel or None."""
    from zango.apps.appauth.models import AppUserModel, UserRoleModel
    cfg = _cfg(entity_code)
    if not cfg:
        return None
    try:
        name, email, mobile = _contact(obj, cfg)
        if not email and not mobile:
            logger.error("zas.app_user: %s %s has no email or mobile", entity_code, obj.object_uuid)
            return None
        role = UserRoleModel.objects.filter(name=cfg["role"]).last()
        if not role:
            logger.error("zas.app_user: role %r not found", cfg["role"])
            return None
        key, uid = str(role.id), str(obj.object_uuid)
        existing = AppUserModel.objects.filter(app_objects__contains={key: uid}).first()
        if not existing and email:
            existing = AppUserModel.objects.filter(email__iexact=email).first()
        if not existing and mobile:
            existing = AppUserModel.objects.filter(mobile=mobile).first()
        if existing:
            return _update(existing, role, uid, name, email, mobile)
        tenant = getattr(request, "tenant", None)
        password = None
        can_set, _ = AppUserModel.should_set_password(tenant, [role.id])
        if can_set:
            password = generate_password()
        result = AppUserModel.create_user(
            name=name, email=email, mobile=mobile, password=password, role_ids=[role.id],
            force_password_reset=True, require_verification=False, app_objects={key: uid}, tenant=tenant,
        )
        if result.get("success"):
            logger.info("zas.app_user: provisioned %s login for %s", cfg["role"], uid)
            return result.get("app_user")
        logger.error("zas.app_user: create_user failed for %s: %s", uid, result.get("message"))
    except Exception:
        logger.exception("zas.app_user: provision failed for %s", getattr(obj, "object_uuid", "?"))
    return None


def _update(user, role, uid, name, email, mobile):
    try:
        user.name = name or user.name
        if email:
            user.email = email
        if mobile:
            user.mobile = mobile
        objs = dict(user.app_objects or {})
        objs[str(role.id)] = uid
        user.app_objects = objs
        if not user.roles.filter(id=role.id).exists():
            user.roles.add(role)
        user.save()
        return user
    except Exception:
        logger.exception("zas.app_user: update failed for %s", uid)
        return None


def set_active(obj, entity_code, active):
    """Enable or disable the record's login (e.g. vendor on hold)."""
    user = find_user(obj, entity_code)
    if user and user.is_active != active:
        user.is_active = active
        user.save(update_fields=["is_active"])
    return user


def maybe_provision(obj, entity_code, request=None, on_create=False):
    """Provision when the spec's create_on is met. Safe to call repeatedly."""
    from . import access
    from . import expr as zx
    cfg = _cfg(entity_code)
    if not cfg:
        return None
    co = cfg.get("create_on", "create")
    if co == "create":
        return provision(obj, entity_code, request) if on_create else None
    ast = cfg.get("create_on_ast")
    if ast and zx.evaluate(ast, obj, access.expr_ctx(request)):
        if not find_user(obj, entity_code):
            return provision(obj, entity_code, request)
    return None
