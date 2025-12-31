from rest_framework import serializers

from zango.apps.codeexec.guards import validate_imports
from zango.apps.codeexec.models import ZangoAdminCodeExecutionModel
from zango.apps.shared.platformauth.models import PlatformUserModel
from zango.core.utils import get_datetime_str_in_tenant_timezone


class CodeExecSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    modified_at = serializers.SerializerMethodField()
    author_name = serializers.CharField(source="author.name", read_only=True)
    id = serializers.IntegerField(read_only=True)
    slug_code = serializers.UUIDField(read_only=True)

    class Meta:
        model = ZangoAdminCodeExecutionModel
        fields = [
            "id",
            "slug_code",
            "name",
            "description",
            "code",
            "author",
            "author_name",
            "execution_history",
            "created_at",
            "modified_at",
        ]

    def get_created_at(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.created_at, self.context.get("tenant")
        )

    def get_modified_at(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.modified_at, self.context.get("tenant")
        )

    def validate_code(self, value):
        """Validate code for restricted imports"""
        if value:
            not_allowed_imports = validate_imports(value)
            if not_allowed_imports:
                error_messages = [
                    f"Line {item['line']}: {item['error']}"
                    for item in not_allowed_imports
                ]
                raise serializers.ValidationError(", ".join(error_messages))
        return value

    def create(self, validated_data):
        """Set author to current user when creating"""
        request = self.context.get("request")
        if request and request.user:
            try:
                validated_data["author"] = PlatformUserModel.objects.get(
                    id=request.user.id
                )
            except PlatformUserModel.DoesNotExist:
                raise serializers.ValidationError("Invalid user")
        return super().create(validated_data)


class CodeExecExecutionHistorySerializer(serializers.Serializer):
    """Serializer for code execution history details"""

    start_time = serializers.CharField(read_only=True)
    end_time = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)
    logger = serializers.JSONField(read_only=True, required=False)
    traceback = serializers.CharField(read_only=True, required=False)
