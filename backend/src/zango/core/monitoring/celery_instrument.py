from loguru import logger
from opentelemetry import trace
from opentelemetry.instrumentation.celery import (
    _TASK_RUN,
    CeleryInstrumentor,
    celery_getter,
    utils,
)
from opentelemetry.propagate import extract


class ZangoCeleryInstrumentor(CeleryInstrumentor):
    """
    A custom Celery instrumentor for the Zango framework that overrides the default operation name for the the tasks implemented in
    tenants. All tasks implemented in tenants are handled by 'zango.core.tasks.zango_task_executor' but
    we want to have the actual task name shown in the operation name in the traces.
    """

    def _trace_prerun(self, *args, **kwargs):
        task = utils.retrieve_task(kwargs)
        task_id = utils.retrieve_task_id(kwargs)

        if task is None or task_id is None:
            return

        self.update_task_duration_time(task_id)
        request = task.request
        tracectx = extract(request, getter=celery_getter) or None

        logger.debug("prerun signal start task_id=%s", task_id)
        if task.name == "zango.core.tasks.zango_task_executor":
            operation_name = f"{_TASK_RUN}/{kwargs['args'][0]}-{kwargs['args'][1]}"
        else:
            operation_name = f"{_TASK_RUN}/{task.name}"
        span = self._tracer.start_span(
            operation_name, context=tracectx, kind=trace.SpanKind.CONSUMER
        )

        activation = trace.use_span(span, end_on_exit=True)
        activation.__enter__()  # pylint: disable=E1101
        utils.attach_span(task, task_id, (span, activation))
