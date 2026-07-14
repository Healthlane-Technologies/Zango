from rest_framework import serializers

from zango.apps.exports.models import ExportJob


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
    has_file = serializers.SerializerMethodField()

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
            "has_file",
        ]

    def get_kind_label(self, obj):
        return obj.get_kind_display()

    def get_requested_by_email(self, obj):
        if obj.requested_by_id and obj.requested_by:
            return obj.requested_by.email or ""
        return ""

    def get_has_file(self, obj):
        return bool(obj.file and obj.file.name)
