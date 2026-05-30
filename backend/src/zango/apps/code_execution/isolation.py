"""Per-run session pinning (isolation Layer 3).

Sets `search_path` and `statement_timeout` for the duration of a single
transaction. Unqualified table references resolve to this tenant's schema
or `public` only; the statement timeout caps any one query at the snippet's
wall-clock budget.

L2 (per-tenant Postgres role with USAGE only on its own schema) — the
load-bearing defense for cross-tenant query blocking — is currently PARKED.
We are deliberately not provisioning DB-level roles in this environment.
The remaining defenses against cross-tenant access are:

  - L1: AST deny-list (rejects obvious tenant-switching attempts at save)
  - L3: locked search_path (unqualified queries resolve to this tenant)
  - L4: ConnectionGuard (blocks `connection.set_tenant`, etc. at runtime)

This is a documented gap. Snippets *can* still reach other tenant schemas
via fully-qualified raw SQL (`SELECT … FROM "tntApp"."x"`). To close this,
we will need to provision per-tenant Postgres roles — see docs/code-
execution-spec.html § Tenant isolation.
"""

from __future__ import annotations

import re


# Postgres identifiers (quoted): letters of either case, digits, underscores.
# Allow up to 63 chars (PG limit). Schema names from django-tenants may be
# mixed-case (e.g. "CRASystem7063").
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


def _validate_identifier(value: str, label: str) -> str:
    """Ensure `value` is safe to embed in a quoted SQL identifier (case-preserved)."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    if not _IDENT_RE.fullmatch(value):
        raise ValueError(f"Unsafe {label}: {value!r}")
    return value


def begin_isolated_session(cursor, schema_name: str, timeout_seconds: int) -> None:
    """Pin session settings inside the current transaction.

    Caller must be inside `transaction.atomic()`. Settings revert automatically
    when the transaction ends.

    - SET LOCAL search_path: tenant schema + public, nothing else.
    - SET LOCAL statement_timeout: snippet's wall-clock budget in ms.
    """
    schema = _validate_identifier(schema_name, "schema_name")
    timeout_ms = max(1000, int(timeout_seconds) * 1000)

    cursor.execute(f'SET LOCAL search_path = "{schema}", public')
    cursor.execute(f"SET LOCAL statement_timeout = {timeout_ms}")
