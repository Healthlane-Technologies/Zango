from django.contrib import admin

from zango.apps.platform_logs.models import LogConnectorConfig


@admin.register(LogConnectorConfig)
class LogConnectorConfigAdmin(admin.ModelAdmin):
    list_display = ("environment", "component", "connector", "is_active", "modified_at")
    list_filter = ("environment", "component", "connector", "is_active")
    search_fields = ("environment", "component")
    readonly_fields = ("id", "created_at", "created_by", "modified_at", "modified_by")
