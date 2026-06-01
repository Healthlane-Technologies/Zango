"""Platform API views for Code Execution.

Mounted under /api/platform/v1/apps/<app_uuid>/code-execution/.

All views inherit `ZangoGenericPlatformAPIView` (session + knox auth, platform
user required) and use `set_app_schema_path` to bind the tenant context from
the URL's app_uuid.
"""

from __future__ import annotations

import hashlib
import logging

from django.db import connection, transaction
from django.http import FileResponse, Http404, HttpResponse
from urllib.parse import quote as _url_quote

from django.utils.decorators import method_decorator
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from zango.apps.code_execution.models import (
    CodeExecFile,
    CodeExecution,
    CodeExecutionLogLine,
    CodeSnippet,
    CodeSnippetFile,
    ExecStatus,
    FileKind,
    TERMINAL_STATUSES,
    TriggerKind,
)
from zango.apps.code_execution.tasks import codexec_executor
from zango.apps.code_execution.validator import validate
from zango.core.api import (
    TenantMixin,
    ZangoGenericPlatformAPIView,
    get_api_response,
)
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path

from .serializers import (
    CodeExecFileSerializer,
    CodeExecutionDetailSerializer,
    CodeExecutionListSerializer,
    CodeSnippetDetailSerializer,
    CodeSnippetFileSerializer,
    CodeSnippetListSerializer,
    CodeSnippetWriteSerializer,
)


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bind_tenant(view, app_uuid):
    """Resolve tenant from URL UUID and set the DB connection to its schema."""
    tenant = view.get_tenant(app_uuid=app_uuid)
    connection.set_tenant(tenant)
    return tenant


def _user_label(request) -> str:
    """Return the requesting PlatformUserModel's email.

    `request.user` is the Django auth User. The PlatformUserModel lives
    one hop away via the `platform_user` reverse OneToOne FK.
    """
    auth_user = getattr(request, "user", None)
    if auth_user is None:
        return "system"
    platform_user = getattr(auth_user, "platform_user", None)
    if platform_user is not None:
        email = (getattr(platform_user, "email", "") or "").strip()
        if email:
            return email
    # Fallback to whatever the auth user carries.
    return (getattr(auth_user, "email", "") or "").strip() or "system"


def _content_disposition(filename: str) -> str:
    """Build a Content-Disposition header that preserves the original name."""
    safe_ascii = filename.encode("ascii", "ignore").decode("ascii") or "download"
    quoted = _url_quote(filename)
    return f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{quoted}"


def _serve_filefield(file_field, name: str) -> HttpResponse:
    """Serve a Django FileField as a download with the original name."""
    storage = file_field.storage
    # Prefer signed URL if the storage exposes one (S3 returns a presigned URL).
    try:
        url = file_field.url
    except Exception:  # noqa: BLE001
        url = None
    if url and (url.startswith("http://") or url.startswith("https://")):
        resp = HttpResponse(status=302)
        resp["Location"] = url
        resp["Content-Disposition"] = _content_disposition(name)
        return resp
    # Fall back to streaming through Django.
    fh = file_field.open("rb")
    resp = FileResponse(fh, as_attachment=True, filename=name)
    resp["Content-Disposition"] = _content_disposition(name)
    return resp


# ---------------------------------------------------------------------------
# Snippet list / create
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetListView(
    ZangoGenericPlatformAPIView, ZangoAPIPagination, TenantMixin
):
    pagination_class = ZangoAPIPagination
    parser_classes = (JSONParser,)

    def get_queryset(self, search):
        qs = CodeSnippet.objects.filter(is_archived=False).order_by("-modified_at")
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(slug__icontains=search)
        return qs

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            search = request.GET.get("search", "")
            qs = self.get_queryset(search)
            page = self.paginate_queryset(qs, request, view=self)
            data = CodeSnippetListSerializer(page, many=True).data
            paginated = self.get_paginated_response_data(data)
            return get_api_response(True, {"snippets": paginated}, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: snippet list failed")
            return get_api_response(False, {"message": str(exc)}, 500)

    def post(self, request, app_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            ser = CodeSnippetWriteSerializer(data=request.data)
            ser.is_valid(raise_exception=True)

            # Validate code at save time (AST L1)
            violations = validate(ser.validated_data.get("code", ""))
            if violations:
                return get_api_response(
                    False,
                    {
                        "message": "Code failed AST validation.",
                        "violations": [v.to_dict() for v in violations],
                    },
                    200,
                )

            user = _user_label(request)
            snippet = CodeSnippet.objects.create(
                **ser.validated_data,
                created_by=user,
                modified_by=user,
            )
            return get_api_response(
                True,
                {"snippet": CodeSnippetDetailSerializer(snippet).data},
                201,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: snippet create failed")
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Snippet detail / update / delete
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetDetailView(ZangoGenericPlatformAPIView, TenantMixin):
    parser_classes = (JSONParser,)

    def _get(self, snippet_uuid):
        try:
            return CodeSnippet.objects.get(object_uuid=snippet_uuid)
        except CodeSnippet.DoesNotExist as exc:
            raise Http404("snippet not found") from exc

    def get(self, request, app_uuid, snippet_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            snippet = self._get(snippet_uuid)
            return get_api_response(
                True,
                {"snippet": CodeSnippetDetailSerializer(snippet).data},
                200,
            )
        except Http404 as exc:
            return get_api_response(False, {"message": str(exc)}, 404)
        except Exception as exc:  # noqa: BLE001
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetUpdateView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST /snippets/{id}/update/  — partial update.

    Update is a POST (not PATCH) so we stick to GET + POST only on the wire.
    """

    parser_classes = (JSONParser,)

    def post(self, request, app_uuid, snippet_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                snippet = CodeSnippet.objects.get(object_uuid=snippet_uuid)
            except CodeSnippet.DoesNotExist:
                return get_api_response(False, {"message": "snippet not found"}, 404)

            ser = CodeSnippetWriteSerializer(snippet, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            new_code = ser.validated_data.get("code", snippet.code)
            if new_code != snippet.code:
                violations = validate(new_code)
                if violations:
                    return get_api_response(
                        False,
                        {
                            "message": "Code failed AST validation.",
                            "violations": [v.to_dict() for v in violations],
                        },
                        422,
                    )
                snippet.bump_version()
            for field, value in ser.validated_data.items():
                setattr(snippet, field, value)
            snippet.modified_by = _user_label(request)
            snippet.save()
            return get_api_response(
                True,
                {"snippet": CodeSnippetDetailSerializer(snippet).data},
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: snippet update failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetArchiveView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST /snippets/{id}/archive/  — soft delete."""

    parser_classes = (JSONParser,)

    def post(self, request, app_uuid, snippet_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                snippet = CodeSnippet.objects.get(object_uuid=snippet_uuid)
            except CodeSnippet.DoesNotExist:
                return get_api_response(False, {"message": "snippet not found"}, 404)
            snippet.is_archived = True
            snippet.save(update_fields=["is_archived", "modified_at"])
            return get_api_response(True, {"message": "archived"}, 200)
        except Exception as exc:  # noqa: BLE001
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Validate (dry run AST check)
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetValidateView(ZangoGenericPlatformAPIView, TenantMixin):
    parser_classes = (JSONParser,)

    def post(self, request, app_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            code = request.data.get("code", "")
            violations = validate(code)
            return get_api_response(
                True,
                {
                    "valid": len(violations) == 0,
                    "violations": [v.to_dict() for v in violations],
                },
                200,
            )
        except Exception as exc:  # noqa: BLE001
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Trigger a run
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetRunView(ZangoGenericPlatformAPIView, TenantMixin):
    parser_classes = (JSONParser,)

    def post(self, request, app_uuid, snippet_uuid, *args, **kwargs):
        try:
            tenant = _bind_tenant(self, app_uuid)
            try:
                snippet = CodeSnippet.objects.get(object_uuid=snippet_uuid, is_archived=False)
            except CodeSnippet.DoesNotExist:
                return get_api_response(False, {"message": "snippet not found"}, 404)

            # Refuse a second concurrent run on the same snippet.
            in_flight = CodeExecution.objects.filter(
                snippet=snippet, status__in=[ExecStatus.QUEUED, ExecStatus.RUNNING]
            ).first()
            if in_flight:
                return get_api_response(
                    False,
                    {
                        "message": "Another run for this snippet is already in flight.",
                        "execution_uuid": str(in_flight.object_uuid),
                    },
                    200,
                )

            # AST recheck before enqueuing.
            violations = validate(snippet.code)
            if violations:
                return get_api_response(
                    False,
                    {
                        "message": "Snippet has validation violations; fix them first.",
                        "violations": [v.to_dict() for v in violations],
                    },
                    200,
                )

            user = _user_label(request)
            trigger_kind = request.data.get("trigger_kind") or TriggerKind.UI_RUN

            # Optional overrides — used by "Re-run this version" from version history
            source_override = request.data.get("source_override")
            version_override = request.data.get("snippet_version_override")

            code_to_run = source_override if source_override is not None else snippet.code
            version_to_record = (
                int(version_override) if version_override is not None
                else snippet.version
            )
            source_hash = hashlib.sha256(code_to_run.encode("utf-8")).hexdigest()

            # AST recheck the actual code being run (could be a historical version)
            violations_for_run = validate(code_to_run)
            if violations_for_run:
                return get_api_response(
                    False,
                    {
                        "message": "Code for this version has validation violations.",
                        "violations": [v.to_dict() for v in violations_for_run],
                    },
                    200,
                )

            with transaction.atomic():
                execution = CodeExecution.objects.create(
                    snippet=snippet,
                    snippet_version=version_to_record,
                    source_snapshot=code_to_run,
                    source_hash=source_hash,
                    status=ExecStatus.QUEUED,
                    triggered_by=user,
                    trigger_kind=trigger_kind,
                )
                # Snapshot snippet files → exec input files (shared storage_key,
                # tracked via source_snippet_file FK).
                for snip_file in snippet.files.all():
                    CodeExecFile.objects.create(
                        execution=execution,
                        kind=FileKind.INPUT,
                        name=snip_file.name,
                        # Reuse the existing blob — no byte copy.
                        file=snip_file.file.name,
                        source_snippet_file=snip_file,
                        size_bytes=snip_file.size_bytes,
                        content_type=snip_file.content_type,
                        sha256=snip_file.sha256,
                    )

            # Enqueue. The celery task does its own AST recheck on pickup.
            try:
                async_result = codexec_executor.apply_async(
                    args=[str(execution.object_uuid), tenant.name],
                    soft_time_limit=snippet.timeout_seconds,
                    time_limit=snippet.timeout_seconds + 10,
                )
                execution.celery_task_id = (async_result.id or "")[:64]
                execution.save(update_fields=["celery_task_id", "modified_at"])
            except Exception:  # noqa: BLE001
                # Couldn't reach the broker — mark queued anyway so the row is
                # visible; user can re-enqueue. Don't 500 the whole request.
                log.exception("codexec: failed to enqueue celery task")

            return get_api_response(
                True,
                {
                    "execution": CodeExecutionListSerializer(execution).data,
                },
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: run trigger failed")
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Snippet versions
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetVersionsView(ZangoGenericPlatformAPIView, TenantMixin):
    """GET /snippets/{id}/versions/

    Returns the distinct snippet_version values this snippet has been run at,
    along with the frozen source_snapshot for each, run counts, and first/last
    run timestamps. Useful for a "version history" view in the UI.

    Note: a version that was saved but never run is NOT in the result — we
    only persist code snapshots via executions. The current `snippet.code`
    + `snippet.version` is returned as a synthetic "current" entry on top.
    """

    def get(self, request, app_uuid, snippet_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                snippet = CodeSnippet.objects.get(object_uuid=snippet_uuid)
            except CodeSnippet.DoesNotExist:
                return get_api_response(False, {"message": "snippet not found"}, 404)

            from django.db.models import Count, Max, Min

            qs = (
                CodeExecution.objects.filter(snippet=snippet)
                .values("snippet_version", "source_hash")
                .annotate(
                    run_count=Count("id"),
                    first_run_at=Min("queued_at"),
                    last_run_at=Max("queued_at"),
                )
                .order_by("-snippet_version")
            )

            versions = []
            seen_versions = set()
            for row in qs:
                v = row["snippet_version"]
                if v in seen_versions:
                    continue
                seen_versions.add(v)
                # Find a representative source_snapshot for this version
                rep = (
                    CodeExecution.objects.filter(
                        snippet=snippet, snippet_version=v
                    )
                    .only("source_snapshot", "source_hash", "id")
                    .first()
                )
                versions.append({
                    "version": v,
                    "source_hash": row["source_hash"],
                    "source_snapshot": rep.source_snapshot if rep else "",
                    "run_count": row["run_count"],
                    "first_run_at": row["first_run_at"].isoformat() if row["first_run_at"] else None,
                    "last_run_at": row["last_run_at"].isoformat() if row["last_run_at"] else None,
                    "is_current": v == snippet.version,
                    "representative_execution_uuid": str(rep.object_uuid) if rep else None,
                })

            # If the current snippet version has never been run, prepend it as
            # a "current · unrun" entry so the user still sees it.
            if snippet.version not in seen_versions:
                versions.insert(0, {
                    "version": snippet.version,
                    "source_hash": snippet.code_hash,
                    "source_snapshot": snippet.code,
                    "run_count": 0,
                    "first_run_at": None,
                    "last_run_at": None,
                    "is_current": True,
                    "representative_execution_uuid": None,
                })

            return get_api_response(
                True,
                {
                    "snippet_uuid": str(snippet.object_uuid),
                    "snippet_name": snippet.name,
                    "current_version": snippet.version,
                    "versions": versions,
                },
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: versions endpoint failed")
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Snippet files
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetFileListView(ZangoGenericPlatformAPIView, TenantMixin):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get(self, request, app_uuid, snippet_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            qs = CodeSnippetFile.objects.filter(snippet__object_uuid=snippet_uuid).order_by("name")
            return get_api_response(
                True,
                {"files": CodeSnippetFileSerializer(qs, many=True).data},
                200,
            )
        except Exception as exc:  # noqa: BLE001
            return get_api_response(False, {"message": str(exc)}, 500)

    def post(self, request, app_uuid, snippet_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                snippet = CodeSnippet.objects.get(object_uuid=snippet_uuid, is_archived=False)
            except CodeSnippet.DoesNotExist:
                return get_api_response(False, {"message": "snippet not found"}, 404)

            files = request.FILES.getlist("files") or list(request.FILES.values())
            if not files:
                return get_api_response(
                    False, {"message": "No files in the request."}, 400
                )

            results = []
            for f in files:
                raw_name = getattr(f, "name", "") or ""
                base = raw_name.replace("\\", "/").split("/")[-1].lstrip(".")[:255]
                if not base:
                    continue
                # Capture bytes once for sha256 (small files — 25 MB cap).
                bytes_seen = 0
                hasher = hashlib.sha256()
                for chunk in f.chunks():
                    hasher.update(chunk)
                    bytes_seen += len(chunk)
                f.seek(0)

                obj, created = CodeSnippetFile.objects.update_or_create(
                    snippet=snippet,
                    name=base,
                    defaults={
                        "size_bytes": bytes_seen,
                        "content_type": getattr(f, "content_type", "") or "",
                        "sha256": hasher.hexdigest(),
                    },
                )
                # Replace existing blob if overwriting.
                if not created and obj.file:
                    try:
                        obj.file.delete(save=False)
                    except Exception:  # noqa: BLE001
                        pass
                obj.file.save(base, f, save=True)
                results.append(obj)

            return get_api_response(
                True,
                {"files": CodeSnippetFileSerializer(results, many=True).data},
                201,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: snippet file upload failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetFileDeleteView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST /snippets/{id}/files/{file_uuid}/delete/  — hard delete a snippet file row."""

    parser_classes = (JSONParser,)

    def post(self, request, app_uuid, snippet_uuid, file_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                f = CodeSnippetFile.objects.get(object_uuid=file_uuid, snippet__object_uuid=snippet_uuid)
            except CodeSnippetFile.DoesNotExist:
                return get_api_response(False, {"message": "file not found"}, 404)
            # Hard delete the row. The blob stays on storage as long as any
            # CodeExecFile snapshot references the same storage path (the FK
            # uses on_delete=SET_NULL, so past runs are unaffected).
            f.delete()
            return get_api_response(True, {"message": "deleted"}, 200)
        except Exception as exc:  # noqa: BLE001
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class CodeSnippetFileDownloadView(ZangoGenericPlatformAPIView, TenantMixin):
    def get(self, request, app_uuid, snippet_uuid, file_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                f = CodeSnippetFile.objects.get(object_uuid=file_uuid, snippet__object_uuid=snippet_uuid)
            except CodeSnippetFile.DoesNotExist:
                return get_api_response(False, {"message": "file not found"}, 404)
            return _serve_filefield(f.file, f.name)
        except Exception as exc:  # noqa: BLE001
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Execution list / detail
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class CodeExecutionListView(
    ZangoGenericPlatformAPIView, ZangoAPIPagination, TenantMixin
):
    pagination_class = ZangoAPIPagination

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            qs = CodeExecution.objects.select_related("snippet").order_by("-queued_at")
            snippet_uuid = request.GET.get("snippet_uuid")
            if snippet_uuid:
                qs = qs.filter(snippet__object_uuid=snippet_uuid)
            status = request.GET.get("status")
            if status:
                qs = qs.filter(status=status)
            page = self.paginate_queryset(qs, request, view=self)
            data = CodeExecutionListSerializer(page, many=True).data
            return get_api_response(
                True,
                {"executions": self.get_paginated_response_data(data)},
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: execution list failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class CodeExecutionDetailView(ZangoGenericPlatformAPIView, TenantMixin):
    def get(self, request, app_uuid, execution_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                execution = (
                    CodeExecution.objects.select_related("snippet")
                    .prefetch_related("files")
                    .get(object_uuid=execution_uuid)
                )
            except CodeExecution.DoesNotExist:
                return get_api_response(False, {"message": "execution not found"}, 404)
            return get_api_response(
                True,
                {"execution": CodeExecutionDetailSerializer(execution).data},
                200,
            )
        except Exception as exc:  # noqa: BLE001
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Execution files
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class CodeExecFileListView(ZangoGenericPlatformAPIView, TenantMixin):
    def get(self, request, app_uuid, execution_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            qs = CodeExecFile.objects.filter(execution__object_uuid=execution_uuid).order_by(
                "kind", "name"
            )
            kind = request.GET.get("kind")
            if kind in (FileKind.INPUT, FileKind.OUTPUT):
                qs = qs.filter(kind=kind)
            return get_api_response(
                True,
                {"files": CodeExecFileSerializer(qs, many=True).data},
                200,
            )
        except Exception as exc:  # noqa: BLE001
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class CodeExecFileDownloadView(ZangoGenericPlatformAPIView, TenantMixin):
    def get(self, request, app_uuid, execution_uuid, file_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                f = CodeExecFile.objects.get(object_uuid=file_uuid, execution__object_uuid=execution_uuid)
            except CodeExecFile.DoesNotExist:
                return get_api_response(False, {"message": "file not found"}, 404)
            return _serve_filefield(f.file, f.name)
        except Exception as exc:  # noqa: BLE001
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Log tail (live)  &  abort
# ---------------------------------------------------------------------------


@method_decorator(set_app_schema_path, name="dispatch")
class CodeExecutionExportView(ZangoGenericPlatformAPIView, TenantMixin):
    """GET /executions/export.csv?snippet_uuid=…&status=…&from=…&to=…

    Streams the filtered execution history as CSV. Useful for compliance
    audits and offline analysis.
    """

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            import csv
            from io import StringIO

            _bind_tenant(self, app_uuid)
            qs = CodeExecution.objects.select_related("snippet").order_by("-queued_at")
            snippet_uuid = request.GET.get("snippet_uuid")
            if snippet_uuid:
                qs = qs.filter(snippet__object_uuid=snippet_uuid)
            status = request.GET.get("status")
            if status:
                qs = qs.filter(status=status)
            since = request.GET.get("from")
            until = request.GET.get("to")
            if since:
                qs = qs.filter(queued_at__gte=since)
            if until:
                qs = qs.filter(queued_at__lte=until)

            buf = StringIO()
            writer = csv.writer(buf)
            writer.writerow(
                [
                    "execution_uuid",
                    "snippet_uuid",
                    "snippet_name",
                    "snippet_version",
                    "status",
                    "queued_at",
                    "started_at",
                    "ended_at",
                    "duration_ms",
                    "triggered_by",
                    "trigger_kind",
                    "exception_type",
                    "source_hash",
                ]
            )
            for ex in qs.iterator(chunk_size=200):
                writer.writerow(
                    [
                        str(ex.object_uuid),
                        str(ex.snippet.object_uuid),
                        ex.snippet.name if ex.snippet else "",
                        ex.snippet_version,
                        ex.status,
                        ex.queued_at.isoformat() if ex.queued_at else "",
                        ex.started_at.isoformat() if ex.started_at else "",
                        ex.ended_at.isoformat() if ex.ended_at else "",
                        ex.duration_ms or "",
                        ex.triggered_by,
                        ex.trigger_kind,
                        ex.exception_type,
                        ex.source_hash,
                    ]
                )

            resp = HttpResponse(buf.getvalue(), content_type="text/csv")
            resp["Content-Disposition"] = (
                'attachment; filename="codexec-executions.csv"'
            )
            return resp
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: export failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class CodeExecutionLogTailView(ZangoGenericPlatformAPIView, TenantMixin):
    """GET /executions/{id}/log-tail/

    Two modes:
      - Forward (live tail):   ?after_seq=N  → returns lines with seq > N, asc.
      - Backward (page older): ?before_seq=N&limit=M  → returns the latest M lines
        with seq < N, returned in ascending seq order so the client can prepend.

    Caller also gets back the run's current status and an `is_terminal` flag
    so the client knows when to stop polling.
    """

    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 500

    def get(self, request, app_uuid, execution_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                execution = CodeExecution.objects.only("id", "status").get(
                    object_uuid=execution_uuid
                )
            except CodeExecution.DoesNotExist:
                return get_api_response(False, {"message": "execution not found"}, 404)

            before_seq_raw = request.GET.get("before_seq")
            try:
                limit = min(
                    self.MAX_PAGE_SIZE,
                    max(1, int(request.GET.get("limit", self.DEFAULT_PAGE_SIZE))),
                )
            except (TypeError, ValueError):
                limit = self.DEFAULT_PAGE_SIZE

            total_count = CodeExecutionLogLine.objects.filter(
                execution__object_uuid=execution_uuid
            ).count()

            if before_seq_raw is not None:
                # Backward page: latest `limit` rows with seq < before_seq,
                # returned asc so the client can prepend in display order.
                try:
                    before_seq = int(before_seq_raw)
                except (TypeError, ValueError):
                    before_seq = 0
                qs = (
                    CodeExecutionLogLine.objects.filter(
                        execution__object_uuid=execution_uuid, seq__lt=before_seq
                    )
                    .order_by("-seq")
                    .values("seq", "level", "ts", "message")[:limit]
                )
                lines = list(qs)
                lines.reverse()  # ascending for display
            else:
                # Forward live tail.
                try:
                    after_seq = int(request.GET.get("after_seq", 0))
                except (TypeError, ValueError):
                    after_seq = 0
                qs = (
                    CodeExecutionLogLine.objects.filter(
                        execution__object_uuid=execution_uuid, seq__gt=after_seq
                    )
                    .order_by("seq")
                    .values("seq", "level", "ts", "message")[:limit]
                )
                lines = list(qs)

            for row in lines:
                ts = row.get("ts")
                row["ts"] = ts.isoformat() if ts else None

            oldest_seq = lines[0]["seq"] if lines else None
            newest_seq = lines[-1]["seq"] if lines else None

            return get_api_response(
                True,
                {
                    "status": execution.status,
                    "is_terminal": execution.status in TERMINAL_STATUSES,
                    "lines": lines,
                    "oldest_seq": oldest_seq,
                    "newest_seq": newest_seq,
                    "total": total_count,
                    "has_more_before": (
                        oldest_seq is not None and oldest_seq > 1
                    ),
                    # Back-compat for older clients:
                    "next_seq": newest_seq
                    if newest_seq is not None
                    else int(request.GET.get("after_seq", 0)),
                },
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: log-tail failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class CodeExecutionAbortView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST /executions/{id}/abort/  — revoke the celery task and mark aborted."""

    parser_classes = (JSONParser,)

    def post(self, request, app_uuid, execution_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                execution = CodeExecution.objects.get(object_uuid=execution_uuid)
            except CodeExecution.DoesNotExist:
                return get_api_response(False, {"message": "execution not found"}, 404)

            if execution.status in TERMINAL_STATUSES:
                return get_api_response(
                    False,
                    {"message": f"Run is already {execution.status}; cannot abort."},
                    200,
                )

            # Revoke the celery task. terminate=True kills it mid-execution.
            if execution.celery_task_id:
                try:
                    from celery.result import AsyncResult

                    AsyncResult(execution.celery_task_id).revoke(
                        terminate=True, signal="SIGTERM"
                    )
                except Exception:  # noqa: BLE001
                    log.exception(
                        "codexec: failed to revoke celery task %s",
                        execution.celery_task_id,
                    )

            execution.status = ExecStatus.ABORTED
            from django.utils import timezone as _tz

            execution.ended_at = _tz.now()
            if execution.started_at:
                delta = (execution.ended_at - execution.started_at).total_seconds()
                execution.duration_ms = int(delta * 1000)
            execution.exception_type = "AbortedByUser"
            execution.exception_message = (
                _user_label(request)
                + " aborted the run."
            )
            execution.save()

            # Add a system log line so the live tail surfaces the abort cleanly.
            try:
                last = (
                    CodeExecutionLogLine.objects.filter(execution_id=execution.id)
                    .order_by("-seq")
                    .first()
                )
                next_seq = (last.seq + 1) if last else 1
                CodeExecutionLogLine.objects.create(
                    execution_uuid=execution.id,
                    seq=next_seq,
                    level="sys",
                    message="Run aborted by user.",
                )
            except Exception:  # noqa: BLE001
                pass

            return get_api_response(True, {"status": execution.status}, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("codexec: abort failed")
            return get_api_response(False, {"message": str(exc)}, 500)
