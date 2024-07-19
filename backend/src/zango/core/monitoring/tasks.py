from celery.signals import worker_process_init

from .telemetry import setup_telemetry
from .logging import setup_logging


@worker_process_init.connect
def initialize_otel(**kwargs):
    setup_telemetry(
        add_django_instrumentation=False
        )
    setup_logging()