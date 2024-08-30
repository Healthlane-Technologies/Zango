import multiprocessing
import os


bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1


# https://opentelemetry-python.readthedocs.io/en/latest/examples/fork-process-model/README.html
def post_fork(server, worker):
    project_name = os.environ.get("PROJECT_NAME", "zango_project")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_name}.settings")
    from zango.core.monitoring.telemetry import setup_telemetry

    setup_telemetry(add_django_instrumentation=True)
