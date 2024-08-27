from celery.signals import worker_process_init


@worker_process_init.connect
def initialize_otel(**kwargs):
    """
    Initializes OpenTelemetry (OTel) for worker processes.

    This function is connected to the `worker_process_init` signal and is called
    when a worker process starts. It sets up the telemetry and logging
    configurations.
    """
    from .logging import setup_logging
    from .telemetry import setup_telemetry

    setup_telemetry(add_django_instrumentation=False)
    setup_logging()
