from django.contrib import admin

from .models import CodeExecFile, CodeExecution, CodeSnippet, CodeSnippetFile


@admin.register(CodeSnippet)
class CodeSnippetAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "version", "is_archived", "modified_at")
    search_fields = ("name", "slug")
    list_filter = ("is_archived",)
    readonly_fields = ("id", "code_hash", "created_at", "modified_at")


@admin.register(CodeSnippetFile)
class CodeSnippetFileAdmin(admin.ModelAdmin):
    list_display = ("name", "snippet", "size_bytes", "content_type", "created_at")
    search_fields = ("name", "snippet__name")
    readonly_fields = ("id", "sha256", "size_bytes", "created_at", "modified_at")


@admin.register(CodeExecution)
class CodeExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "snippet",
        "status",
        "duration_ms",
        "triggered_by",
        "queued_at",
    )
    list_filter = ("status", "trigger_kind")
    search_fields = ("id", "snippet__name", "triggered_by")
    readonly_fields = (
        "id",
        "source_hash",
        "celery_task_id",
        "queued_at",
        "started_at",
        "ended_at",
        "duration_ms",
        "created_at",
        "modified_at",
    )


@admin.register(CodeExecFile)
class CodeExecFileAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "execution", "size_bytes", "created_at")
    list_filter = ("kind",)
    search_fields = ("name", "execution__id")
    readonly_fields = ("id", "sha256", "size_bytes", "created_at", "modified_at")
