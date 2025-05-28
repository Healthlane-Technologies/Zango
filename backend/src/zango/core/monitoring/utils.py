import logging
import os

from opentelemetry.sdk._logs import LoggingHandler

from django.conf import settings


def otel_is_enabled():
    """
    Returns the value of the `OTEL_IS_ENABLED` setting from the Django settings.
    """
    return getattr(settings, "OTEL_IS_ENABLED", False)


def otel_export_to_otlp():
    """
    Returns the value of the `OTEL_EXPORT_TO_OTLP` setting from the Django settings.
    """
    return getattr(settings, "OTEL_EXPORT_TO_OTLP", False)


def otel_otlp_endpoint():
    """
    Returns the value of the `OTEL_EXPORTER_OTLP_ENDPOINT` setting from the Django settings.
    """
    return getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")


def otel_otlp_headers():
    """
    Returns the value of the `OTEL_EXPORTER_OTLP_HEADERS` setting from the Django settings.
    """
    return getattr(settings, "OTEL_EXPORTER_OTLP_HEADERS", "")


def otel_otlp_protocol():
    """
    Returns the value of the `OTEL_EXPORTER_PROTOCOL` setting from the Django settings.
    """
    return getattr(settings, "OTEL_EXPORTER_PROTOCOL", "")


def otel_resource_name():
    """
    Returns the value of the `OTEL_RESOURCE_NAME` setting from the Django settings.
    """
    return getattr(settings, "OTEL_RESOURCE_NAME", "Zango")


def otel_collector():
    """
    Returns the value of the `OTEL_COLLECTOR` setting from the Django settings.
    """
    return getattr(settings, "OTEL_COLLECTOR", True)


def _get_tenant_name():
    from django.db import connection

    try:
        tenant_name = connection.tenant.name
    except Exception:
        tenant_name = "FakeTenant"
    return tenant_name


def _get_tenant_filename(original_name):
    if original_name.startswith("pluginbase"):
        result = (
            f"workspaces.{_get_tenant_name()}.{'.'.join(original_name.split('.')[3:])}"
        )
    else:
        result = original_name
    return result


def get_loguru_format(record):
    file_name = _get_tenant_filename(record["name"])

    loguru_format = (
        f"<magenta>{os.getpid()}|</magenta>"
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>|"
        "<level>{level}</level>|"
        f"<cyan>{file_name}</cyan>:"
        "<cyan>{function}</cyan>:"
        "<cyan>{line}</cyan> - "
        "<level>{message}</level>\n"
    )
    return loguru_format


class LogGuruCompatibleLoggerHandler(LoggingHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # The Otel exporter does not handle nested dictionaries. Loguru stores all of
        # the extra log context developers can add on the extra dict. Here unnest
        # them as attributes on the record itself so otel can export them properly.
        for k, v in record.extra.items():
            setattr(record, f"zango.{k}", v)
        del record.extra

        # by default otel doesn't send funcName, rename it so it does.
        setattr(record, "python_function", record.funcName)
        super().emit(record)
