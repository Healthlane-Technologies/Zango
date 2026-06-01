"""Preserve Django's LOGGING dict inside the Celery worker.

Celery, by default, replaces the application's logging config with its own
at worker boot. Without this, every line emitted by the worker would go
through Celery's bare formatter — the bracketed tenant prefix added by
the verbose formatter would be lost, and the Platform Logs CloudWatch
connector wouldn't be able to filter celery lines by tenant.

Connecting to the `setup_logging` signal tells Celery "I'll handle
logging, leave it alone." We re-apply settings.LOGGING via dictConfig so
the worker uses the exact same config as the web process.

The signal must be connected on import; that happens via
`apps.py:ready()` calling `import zango.apps.platform_logs.celery_logging`.
"""

from __future__ import annotations

import logging

from celery.signals import setup_logging


logger = logging.getLogger(__name__)


@setup_logging.connect
def configure_logging(*args, **kwargs):
    from logging.config import dictConfig

    from django.conf import settings

    try:
        dictConfig(settings.LOGGING)
    except Exception as exc:
        # Never bring the worker down because of a logging config issue —
        # celery will fall back to its default and we'll see this in stderr.
        logger.exception(
            "platform_logs: failed to apply Django LOGGING in celery worker: %s",
            exc,
        )
