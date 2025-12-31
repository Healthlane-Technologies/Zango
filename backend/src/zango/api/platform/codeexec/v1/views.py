from django.db.models import Q
from django.utils.decorators import method_decorator

from zango.apps.codeexec.models import ZangoAdminCodeExecutionModel
from zango.apps.codeexec.tasks import zelthy_code_execution_task
from zango.apps.shared.tenancy.models import TenantModel
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path
from zango.core.time_utils import process_timestamp
from zango.core.utils import get_search_columns

from .serializers import CodeExecExecutionHistorySerializer, CodeExecSerializer


@method_decorator(set_app_schema_path, name="dispatch")
class CodeExecViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    pagination_class = ZangoAPIPagination

    def process_id(self, id):
        if id is None:
            return None
        try:
            return int(id)
        except (ValueError, TypeError):
            return None

    def get_queryset(self, search, tenant, columns={}):
        field_name_query_mapping = {
            "name": "name__icontains",
            "description": "description__icontains",
            "id": "id__icontains",
        }
        search_filters = {
            "id": self.process_id,
            "created_at": process_timestamp,
            "modified_at": process_timestamp,
        }
        records = ZangoAdminCodeExecutionModel.objects.all().order_by("-id")
        if search == "" and columns == {}:
            return records
        filters = Q()
        for field_name, query in field_name_query_mapping.items():
            if search:
                if search_filters.get(field_name, None):
                    try:
                        value = search_filters[field_name](search)
                        if value is not None:
                            filters |= Q(**{query: value})
                    except (ValueError, TypeError, Exception):
                        # Skip invalid search values
                        continue
                else:
                    filters |= Q(**{query: search})
        records = records.filter(filters).distinct()
        if columns.get("created_at"):
            try:
                processed = process_timestamp(
                    columns.get("created_at"), tenant.timezone
                )
                if processed is not None:
                    records = records.filter(
                        created_at__gte=processed["start"],
                        created_at__lte=processed["end"],
                    )
            except (ValueError, TypeError, Exception):
                pass
        if columns.get("modified_at"):
            try:
                processed = process_timestamp(
                    columns.get("modified_at"), tenant.timezone
                )
                if processed is not None:
                    records = records.filter(
                        modified_at__gte=processed["start"],
                        modified_at__lte=processed["end"],
                    )
            except (ValueError, TypeError, Exception):
                pass
        return records

    def get(self, request, *args, **kwargs):
        try:
            action = request.GET.get("action", None)
            app_uuid = kwargs.get("app_uuid")
            codeexec_id = self.process_id(request.GET.get("codeexec_id", None))

            if action == "get_execution_history":
                try:
                    codeexec = ZangoAdminCodeExecutionModel.objects.get(id=codeexec_id)
                    execution_history = codeexec.execution_history or []
                    serializer = CodeExecExecutionHistorySerializer(
                        execution_history, many=True
                    )
                    return get_api_response(
                        True,
                        {
                            "execution_history": serializer.data,
                            "message": "Execution history fetched successfully",
                        },
                        200,
                    )
                except ZangoAdminCodeExecutionModel.DoesNotExist:
                    return get_api_response(False, "Code execution not found", 404)
                except Exception as e:
                    return get_api_response(False, {"message": str(e)}, 500)

            # If codeexec_id is provided, return single codeexec details
            if codeexec_id:
                try:
                    codeexec = ZangoAdminCodeExecutionModel.objects.get(id=codeexec_id)
                    tenant = TenantModel.objects.get(uuid=app_uuid)
                    serializer = CodeExecSerializer(
                        codeexec, context={"tenant": tenant, "request": request}
                    )
                    return get_api_response(
                        True,
                        {
                            "codeexec": serializer.data,
                            "message": "Code execution fetched successfully",
                        },
                        200,
                    )
                except ZangoAdminCodeExecutionModel.DoesNotExist:
                    return get_api_response(False, "Code execution not found", 404)
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    return get_api_response(False, {"message": str(e)}, 500)

            tenant = TenantModel.objects.get(uuid=app_uuid)
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            try:
                codeexecs = self.get_queryset(search, tenant, columns)
            except Exception as e:
                # If get_queryset fails, return all records
                import traceback

                traceback.print_exc()
                codeexecs = ZangoAdminCodeExecutionModel.objects.all().order_by("-id")

            try:
                paginated_codeexecs = self.paginate_queryset(
                    codeexecs, request, view=self
                )
                if paginated_codeexecs is None:
                    # If paginate_queryset returns None, use all records
                    paginated_codeexecs = codeexecs
                    serializer = CodeExecSerializer(
                        paginated_codeexecs,
                        many=True,
                        context={"tenant": tenant, "request": request},
                    )
                    response = {
                        "codeexecs": {
                            "total_records": len(list(paginated_codeexecs)),
                            "total_pages": 1,
                            "records": serializer.data,
                        },
                        "message": "Code executions fetched successfully",
                    }
                else:
                    serializer = CodeExecSerializer(
                        paginated_codeexecs,
                        many=True,
                        context={"tenant": tenant, "request": request},
                    )
                    response = {
                        "codeexecs": self.get_paginated_response_data(serializer.data),
                        "message": "Code executions fetched successfully",
                    }
                success = True
                status = 200
            except Exception as e:
                import traceback

                traceback.print_exc()
                success = False
                response = {"message": str(e)}
                status = 500
        except Exception as e:
            import traceback

            traceback.print_exc()

            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)

    def post(self, request, *args, **kwargs):
        try:
            codeexec = CodeExecSerializer(
                data=request.data, context={"request": request}
            )
            if codeexec.is_valid():
                codeexec_obj = codeexec.save()
                success = True
                response = {
                    "message": "Code execution created successfully",
                    "codeexec_id": codeexec_obj.id,
                    "slug_code": str(codeexec_obj.slug_code),
                }
                status = 200
            else:
                success = False
                if codeexec.errors:
                    error_messages = [
                        error[0] for field_name, error in codeexec.errors.items()
                    ]
                    error_message = ", ".join(error_messages)
                else:
                    error_message = "Invalid data"
                response = {"message": error_message}
                status = 400
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        try:
            codeexec_id = self.process_id(request.GET.get("codeexec_id", None))
            if not codeexec_id:
                return get_api_response(False, "codeexec_id is required", 400)
            codeexec_obj = ZangoAdminCodeExecutionModel.objects.get(id=codeexec_id)
            codeexec = CodeExecSerializer(
                instance=codeexec_obj,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if codeexec.is_valid():
                codeexec_obj = codeexec.save()
                success = True
                response = {
                    "message": "Code execution updated successfully",
                    "codeexec_id": codeexec_obj.id,
                }
                status = 200
            else:
                success = False
                if codeexec.errors:
                    error_messages = [
                        error[0] for field_name, error in codeexec.errors.items()
                    ]
                    error_message = ", ".join(error_messages)
                else:
                    error_message = "Invalid data"
                response = {"message": error_message}
                status = 400
        except ZangoAdminCodeExecutionModel.DoesNotExist:
            success = False
            response = {"message": "Code execution not found"}
            status = 404
        except Exception as e:
            import traceback

            traceback.print_exc()
            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)

    def delete(self, request, *args, **kwargs):
        try:
            codeexec_id = self.process_id(request.GET.get("codeexec_id", None))
            if not codeexec_id:
                return get_api_response(False, "codeexec_id is required", 400)
            codeexec = ZangoAdminCodeExecutionModel.objects.get(id=codeexec_id)
            codeexec.delete()
            success = True
            response = {"message": "Code execution deleted successfully"}
            status = 200
        except ZangoAdminCodeExecutionModel.DoesNotExist:
            success = False
            response = {"message": "Code execution not found"}
            status = 404
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)


@method_decorator(set_app_schema_path, name="dispatch")
class CodeExecExecuteViewAPIV1(ZangoGenericPlatformAPIView):
    """View to execute code for a given ZangoAdminCodeExecutionModel"""

    def process_id(self, id):
        if id is None:
            return None
        try:
            return int(id)
        except (ValueError, TypeError):
            return None

    def post(self, request, *args, **kwargs):
        try:
            codeexec_id = self.process_id(request.GET.get("codeexec_id", None))
            app_uuid = kwargs.get("app_uuid")

            if not codeexec_id:
                return get_api_response(False, "Invalid codeexec_id", 400)

            try:
                codeexec = ZangoAdminCodeExecutionModel.objects.get(id=codeexec_id)
            except ZangoAdminCodeExecutionModel.DoesNotExist:
                return get_api_response(False, "Code execution not found", 404)

            # Get tenant information
            tenant = TenantModel.objects.get(uuid=app_uuid)

            # Initialize execution history if not present
            if not codeexec.execution_history:
                codeexec.execution_history = []

            # Trigger async task to execute code
            zelthy_code_execution_task.delay(tenant.name, codeexec_id)

            success = True
            response = {
                "message": "Code execution started",
                "codeexec_id": codeexec_id,
                "slug_code": str(codeexec.slug_code),
            }
            status = 202  # Accepted

        except Exception as e:
            import traceback

            traceback.print_exc()
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)
