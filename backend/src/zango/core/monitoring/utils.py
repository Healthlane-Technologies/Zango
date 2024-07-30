import os
import logging
from opentelemetry.sdk._logs import LoggingHandler


def otel_is_enabled():
    """Returns True if env var OTEL_IS_ENABLED is set to any non
    blank string
    """
    if os.getenv("OTEL_IS_ENABLED", "false").strip() == "true":
        return True
    return False


def otel_export_to_otlp():
    """Returns True if env var OTEL_EXPORT_TO_OTLP is set to any non
    blank string
    """
    if os.getenv("OTEL_EXPORT_TO_OTLP", "false").strip() == "true":
        return True
    return False


def otel_otlp_endpoint():
    return str(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))


def otel_otlp_headers():
    return str(os.getenv("OTEL_EXPORTER_OTLP_HEADERS", ""))


def otel_otlp_protocol():
    return str(os.getenv("OTEL_EXPORTER_PROTOCOL", ""))


def otel_resource_name():
    return str(os.getenv("OTEL_RESOURCE_NAME", "Zango"))


def _get_tenant_name():
    from django.db import connection

    try:
        tenant_name = connection.tenant.name
    except Exception as e:
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
