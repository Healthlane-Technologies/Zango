import os
import sys
import uuid
import logging
from pathlib import Path
from loguru import logger
from .settings import OTEL_IS_ENABLED
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs._internal.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics._internal.export import PeriodicExportingMetricReader
from opentelemetry.trace import ProxyTracerProvider


from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry import trace

BASE_DIR = Path(__file__).resolve().parent.parent


class LogGuruCompatibleLoggerHandler(LoggingHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # The Otel exporter does not handle nested dictionaries. Loguru stores all of
        # the extra log context developers can add on the extra dict. Here unnest
        # them as attributes on the record itself so otel can export them properly.
        for k, v in record.extra.items():
            setattr(record, f"zelthy.{k}", v)
        del record.extra

        # by default otel doesn't send funcName, rename it so it does.
        setattr(record, "python_function", record.funcName)
        super().emit(record)


def uuid_sink(record):
    """
    Custom sink function that adds a UUID to each log record.
    """
    # Generate a UUID for the log record
    record["extra"]["uuid"] = str(uuid.uuid4())
    return record


def setup_logging():
    """
    This function configures loguru and optionally sets up open telemetry log exporting
    using a loguru sink.
    """

    # A slightly customized default loguru format which includes the process id.
    loguru_format = (
        "<magenta>{extra[uuid]}|</magenta>"
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>|"
        "[{extra[schema_name]}:testlogapp.zelthy.com][{extra[ip_address]}]|"
        "<level>{level}</level>|"
        "<cyan>{name}</cyan>:"
        "<cyan>{function}</cyan>:"
        "<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Remove the default loguru stderr sink
    logger.remove()
    
    log_folder = os.path.join(BASE_DIR, 'log')
    log_file = os.path.join(log_folder, 'server.log')

    # Check if the log folder exists, if not, create it
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # Check if the log file exists, if not, create it
    if not os.path.exists(log_file):
        with open(log_file, 'a'):
            pass  # Create an empty file

    logger.add(
        log_file, format=loguru_format, level="INFO", filter=uuid_sink
    )
    
    logger.info("Logger setup.")


def setup_telemetry(add_django_instrumentation: bool):
    """
    Sets up logging and when the env var ZELTHY_ENABLE_OTEL is set to any non-blank
    string and this function is called metrics will be setup and sent according to
    the OTEL env vars you can find described at:
    - https://opentelemetry.io/docs/reference/specification/protocol/exporter/
    - https://opentelemetry.io/docs/reference/specification/sdk-environment-variables/

    :param add_django_instrumentation: Enables specific instrumentation for a django
        process that is processing requests. Don't enable this for a celery process etc.
    """

    if OTEL_IS_ENABLED:
        _setup_standard_backend_instrumentation()

        # # Add console exporter
        # console_exporter = ConsoleSpanExporter()
        # span_processor = BatchSpanProcessor(console_exporter)
        # # Initialize the TracerProvider
        # tracer_provider = TracerProvider()

        # # Add the BatchSpanProcessor to the TracerProvider
        # tracer_provider.add_span_processor(span_processor)

        # # Configure the tracer provider
        # trace.set_tracer_provider(tracer_provider)

        print("Configured default backend instrumentation")
        if add_django_instrumentation:
            print("Adding Django request instrumentation also.")
            _setup_django_process_instrumentation()

        print("Telemetry enabled!")
    


def _setup_standard_backend_instrumentation():
    BotocoreInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()
    RedisInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    CeleryInstrumentor().instrument()


def _setup_django_process_instrumentation():
    DjangoInstrumentor().instrument()