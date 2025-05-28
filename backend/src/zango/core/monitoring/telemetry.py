from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as OTLPSpanExporterGRPC,
)
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs._internal.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import ProxyTracerProvider

from .celery_instrument import ZangoCeleryInstrumentor
from .utils import (
    LogGuruCompatibleLoggerHandler,
    otel_collector,
    otel_export_to_otlp,
    otel_is_enabled,
    otel_otlp_endpoint,
    otel_otlp_headers,
    otel_resource_name,
)


tracer = trace.get_tracer(__name__)


def setup_telemetry(add_django_instrumentation: bool):
    """
    Sets up logging and when the env var OTEL_IS_ENABLED is set to any
    non-blank string and this function is called metrics will be setup
    and sent according as per the bellow env vars:
    - OTEL_EXPORT_TO_OTLP: Export otel to OTLP else send to console
    - OTEL_EXPORTER_OTLP_ENDPOINT: Endpoint URL of OTLP. Defaults to
    - OTEL_EXPORTER_OTLP_HEADERS: Authorization header of OTLP
    - OTEL_RESOURCE_NAME: service.name of Resource. Defaults to Zango

    :param add_django_instrumentation: Enables specific instrumentation for a django
        process that is processing requests. Don't enable this for a celery process etc.
    """

    if otel_is_enabled():
        existing_provider = trace.get_tracer_provider()
        if not isinstance(existing_provider, ProxyTracerProvider):
            print("Provider already configured not reconfiguring...")
        else:
            resource = Resource.create(
                attributes={"service.name": otel_resource_name()}
            )

            if otel_export_to_otlp():
                endpoint = otel_otlp_endpoint()
                if endpoint:
                    headers = otel_otlp_headers()
                    if otel_collector():
                        exporter = OTLPSpanExporter(
                            endpoint=f"{endpoint}/v1/traces", headers=headers
                        )
                    else:
                        exporter = OTLPSpanExporterGRPC(
                            endpoint=endpoint, headers=headers
                        )
                    print(f"Exporter set to {endpoint}")
                else:
                    print("OTLP endpoint not provided. Switching to console exporter")
                    exporter = ConsoleSpanExporter()
            else:  # Add console exporter
                exporter = ConsoleSpanExporter()
                print("Otel exporting to console!")

            span_processor = BatchSpanProcessor(exporter)
            # Initialize the TracerProvider
            tracer_provider = TracerProvider(resource=resource)

            # Add the BatchSpanProcessor to the TracerProvider
            tracer_provider.add_span_processor(span_processor)

            # Configure the tracer provider
            trace.set_tracer_provider(tracer_provider)

            _setup_standard_backend_instrumentation()

            print("Configured default backend instrumentation")

            if add_django_instrumentation:
                print("Adding Django request instrumentation also.")
                _setup_django_process_instrumentation()

            print("Telemetry enabled!")
    else:
        print("Telemetry not enabled!")


def setup_log_exporting(logger, format):
    resource = Resource.create(attributes={"service.name": otel_resource_name()})

    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    exporter = OTLPLogExporter(endpoint=f"{otel_otlp_endpoint()}/v1/logs")
    handler = LogGuruCompatibleLoggerHandler(
        level="DEBUG",
        logger_provider=logger_provider,
    )
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    logger.add(handler, format=format, level="DEBUG")
    logger.info("Logger open telemetry exporting setup.")


def _setup_standard_backend_instrumentation():
    BotocoreInstrumentor().instrument()
    Psycopg2Instrumentor().instrument(skip_dep_check=True)
    RedisInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    ZangoCeleryInstrumentor().instrument()


def _setup_django_process_instrumentation():
    DjangoInstrumentor().instrument()
