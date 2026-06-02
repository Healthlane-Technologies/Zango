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

        # Install the stdout/stderr proxy once. Idempotent — the proxy
        # itself is a no-op until a request middleware or celery task
        # hook binds a target via stdout_proxy.bind(...).
        try:
            from zango.apps.shared.platform_logs import stdout_proxy

            stdout_proxy.install()
        except Exception:
            # Never fail app boot because of logging plumbing.
            pass

        # task_prerun / task_postrun signals that swap stdout for the
        # duration of each celery task. Imported here so the receivers
        # are registered before Celery starts dispatching.
        try:
            from zango.apps.shared.platform_logs import celery_print_capture  # noqa: F401
        except ImportError:
            pass
