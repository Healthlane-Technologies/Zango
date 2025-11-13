import traceback

from django.db import connection
from django.db.models import Q
from django.utils.decorators import method_decorator

from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.shared.tenancy.models import TenantModel
from zango.apps.tasks.models import AppTask
from zango.core.api import TenantMixin, ZangoGenericPlatformAPIView, get_api_response
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path
from zango.core.utils import get_search_columns

from .serializers import TaskSerializer


@method_decorator(set_app_schema_path, name="dispatch")
class AppTaskView(ZangoGenericPlatformAPIView, ZangoAPIPagination, TenantMixin):
    pagination_class = ZangoAPIPagination

    def get_queryset(self, search, columns={}):
        name_field_query_mappping = {
            "name": "name__icontains",
            "id": "id__icontains",
            "attached_policies": "attached_policies__name__icontains",
            "is_enabled": "is_enabled",
        }
        if columns.get("is_enabled") == "" or columns.get("is_enabled") is None:
            name_field_query_mappping.pop("is_enabled")
        if columns.get("is_enabled") == "true":
            columns["is_enabled"] = True
        if columns.get("is_enabled") == "false":
            columns["is_enabled"] = False
        records = AppTask.objects.filter(is_deleted=False).order_by("-id")
        if search == "" and columns == {}:
            return records
        filters = Q()
        for field_name, query in name_field_query_mappping.items():
            if field_name in columns:
                filters &= Q(**{query: columns.get(field_name)})
            else:
                if search:
                    filters |= Q(**{query: search})
        return records.filter(filters).distinct()

    def get(self, request, app_uuid, task_uuid=None, *args, **kwargs):
        try:
            tenant = self.get_tenant(app_uuid=app_uuid)
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            app_tasks = self.get_queryset(search, columns)
            paginated_tasks = self.paginate_queryset(app_tasks, request, view=self)
            connection.set_tenant(tenant)
            with connection.cursor() as c:
                ws = Workspace.get_plugin_source()
                serializer = TaskSerializer(
                    paginated_tasks,
                    many=True,
                    context={"plugin_source": ws, "tenant": tenant},
                )
            paginated_app_tasks = self.get_paginated_response_data(serializer.data)
            success = True
            response = {
                "tasks": paginated_app_tasks,
                "message": "All app tasks fetched successfully",
            }
            status = 200
        except Exception as e:
            traceback.print_exc()
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
class AppTaskDetailView(ZangoGenericPlatformAPIView, TenantMixin):
    def get(self, request, app_uuid, task_id, *args, **kwargs):
        try:
            tenant = self.get_tenant(app_uuid=app_uuid)
            app_task = AppTask.objects.get(id=task_id)
            tenant = TenantModel.objects.get(uuid=app_uuid)
            connection.set_tenant(tenant)
            with connection.cursor() as c:
                serializer = TaskSerializer(
                    instance=app_task,
                    context={"history": True, "tenant": tenant},
                )
            response = {"task": serializer.data}
            status = 200
            success = True
        except Exception as e:
            response = {"message": str(e)}
            status = 500
            success = False
        return get_api_response(success, response, status)

    def post(self, request, app_uuid, task_id, *args, **kwargs):
        data = request.data
        crontab_exp = data.get("crontab_exp")
        try:
            app_task = AppTask.objects.get(id=task_id)
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
