"""Create the app roles a run's policies depend on.

Why this exists: ``Workspace.sync_policies_with_roles`` attaches roles named
in ``policies.json`` to the policy, but **silently skips any role that does
not exist**:

    role_ids = [UserRoleModel.objects.get(name=role).id
                for role in roles
                if UserRoleModel.objects.filter(name=role).exists()]

So an agent that writes a perfectly good ``policies.json`` referencing
``Admin`` ends up with a policy nobody is attached to, and views no user can
reach — with no error anywhere. Creating the referenced roles before
``ws_sync`` closes that hole.

Roles are pure tenant-schema ORM, so unlike packages and migrations this runs
in-process on the Celery main thread: no relative paths, no workspace imports,
nothing that needs a subprocess.

Two sources, in order of authority:

1. ``roles.json`` at the workspace root, if the agent wrote one — lets it
   record intent (description, whether the role is app-facing).
2. Every role name referenced by any module's ``policies.json`` — the set
   that would otherwise be silently dropped.
"""

from __future__ import annotations

import json
import logging
import os

from dataclasses import dataclass


logger = logging.getLogger("zango.agent_mode")

# Framework roles. AnonymousUsers already exists; SystemUsers is internal and
# cannot legally appear in a policy. Never create or touch either.
RESERVED_ROLES = frozenset({"SystemUsers", "AnonymousUsers"})

ROLES_FILENAME = "roles.json"
MAX_ROLE_NAME = 50  # UserRoleModel.name max_length

# The platform's only `userAccess` policy (0.0.0.0/0). Attaching it is not
# optional: PermissionMixin.has_perm checks userAccess *before* view
# permissions and returns False when a role has no userAccess policy at all —
#
#     policies = self.get_policies(perm_type, view_name)
#     if not policies.exists():
#         return False
#
# so a role without it is inert, and every request from its users is denied
# no matter how correct the view policies are. The interactive skill calls
# this out in STEP 3; an earlier version of Agent Mode skipped it and shipped
# two roles that could not load a single page.
USER_ACCESS_POLICY = "AllowFromAnywhere"


@dataclass
class RoleResult:
    name: str
    status: str  # "created" | "exists" | "reserved" | "invalid" | "failed"
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("created", "exists", "reserved")


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001 - a malformed file must not break the run
        return None


def declared_roles(workspace_path: str) -> list:
    """Role names from an agent-written roles.json, if present."""
    data = _read_json(os.path.join(workspace_path, ROLES_FILENAME))
    names = []
    if isinstance(data, dict):
        data = data.get("roles") or []
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, str):
                names.append(entry)
            elif isinstance(entry, dict) and entry.get("name"):
                names.append(str(entry["name"]))
    return names


def referenced_roles(workspace_path: str) -> list:
    """Every role named by any policies.json under the workspace."""
    names = set()
    for dirpath, dirnames, filenames in os.walk(workspace_path):
        dirnames[:] = [
            d for d in dirnames if d not in ("__pycache__", ".git", "node_modules")
        ]
        if "policies.json" not in filenames:
            continue
        data = _read_json(os.path.join(dirpath, "policies.json"))
        if not isinstance(data, dict):
            continue
        for policy in data.get("policies") or []:
            if isinstance(policy, dict):
                for role in policy.get("roles") or []:
                    if isinstance(role, str) and role.strip():
                        names.add(role.strip())
    return sorted(names)


def _attach_user_access(role) -> bool:
    """Give a new role the baseline userAccess policy. Never raises."""
    from zango.apps.permissions.models import PolicyModel

    try:
        policy = PolicyModel.objects.filter(name=USER_ACCESS_POLICY).first()
        if policy is None:
            return False
        role.policies.add(policy)
        return True
    except Exception:  # noqa: BLE001
        logger.exception("agent_mode: could not attach %s", USER_ACCESS_POLICY)
        return False


def ensure_roles(workspace_path: str, emit=None) -> list:
    """Create every role the workspace references but the app lacks.

    Must run with the tenant already bound, and before ``ws_sync``.
    """
    from zango.apps.appauth.models import UserRoleModel

    wanted = []
    for name in [*declared_roles(workspace_path), *referenced_roles(workspace_path)]:
        if name not in wanted:
            wanted.append(name)

    results = []
    for name in wanted:
        if name in RESERVED_ROLES:
            results.append(RoleResult(name, "reserved"))
            continue
        if not name or len(name) > MAX_ROLE_NAME:
            results.append(
                RoleResult(
                    name[:60], "invalid", f"role names must be 1-{MAX_ROLE_NAME} chars"
                )
            )
            if emit:
                emit(f"role {name[:60]!r}: invalid name, skipped", is_error=True)
            continue
        try:
            if UserRoleModel.objects.filter(name=name).exists():
                results.append(RoleResult(name, "exists"))
                continue
            role = UserRoleModel.objects.create(name=name, is_active=True)
            attached = _attach_user_access(role)
            results.append(RoleResult(name, "created"))
            if emit:
                emit(
                    f"role {name!r}: created"
                    + (f" (+{USER_ACCESS_POLICY})" if attached else "")
                )
            if not attached and emit:
                emit(
                    f"role {name!r}: could not attach {USER_ACCESS_POLICY}; "
                    "its users will be denied access until it is assigned",
                    is_error=True,
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent_mode: could not create role %s", name)
            results.append(RoleResult(name, "failed", f"{type(exc).__name__}: {exc}"))
            if emit:
                emit(f"role {name!r}: FAILED — {exc}", is_error=True)
    return results
