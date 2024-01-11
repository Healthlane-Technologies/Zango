from django.utils.decorators import method_decorator
from django.db import connection

from zelthy.core.api import get_api_response, ZelthyGenericPlatformAPIView
from zelthy.apps.tasks.models import AppTask
from zelthy.core.api.utils import ZelthyAPIPagination
from zelthy.core.common_utils import set_app_schema_path
from zelthy.apps.dynamic_models.workspace.base import Workspace
from zelthy.apps.shared.tenancy.models import TenantModel


from .serializers import TaskSerializer


@method_decorator(set_app_schema_path, name="dispatch")
class AppTaskView(ZelthyGenericPlatformAPIView, ZelthyAPIPagination):
    pagination_class = ZelthyAPIPagination

    def get(self, request, app_uuid, task_uuid=None, *args, **kwargs):
        try:
            app_tasks = AppTask.objects.filter(is_deleted=False).order_by("-id")
            paginated_tasks = self.paginate_queryset(app_tasks, request, view=self)
            serializer = TaskSerializer(paginated_tasks, many=True)
            paginated_app_tasks = self.get_paginated_response_data(serializer.data)
            success = True
            response = {
                "tasks": paginated_app_tasks,
                "message": "All app tasks fetched successfully",
            }
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)

    def post(self, request, app_uuid, *args, **kwargs):
        try:
            tenant = TenantModel.objects.get(uuid=app_uuid)
            connection.set_tenant(tenant)
            with connection.cursor() as c:
                ws = Workspace(connection.tenant, request=None, as_systemuser=True)
                ws.ready()
                ws.sync_tasks(tenant.name)
            response = {"message": "Tasks synced successfully"}
            status = 200
            success = True
        except Exception as e:
            response = {"message": str(e)}
            status = 500
            success = False
        return get_api_response(success, response, status)


@method_decorator(set_app_schema_path, name="dispatch")
class AppTaskDetailView(ZelthyGenericPlatformAPIView):
    def get(self, request, app_uuid, task_uuid, *args, **kwargs):
        try:
            app_task = AppTask.objects.get(id=task_uuid)
            serializer = TaskSerializer(instance=app_task)
            response = {"task": serializer.data}
            status = 200
            success = True
        except Exception as e:
            response = {"message": str(e)}
            status = 500
            success = False
        return get_api_response(success, response, status)

    def post(self, request, app_uuid, task_uuid, *args, **kwargs):
        data = request.data
        crontab_exp = data.get("crontab_exp")
        try:
            app_task = AppTask.objects.get(id=task_uuid)
            serializer = TaskSerializer(
                instance=app_task,
                data=request.data,
                partial=True,
                context={"cronexp": crontab_exp},
            )
            if serializer.is_valid():
                serializer.save()
                response = {"message": "Task updated successfully"}
                status = 200
                success = True
            else:
                response = {"message": serializer.errors}
                status = 400
                success = False
        except Exception as e:
            response = {"message": str(e)}
            status = 500
            success = False
        return get_api_response(success, response, status)
