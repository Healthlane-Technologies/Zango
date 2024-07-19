import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1

# Need to verify this - recommended in https://opentelemetry-python.readthedocs.io/en/latest/examples/fork-process-model/README.html

# from zango.core.monitoring.telemetry import setup_telemetry

# def post_fork(server, worker):
#     setup_telemetry(add_django_instrumentation=True)