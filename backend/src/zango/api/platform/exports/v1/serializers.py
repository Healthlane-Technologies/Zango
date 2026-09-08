from urllib.parse import quote as _url_quote

from rest_framework import serializers

from zango.apps.exports.models import ExportJob


def _content_disposition(filename: str) -> str:
    safe_ascii = filename.encode("ascii", "ignore").decode("ascii") or "export.csv"
    quoted = _url_quote(filename)
    return f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{quoted}"


def _download_url(file_field, filename: str) -> str | None:
    """Return a URL the browser can hit directly to download the CSV.

    For S3 storage, generate a presigned URL with
    `ResponseContentDisposition=attachment` baked in so the file downloads
    instead of rendering inline. For local storage, return the plain URL —
    the client uses <a download> to force the filename.
    """
    if not (file_field and file_field.name):
        return None
    disposition = _content_disposition(filename or "export.csv")
    try:
        return file_field.storage.url(
            file_field.name,
            parameters={
                "ResponseContentDisposition": disposition,
                "ResponseContentType": "text/csv",
            },
        )
    except TypeError:
        # Storage backend (e.g. FileSystemStorage) doesn't accept `parameters`.
        try:
            return file_field.url
        except Exception:
            return None
    except Exception:
        try:
            return file_field.url
        except Exception:
            return None


class ExportJobSerializer(serializers.ModelSerializer):
    """Read-side representation of an ExportJob."""

    object_uuid = serializers.UUIDField(read_only=True)
    kind = serializers.CharField(read_only=True)
    kind_label = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    filters = serializers.JSONField(read_only=True)
    filters_summary = serializers.CharField(read_only=True)
    row_count = serializers.IntegerField(read_only=True)
    filename = serializers.CharField(read_only=True)
    size_bytes = serializers.IntegerField(read_only=True)
    error_message = serializers.CharField(read_only=True)
    requested_by_email = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ExportJob
        fields = [
            "object_uuid",
            "kind",
            "kind_label",
            "status",
            "filters",
            "filters_summary",
            "row_count",
            "filename",
            "size_bytes",
            "error_message",
            "requested_by_email",
            "created_at",
            "started_at",
            "completed_at",
            "file_url",
        ]

    def get_kind_label(self, obj):
        return obj.get_kind_display()

    def get_requested_by_email(self, obj):
        if obj.requested_by_id and obj.requested_by:
            return obj.requested_by.email or ""
        return ""

    def get_file_url(self, obj):
        return _download_url(obj.file, obj.filename)
