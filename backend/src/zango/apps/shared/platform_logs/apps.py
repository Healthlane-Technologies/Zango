from django.apps import AppConfig


class PlatformLogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zango.apps.shared.platform_logs"
    verbose_name = "Platform Logs"

    def ready(self):
        # Wire Celery's setup_logging signal so worker boot doesn't
        # discard Django's tenant-aware LOGGING dict. Implemented in P4.
        try:
            from zango.apps.shared.platform_logs import celery_logging  # noqa: F401
        except ImportError:
            pass
