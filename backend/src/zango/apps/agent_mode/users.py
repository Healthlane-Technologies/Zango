"""Create the test users that make a generated app actually usable.

The interactive skill ends with "create test users for each role"; without
them a run finishes with working code, correct policies and nobody able to
log in — which is not a working app.

Same shape as roles: the **agent declares**, the **runner creates**. The
agent cannot touch the ORM (its hooks run on the SDK's event loop, where
Django raises SynchronousOnlyOperation and the connection is on the public
schema), so it writes `users.json` and the runner reconciles it after the
stream ends.

Passwords are generated here, never chosen by the agent, and returned to the
caller so the panel can show them once. They are deliberately temporary:
``force_password_reset=True`` means the first login must change them.
"""

from __future__ import annotations

import logging
import os
import secrets
import string

from dataclasses import dataclass


logger = logging.getLogger("zango.agent_mode")

USERS_FILENAME = "users.json"
PASSWORD_LENGTH = 16
MAX_USERS = 20


@dataclass
class UserResult:
    email: str
    role: str = ""
    status: str = ""  # "created" | "exists" | "no_role" | "failed" | "invalid"
    password: str = ""  # only set for users created by this run
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("created", "exists")

    def to_dict(self, include_password: bool = True) -> dict:
        data = {"email": self.email, "role": self.role, "status": self.status}
        if self.message:
            data["message"] = self.message
        if include_password and self.password:
            data["password"] = self.password
        return data


def generate_password(length: int = PASSWORD_LENGTH) -> str:
    """A temporary password that satisfies typical complexity rules."""
    alphabet = string.ascii_letters + string.digits
    core = "".join(secrets.choice(alphabet) for _ in range(length - 4))
    return (
        secrets.choice(string.ascii_uppercase)
        + secrets.choice(string.ascii_lowercase)
        + secrets.choice(string.digits)
        + "!"
        + core
    )


def declared_users(workspace_path: str) -> list:
    """Users the agent asked for, from users.json."""
    path = os.path.join(workspace_path, USERS_FILENAME)
    try:
        import json

        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:  # noqa: BLE001
        return []

    if isinstance(data, dict):
        data = data.get("users") or []
    if not isinstance(data, list):
        return []

    out = []
    for entry in data[:MAX_USERS]:
        if not isinstance(entry, dict):
            continue
        email = str(entry.get("email") or "").strip()
        role = str(entry.get("role") or entry.get("role_name") or "").strip()
        if not email or not role:
            continue
        out.append(
            {
                "email": email,
                "role": role,
                "name": str(entry.get("name") or email.split("@")[0]),
                "mobile": str(entry.get("mobile") or ""),
            }
        )
    return out


def ensure_users(workspace_path: str, emit=None) -> list:
    """Create declared test users. Runs with the tenant already bound."""
    from zango.apps.appauth.models import AppUserModel, UserRoleModel

    results = []
    for spec in declared_users(workspace_path):
        email, role_name = spec["email"], spec["role"]
        try:
            if AppUserModel.objects.filter(email__iexact=email).exists():
                results.append(UserResult(email, role_name, "exists"))
                continue

            role = UserRoleModel.objects.filter(name=role_name).first()
            if role is None:
                results.append(
                    UserResult(
                        email,
                        role_name,
                        "no_role",
                        message=f"role {role_name!r} does not exist",
                    )
                )
                if emit:
                    emit(f"user {email}: role {role_name!r} missing", is_error=True)
                continue

            password = generate_password()
            response = AppUserModel.create_user(
                spec["name"],
                email,
                spec["mobile"],
                password,
                [role.id],
                force_password_reset=True,
                require_verification=False,
            )
            ok = not isinstance(response, dict) or response.get("success", True)
            if ok:
                results.append(
                    UserResult(email, role_name, "created", password=password)
                )
                if emit:
                    emit(f"user {email} created for role {role_name}")
            else:
                results.append(
                    UserResult(
                        email,
                        role_name,
                        "failed",
                        message=str(response.get("message", ""))[:500],
                    )
                )
                if emit:
                    emit(f"user {email}: FAILED — {response}", is_error=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent_mode: could not create user %s", email)
            results.append(
                UserResult(
                    email, role_name, "failed", message=f"{type(exc).__name__}: {exc}"
                )
            )
            if emit:
                emit(f"user {email}: FAILED — {exc}", is_error=True)
    return results
