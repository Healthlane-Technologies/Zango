"""Export builders — one per surface, sharing a common interface.

Each builder wraps the SAME `get_queryset` logic used by the corresponding
list view, so a CSV export always matches what the operator sees in the
browse UI byte for byte. Filter payloads are captured verbatim on POST and
handed back to `queryset()` here.

The `write_csv` implementation streams via `.iterator(chunk_size=1000)` so
even a 30k-row audit-log export stays under a few MB of worker RAM.
"""

from __future__ import annotations

import csv
import json
from typing import Any

from django.utils import timezone


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class ExportBuilder:
    """Common interface. Concrete builders override `queryset`, `row_for`,
    `pairs`, and set `HEADERS`."""

    HEADERS: list[str] = []

    def queryset(self, filters: dict, tenant):
        raise NotImplementedError

    def count(self, filters: dict, tenant) -> int:
        return self.queryset(filters, tenant).count()

    def pairs(self, filters: dict) -> list[tuple[str, str]]:
        """Human-readable [(label, value), ...] pairs for the filter payload.

        Powers both the My Downloads one-line summary and the CSV footer.
        """
        raise NotImplementedError

    def summarise(self, filters: dict) -> str:
        """One-line summary of the filter payload for My Downloads."""
        parts = [f"{label}: {value}" for label, value in self.pairs(filters)]
        return " · ".join(parts) if parts else "No filters"

    def row_for(self, obj) -> list:
        raise NotImplementedError

    def write_csv(self, filters: dict, tenant, fp) -> int:
        writer = csv.writer(fp)
        writer.writerow(self.HEADERS)
        count = 0
        for row in self.queryset(filters, tenant).iterator(chunk_size=1000):
            writer.writerow(self.row_for(row))
            count += 1
        self._write_footer(writer, filters, count)
        return count

    def _write_footer(self, writer, filters: dict, row_count: int) -> None:
        """Append filter metadata after the data rows so an Excel viewer sees
        what filters produced the export."""
        writer.writerow([])
        writer.writerow(["Filters applied"])
        pairs = self.pairs(filters)
        if pairs:
            for label, value in pairs:
                writer.writerow([f"{label}: {value}"])
        else:
            writer.writerow(["No filters"])
        writer.writerow([])
        writer.writerow([f"Exported at: {timezone.now():%Y-%m-%d %H:%M:%S %Z}"])
        writer.writerow([f"Rows exported: {row_count}"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_dt(dt) -> str:
    return dt.isoformat() if dt else ""


def _fmt_daterange(v: Any) -> str:
    """Render a table-date-range column filter for humans."""
    if isinstance(v, dict):
        start = v.get("startDate") or v.get("start") or ""
        end = v.get("endDate") or v.get("end") or ""
        if start and end:
            return f"{start} → {end}"
        if start:
            return f"from {start}"
        if end:
            return f"until {end}"
    if isinstance(v, str) and v:
        return v
    return ""


# ---------------------------------------------------------------------------
# App Users
# ---------------------------------------------------------------------------


class AppUsersBuilder(ExportBuilder):
    HEADERS = [
        "ID",
        "Name",
        "Email",
        "Mobile",
        "Roles",
        "Active",
        "Last Login",
        "Date Joined",
    ]

    _COLUMN_LABELS = {
        "user_name": "Name",
        "email": "Email",
        "mobile": "Mobile",
        "user_id": "User ID",
        "roles_access": "Role",
    }

    def queryset(self, filters, tenant):
        from zango.api.platform.tenancy.v1.views import UserViewAPIV1

        view = UserViewAPIV1()
        return view.get_queryset(
            filters.get("search", "") or "",
            filters.get("columns", {}) or {},
        )

    def pairs(self, filters):
        out: list[tuple[str, str]] = []
        search = (filters.get("search") or "").strip()
        if search:
            out.append(("Search", f'"{search}"'))
        columns = filters.get("columns", {}) or {}
        is_active = columns.get("is_active")
        if is_active == "true":
            out.append(("Status", "Active only"))
        elif is_active == "false":
            out.append(("Status", "Inactive only"))
        for key, label in self._COLUMN_LABELS.items():
            v = columns.get(key)
            if v not in (None, ""):
                out.append((label, str(v)))
        return out

    def row_for(self, u):
        return [
            u.id,
            u.name or "",
            u.email or "",
            str(u.mobile) if u.mobile else "",
            ", ".join(r.name for r in u.roles.all()),
            "Yes" if u.is_active else "No",
            _fmt_dt(u.last_login),
            _fmt_dt(u.date_joined),
        ]


# ---------------------------------------------------------------------------
# Access Logs
# ---------------------------------------------------------------------------


_ATTEMPT_TYPE_LABELS = {
    "login": "Login",
    "switch_role": "Switch Role",
}

_LOGIN_SUCCESS_LABELS = {
    "successful": "Successful",
    "failed": "Failed",
    "true": "Successful",
    "false": "Failed",
}


class AccessLogsBuilder(ExportBuilder):
    HEADERS = [
        "ID",
        "User",
        "Username",
        "Role",
        "IP Address",
        "User Agent",
        "Attempt Type",
        "Successful",
        "Attempt Time",
        "Session Expired At",
    ]

    def queryset(self, filters, tenant):
        from zango.api.platform.accesslogs.v1.views import AccessLogViewAPIV1

        view = AccessLogViewAPIV1()
        return view.get_queryset(
            filters.get("search", "") or "",
            tenant,
            filters.get("columns", {}) or {},
        )

    def pairs(self, filters):
        out: list[tuple[str, str]] = []
        search = (filters.get("search") or "").strip()
        if search:
            out.append(("Search", f'"{search}"'))
        columns = filters.get("columns", {}) or {}
        if columns.get("attempt_type"):
            v = columns["attempt_type"]
            out.append(("Attempt Type", _ATTEMPT_TYPE_LABELS.get(str(v), str(v))))
        if columns.get("is_login_successful"):
            v = columns["is_login_successful"]
            out.append(("Result", _LOGIN_SUCCESS_LABELS.get(str(v), str(v))))
        if columns.get("role"):
            out.append(("Role", str(columns["role"])))
        rng = _fmt_daterange(columns.get("attempt_time"))
        if rng:
            out.append(("Attempt Time", rng))
        rng = _fmt_daterange(columns.get("session_expired_at"))
        if rng:
            out.append(("Session Expired", rng))
        return out

    def row_for(self, log):
        return [
            log.id,
            f"{log.user.name} ({log.user.id})" if log.user_id else "",
            log.username or "",
            log.role.name if log.role_id else "",
            log.ip_address or "",
            log.user_agent or "",
            log.attempt_type or "",
            "Yes" if log.is_login_successful else "No",
            _fmt_dt(log.attempt_time),
            _fmt_dt(log.session_expired_at),
        ]


# ---------------------------------------------------------------------------
# Audit Logs — shared base for app / framework
# ---------------------------------------------------------------------------


_ACTION_LABELS = {"0": "Create", "1": "Update", "2": "Delete"}


class _AuditLogsBuilderBase(ExportBuilder):
    MODEL_TYPE: str = ""  # "dynamic_models" or "core_models"

    HEADERS = [
        "ID",
        "Actor",
        "Actor Type",
        "Action",
        "Object Type",
        "Object ID",
        "Object UUID",
        "Object Repr",
        "Changes",
        "Timestamp",
    ]

    def queryset(self, filters, tenant):
        from zango.api.platform.auditlogs.v1.views import AuditLogViewAPIV1

        view = AuditLogViewAPIV1()
        return view.get_queryset(
            filters.get("search", "") or "",
            tenant,
            filters.get("columns", {}) or {},
            self.MODEL_TYPE,
        )

    def _object_type_label(self, tenant, value) -> str:
        # `object_type` filter carries a content_type id — try to resolve it
        # to the model's short name for a human label. Falls back to the raw
        # id if lookup fails.
        try:
            from django.contrib.contenttypes.models import ContentType

            ct = ContentType.objects.filter(id=int(value)).first()
            if ct is not None:
                return ct.model
        except (TypeError, ValueError):
            pass
        except Exception:
            pass
        return str(value)

    def pairs(self, filters):
        out: list[tuple[str, str]] = []
        search = (filters.get("search") or "").strip()
        if search:
            out.append(("Search", f'"{search}"'))
        columns = filters.get("columns", {}) or {}
        action = columns.get("action")
        if action is not None and action != "":
            out.append(("Action", _ACTION_LABELS.get(str(action), str(action))))
        if columns.get("object_type"):
            out.append(
                ("Object Type", self._object_type_label(None, columns["object_type"]))
            )
        rng = _fmt_daterange(columns.get("timestamp"))
        if rng:
            out.append(("Timestamp", rng))
        return out

    def _actor(self, entry) -> tuple[str, str]:
        # Guard against dangling FKs so a stale actor never breaks the export.
        try:
            if entry.tenant_actor_id and entry.tenant_actor:
                return entry.tenant_actor.name or "", "tenant_actor"
        except Exception:  # noqa: BLE001
            pass
        try:
            if entry.platform_actor_id and entry.platform_actor:
                return entry.platform_actor.name or "", "platform_actor"
        except Exception:  # noqa: BLE001
            pass
        return "", ""

    def _object_uuid(self, entry) -> str:
        # object_ref is a GenericForeignKey helper on the entry — fall back
        # to empty string if the target row no longer exists.
        try:
            ref = entry.object_ref
            if ref is not None and getattr(ref, "object_uuid", None):
                return str(ref.object_uuid)
        except Exception:  # noqa: BLE001
            pass
        return ""

    def row_for(self, entry):
        actor, actor_type = self._actor(entry)
        changes = entry.changes
        if isinstance(changes, (dict, list)):
            changes = json.dumps(changes, ensure_ascii=False, default=str)
        return [
            entry.id,
            actor,
            actor_type,
            _ACTION_LABELS.get(str(entry.action), str(entry.action)),
            entry.content_type.model if entry.content_type_id else "",
            entry.object_id or "",
            self._object_uuid(entry),
            entry.object_repr or "",
            changes or "",
            _fmt_dt(entry.timestamp),
        ]


class AuditLogsAppBuilder(_AuditLogsBuilderBase):
    MODEL_TYPE = "dynamic_models"


class AuditLogsFrameworkBuilder(_AuditLogsBuilderBase):
    MODEL_TYPE = "core_models"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


from zango.apps.exports.models import ExportKind  # noqa: E402  (avoids circular)


EXPORT_BUILDERS: dict[str, ExportBuilder] = {
    ExportKind.APP_USERS.value: AppUsersBuilder(),
    ExportKind.ACCESS_LOGS.value: AccessLogsBuilder(),
    ExportKind.AUDIT_LOGS_APP.value: AuditLogsAppBuilder(),
    ExportKind.AUDIT_LOGS_FRAMEWORK.value: AuditLogsFrameworkBuilder(),
}


def get_builder(kind: str) -> ExportBuilder:
    return EXPORT_BUILDERS[kind]
