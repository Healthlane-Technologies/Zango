"""Platform API views for user-requested CSV exports.

Mounted under /api/v1/apps/<app_uuid>/exports/.

- POST /<kind>/ — validate + count + create + dispatch
- GET  /       — list current user's jobs (paginated, newest first)
- GET  /job/<uuid>/ — job detail
- DELETE /job/<uuid>/ — delete (cancel semantics if still queued/running)

Downloads: the serialized job carries `file_url` — a presigned URL with
the download disposition baked in — so the client fetches the file
directly from the storage backend. No proxy view.
"""

from __future__ import annotations

import logging

from django.db import connection, transaction
from django.utils.decorators import method_decorator

from zango.apps.exports.builders import get_builder
from zango.apps.exports.models import (
    ACTIVE_STATUSES,
    MAX_EXPORT_ROWS,
    ExportJob,
    ExportKind,
)
from zango.apps.exports.tasks import run_export
from zango.core.api import (
    TenantMixin,
    ZangoGenericPlatformAPIView,
    get_api_response,
)
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path

from .serializers import ExportJobSerializer


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bind_tenant(view, app_uuid):
    tenant = view.get_tenant(app_uuid=app_uuid)
    connection.set_tenant(tenant)
    return tenant


def _platform_user(request):
    auth_user = getattr(request, "user", None)
    if auth_user is None:
        return None
    return getattr(auth_user, "platform_user", None)


# ---------------------------------------------------------------------------
# Create export
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class ExportJobCreateView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST /exports/<kind>/  — enqueue a new export job."""

    def post(self, request, app_uuid, kind, *args, **kwargs):
        try:
            if kind not in ExportKind.values:
                return get_api_response(
                    False, {"message": f"Unknown export kind '{kind}'."}, 400
                )

            tenant = _bind_tenant(self, app_uuid)
            platform_user = _platform_user(request)

            # 1 — rate limit: one active job per (user, kind)
            if platform_user is not None:
                active = ExportJob.objects.filter(
                    requested_by=platform_user,
                    kind=kind,
                    status__in=list(ACTIVE_STATUSES),
                ).exists()
                if active:
                    return get_api_response(
                        False,
                        {
                            "message": (
                                "An export of this kind is already in progress. "
                                "Check My Downloads."
                            ),
                            "code": "export_in_progress",
                        },
                        409,
                    )

            # 2 — pre-count against the actual queryset the builder will use
            filters = request.data.get("filters", {}) or {}
            builder = get_builder(kind)
            try:
                row_count = builder.count(filters, tenant)
            except Exception as exc:  # noqa: BLE001
                log.exception("exports: pre-count failed for %s", kind)
                return get_api_response(
                    False,
                    {"message": f"Could not evaluate filters: {exc}"},
                    400,
                )

            if row_count > MAX_EXPORT_ROWS:
                return get_api_response(
                    False,
                    {
                        "message": (
                            f"Too many rows to export. Your filters match "
                            f"{row_count:,} rows (max {MAX_EXPORT_ROWS:,}). "
                            "Try adding a date range or narrower search."
                        ),
                        "code": "row_cap_exceeded",
                        "row_count": row_count,
                        "max_rows": MAX_EXPORT_ROWS,
                    },
                    400,
                )

            # 3 — create + dispatch after commit
            job = ExportJob.objects.create(
                kind=kind,
                filters=filters,
                filters_summary=builder.summarise(filters),
                row_count=row_count,
                requested_by=platform_user,
            )
            transaction.on_commit(
                lambda: run_export.apply_async(
                    args=[tenant.name, str(job.object_uuid)]
                )
            )

            return get_api_response(
                True,
                {
                    "job": ExportJobSerializer(job).data,
                    "message": "Export queued. Track it in My Downloads.",
                },
                201,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("exports: create failed")
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class ExportJobListView(
    ZangoGenericPlatformAPIView, ZangoAPIPagination, TenantMixin
):
    """GET /exports/  — list current user's export jobs, newest first."""

    pagination_class = ZangoAPIPagination

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            platform_user = _platform_user(request)

            qs = ExportJob.objects.all().order_by("-created_at")
            if platform_user is not None:
                qs = qs.filter(requested_by=platform_user)
            kind = request.GET.get("kind")
            if kind:
                qs = qs.filter(kind=kind)

            page = self.paginate_queryset(qs, request, view=self)
            data = ExportJobSerializer(page, many=True).data
            payload = self.get_paginated_response_data(data)
            return get_api_response(
                True, {"exports": payload, "message": "Exports fetched successfully"}, 200
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("exports: list failed")
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Detail + Delete
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class ExportJobDetailView(ZangoGenericPlatformAPIView, TenantMixin):
    """GET  /exports/<job_uuid>/  — detail
    DELETE /exports/<job_uuid>/  — delete (row + file). Only the requester can delete.
    """

    def _get_own_job(self, request, app_uuid, job_uuid):
        _bind_tenant(self, app_uuid)
        platform_user = _platform_user(request)
        qs = ExportJob.objects.filter(object_uuid=job_uuid)
        if platform_user is not None:
            qs = qs.filter(requested_by=platform_user)
        return qs.first()

    def get(self, request, app_uuid, job_uuid, *args, **kwargs):
        try:
            job = self._get_own_job(request, app_uuid, job_uuid)
            if not job:
                return get_api_response(False, {"message": "Job not found"}, 404)
            return get_api_response(True, {"job": ExportJobSerializer(job).data}, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("exports: detail failed")
            return get_api_response(False, {"message": str(exc)}, 500)

    def delete(self, request, app_uuid, job_uuid, *args, **kwargs):
        try:
            job = self._get_own_job(request, app_uuid, job_uuid)
            if not job:
                return get_api_response(False, {"message": "Job not found"}, 404)

            # Delete the underlying file too so blobs don't leak in storage.
            if job.file and job.file.name:
                try:
                    job.file.delete(save=False)
                except Exception:  # noqa: BLE001
                    log.warning(
                        "exports: could not delete file %s for job %s",
                        job.file.name,
                        job.object_uuid,
                    )
            job.delete()
            return get_api_response(True, {"message": "Export deleted"}, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("exports: delete failed")
            return get_api_response(False, {"message": str(exc)}, 500)


