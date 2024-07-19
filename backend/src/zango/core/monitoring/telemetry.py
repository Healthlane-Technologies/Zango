
from opentelemetry import metrics, trace

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
# from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry import trace
from loguru import logger

from .celery_instrument import ZangoCeleryInstrumentor
from .utils import otel_is_enabled, otel_export_to_otlp, otel_otlp_endpoint, \
    otel_otlp_headers, otel_resource_name   

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
        _setup_standard_backend_instrumentation()
        
        resource = Resource.create(attributes={
                "service.name": otel_resource_name()
            })
        
        # Add console exporter
        if otel_export_to_otlp():            
            endpoint = otel_otlp_endpoint()
            if endpoint:
                headers = otel_otlp_headers()
                exporter = OTLPSpanExporter(
                                endpoint=endpoint,
                                headers=headers
                                )
                logger.info(f"Exported set to {endpoint}")
            else:
                logger.info(f"OTLP endpoint not provided. Switching to console exporter")
                exporter = ConsoleSpanExporter()
        else:
            exporter = ConsoleSpanExporter()
            logger.info(f"Otel exporting to console!")
        span_processor = BatchSpanProcessor(exporter)
        # Initialize the TracerProvider
        tracer_provider = TracerProvider(resource=resource)

        # Add the BatchSpanProcessor to the TracerProvider
        tracer_provider.add_span_processor(span_processor)

        # Configure the tracer provider
        trace.set_tracer_provider(tracer_provider)

        logger.info("Configured default backend instrumentation")
        if add_django_instrumentation:
            logger.info("Adding Django request instrumentation also.")
            _setup_django_process_instrumentation()

        logger.info("Telemetry enabled!")
    else:
        logger.info("Telemetry not enabled!")



def _setup_standard_backend_instrumentation():
    BotocoreInstrumentor().instrument()
    Psycopg2Instrumentor().instrument(skip_dep_check=True)
    RedisInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    ZangoCeleryInstrumentor().instrument()


def _setup_django_process_instrumentation():
    DjangoInstrumentor().instrument()