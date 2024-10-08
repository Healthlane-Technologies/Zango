from celery import shared_task

from django.db import connection


@shared_task
def zango_task_executor(tenant_name, task_name, *args, **kwargs):
    from zango.apps.dynamic_models.workspace.base import Workspace
    from zango.apps.shared.tenancy.models import TenantModel
    from zango.apps.tasks.models import AppTask

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


def zango_task(task_fun, *args, **kwargs):
    def get_zango_task_executor(**options):
        return zango_task_executor

    def original_function(*args, **kwargs):
        return task_fun(*args, **kwargs)

    task_executor = get_zango_task_executor()
    task_executor.original_function = original_function

    return task_executor
