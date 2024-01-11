from functools import partial
from celery import shared_task, current_task
from django.db import connection


@shared_task
def zelthy_task_executor(tenant_name, task_name, *args, **kwargs):
    from zelthy.apps.dynamic_models.workspace.base import Workspace
    from zelthy.apps.shared.tenancy.models import TenantModel
    from zelthy.apps.tasks.models import AppTask

    tenant = TenantModel.objects.get(name=tenant_name)

    connection.set_tenant(tenant)
    with connection.cursor() as c:
        task_obj = AppTask.objects.get(name=task_name)

        ws = Workspace(connection.tenant, request=None, as_systemuser=True)
        ws.ready()

        task_module = task_obj.name.rsplit(".", 1)[0]
        func_name = task_obj.name.rsplit(".", 1)[1]
        _task = ws.plugin_source.load_plugin(f"{task_module}")
        task_fun = getattr(_task, func_name)
        return task_fun(*args, **kwargs)


def zelthy_task(task_fun, *args, **kwargs):
    def get_zelthy_task_executor(**options):
        return zelthy_task_executor

    def original_function(*args, **kwargs):
        return task_fun(*args, **kwargs)

    task_executor = get_zelthy_task_executor()
    task_executor.original_function = original_function

    return task_executor
