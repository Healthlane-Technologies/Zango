"""Connection guard — tenant isolation Layer 4.

A thread-local guard that, while active, makes tenant-switching methods on
the Django DB connection raise `PermissionError`. Catches reflective bypasses
that slipped past the AST validator (e.g. `getattr(connection, "set_tenant")`).

Implementation: monkey-patches the connection class methods once (idempotent).
The patched methods check a thread-local flag; outside an active guard
context they delegate to the original method unchanged.

Layer 2 (Postgres role) is the load-bearing defense; this is belt-to-the-
suspenders.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator


_guard_active = threading.local()


class TenantSwitchBlocked(PermissionError):
    """Raised when a code-execution snippet tries to switch tenants."""


def _is_active() -> bool:
    return bool(getattr(_guard_active, "active", False))


def _blocked_method_factory(original, name: str):
    def _blocked(self, *args, **kwargs):
        if _is_active():
            raise TenantSwitchBlocked(
                f"connection.{name}(...) is not allowed in Code Execution. "
                f"Cross-tenant access is blocked at the Postgres role level too."
            )
        return original(self, *args, **kwargs)

    _blocked.__name__ = name
    _blocked.__qualname__ = name
    _blocked.__wrapped__ = original  # type: ignore[attr-defined]
    return _blocked


def _blocked_setattr_factory(original_setattr):
    BANNED = {"schema_name", "tenant", "tenant_type"}

    def _blocked(self, name, value):
        if _is_active() and name in BANNED:
            raise TenantSwitchBlocked(
                f"Assigning to connection.{name} is not allowed in Code Execution."
            )
        return original_setattr(self, name, value)

    _blocked.__name__ = "__setattr__"
    _blocked.__wrapped__ = original_setattr  # type: ignore[attr-defined]
    return _blocked


_GUARDED_METHODS = ("set_tenant", "set_schema", "set_schema_to_public", "_set_schema")


def _install_patches_once() -> None:
    """Install method/attribute patches on the live connection class.

    Safe to call multiple times. Original implementations are preserved and
    only invoked when `_is_active()` is False, so production traffic is
    unaffected.

    Note: `django.db.connection` is a proxy that lazily forwards to the real
    DatabaseWrapper. We must patch the wrapper class, not the proxy.
    """
    from django.db import DEFAULT_DB_ALIAS, connections

    cls = type(connections[DEFAULT_DB_ALIAS])
    if getattr(cls, "_codexec_guard_installed", False):
        return

    for name in _GUARDED_METHODS:
        if hasattr(cls, name):
            original = getattr(cls, name)
            if callable(original):
                setattr(cls, name, _blocked_method_factory(original, name))

    # Wrap __setattr__ to guard direct attribute assignment.
    original_setattr = cls.__setattr__
    cls.__setattr__ = _blocked_setattr_factory(original_setattr)  # type: ignore[assignment]

    cls._codexec_guard_installed = True


@contextmanager
def install_connection_guard() -> Iterator[None]:
    """Activate the connection guard for the calling thread."""
    _install_patches_once()
    prev = getattr(_guard_active, "active", False)
    _guard_active.active = True
    try:
        yield
    finally:
        _guard_active.active = prev
