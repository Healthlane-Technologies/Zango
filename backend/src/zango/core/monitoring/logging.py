import sys

from .utils import get_loguru_format, otel_is_enabled


def setup_logging():
    from loguru import logger

    from django.conf import settings

    # Removes the default format
    logger.remove()

    # Add our customized format that adds the tenant context and removes unnecessary initial path for the tenants
    if not otel_is_enabled():
        # Log to console in development environment
        if settings.ENV == "dev":
            logger.add(sys.stderr, format=get_loguru_format, level="DEBUG")
        else:
            # Write to both console (for CloudWatch) and file (for debugging)
            logger.add(sys.stderr, format=get_loguru_format, level="INFO")
            logger.add(
                "log/zango.log",
                format=get_loguru_format,
                level="DEBUG",
                rotation="5 MB",
                retention="1 month",
            )
    else:
        from .telemetry import setup_log_exporting

        setup_log_exporting(logger, get_loguru_format)
