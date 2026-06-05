import logging

from django.apps import AppConfig


_boot_logger = logging.getLogger(__name__)


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

        # `manage.py runserver` doesn't go through wsgi.py / asgi.py, so
        # the loguru sink with our tenant-prefix format never gets
        # installed in local dev. Call setup_logging() here too — it's
        # idempotent (logger.remove() first), so re-invocation from
        # wsgi/asgi after this is a no-op.
        #
        # If setup_logging() raises, loguru is left in a sinkless state
        # (`logger.remove()` ran but no `logger.add()` followed). Without
        # an explicit log of the failure, every workspace `logger.info()`
        # call would silently drop and we'd notice only in CloudWatch.
        # Surface the exception through stdlib logging (which is wired
        # up via Django's LOGGING dict and is independent of loguru) so
        # the boot transcript records it.
        try:
            from zango.core.monitoring import setup_logging

            setup_logging()
        except Exception:
            _boot_logger.exception(
                "platform_logs: setup_logging() failed during ready(); "
                "loguru may have no active sink. Workspace logger calls "
                "will be silently dropped until this is repaired."
            )

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
