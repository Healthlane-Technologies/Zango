"""Serializers for the Code Execution platform API."""

from urllib.parse import quote as _url_quote

from rest_framework import serializers

from zango.apps.code_execution.models import (
    CodeExecFile,
    CodeExecution,
    CodeSnippet,
    CodeSnippetFile,
)


def _signed_download_url(file_field, original_name: str):
    """Return a download URL that preserves the original filename.

    For S3-backed storage (django-storages), generates a presigned URL with
    `ResponseContentDisposition` set so the browser downloads it with the
    original name. For other backends, falls back to `file.url`.
    """
    if not file_field:
        return None
    safe_ascii = (original_name or "download").encode("ascii", "ignore").decode(
        "ascii"
    ) or "download"
    quoted = _url_quote(original_name or "download")
    disposition = f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{quoted}"
    storage = file_field.storage
    name = file_field.name
    # django-storages' S3Boto3Storage accepts `parameters` for presign config.
    try:
        return storage.url(name, parameters={"ResponseContentDisposition": disposition})
    except TypeError:
        # Storage backend doesn't take parameters — fall back to plain url().
        try:
            return file_field.url
        except Exception:  # noqa: BLE001
            return None
    except Exception:  # noqa: BLE001
        try:
            return file_field.url
        except Exception:  # noqa: BLE001
            return None


# ---------------------------------------------------------------------------
# Snippet
# ---------------------------------------------------------------------------


class CodeSnippetListSerializer(serializers.ModelSerializer):
    last_status = serializers.SerializerMethodField()
    last_run_at = serializers.SerializerMethodField()
    last_run_duration_ms = serializers.SerializerMethodField()
    run_count = serializers.SerializerMethodField()

    class Meta:
        model = CodeSnippet
        fields = (
            "object_uuid",
            "name",
            "slug",
            "description",
            "version",
            "timeout_seconds",
            "is_archived",
            "created_at",
            "modified_at",
            "modified_by",
            "last_status",
            "last_run_at",
            "last_run_duration_ms",
            "run_count",
        )

    def _latest(self, obj):
        cache = getattr(obj, "_latest_exec", None)
        if cache is not None:
            return cache
        cache = obj.executions.order_by("-queued_at").first()
        obj._latest_exec = cache
        return cache

    def get_last_status(self, obj):
        latest = self._latest(obj)
        return latest.status if latest else None

    def get_last_run_at(self, obj):
        latest = self._latest(obj)
        return latest.queued_at.isoformat() if latest and latest.queued_at else None

    def get_last_run_duration_ms(self, obj):
        latest = self._latest(obj)
        return latest.duration_ms if latest else None

    def get_run_count(self, obj):
        return obj.executions.count()


class CodeSnippetDetailSerializer(CodeSnippetListSerializer):
    code = serializers.CharField()
    code_hash = serializers.CharField(read_only=True)

    class Meta(CodeSnippetListSerializer.Meta):
        fields = CodeSnippetListSerializer.Meta.fields + ("code", "code_hash")


class CodeSnippetWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeSnippet
        fields = ("name", "description", "code", "timeout_seconds")

    def validate_timeout_seconds(self, value):
        # 24-hour upper bound covers realistic long-running batch snippets
        # while still capping a rogue snippet from tying up a celery slot
        # indefinitely.
        if value < 5 or value > 86400:
            raise serializers.ValidationError(
                "timeout_seconds must be between 5 and 86400."
            )
        return value


# ---------------------------------------------------------------------------
# Snippet files
# ---------------------------------------------------------------------------


class CodeSnippetFileSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = CodeSnippetFile
        fields = (
            "object_uuid",
            "name",
            "size_bytes",
            "content_type",
            "sha256",
            "created_at",
            "download_url",
        )

    def get_download_url(self, obj):
        return _signed_download_url(obj.file, obj.name)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


class CodeExecFileSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = CodeExecFile
        fields = (
            "object_uuid",
            "kind",
            "name",
            "size_bytes",
            "content_type",
            "sha256",
            "created_at",
            "download_url",
        )

    def get_download_url(self, obj):
        return _signed_download_url(obj.file, obj.name)


class CodeExecutionListSerializer(serializers.ModelSerializer):
    snippet_name = serializers.CharField(source="snippet.name", read_only=True)
    snippet_object_uuid = serializers.UUIDField(source="snippet.object_uuid", read_only=True)

    class Meta:
        model = CodeExecution
        fields = (
            "object_uuid",
            "snippet_object_uuid",
            "snippet_name",
            "snippet_version",
            "status",
            "celery_task_id",
            "queued_at",
            "started_at",
            "ended_at",
            "duration_ms",
            "exception_type",
            "triggered_by",
            "trigger_kind",
        )


class CodeExecutionDetailSerializer(CodeExecutionListSerializer):
    source_snapshot = serializers.CharField()
    source_hash = serializers.CharField()
    stdout = serializers.CharField()
    stderr = serializers.CharField()
    return_value = serializers.JSONField()
    return_value_truncated = serializers.BooleanField()
    exception_message = serializers.CharField()
    exception_traceback = serializers.CharField()
    files = CodeExecFileSerializer(many=True, read_only=True)

    class Meta(CodeExecutionListSerializer.Meta):
        fields = CodeExecutionListSerializer.Meta.fields + (
            "source_snapshot",
            "source_hash",
            "stdout",
            "stderr",
            "return_value",
            "return_value_truncated",
            "exception_message",
            "exception_traceback",
            "files",
        )
