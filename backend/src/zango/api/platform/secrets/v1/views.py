from django.db.models import Q
from django.utils.decorators import method_decorator

from zango.apps.secrets.models import SecretsModel
from zango.apps.shared.tenancy.models import TenantModel
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path
from zango.core.time_utils import process_timestamp
from zango.core.utils import get_search_columns

from .serializers import SecretSerializer


@method_decorator(set_app_schema_path, name="dispatch")
class SecretsViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    pagination_class = ZangoAPIPagination

    def process_id(self, id):
        try:
            return int(id)
        except ValueError:
            return None

    def get_queryset(self, search, tenant, columns={}):
        field_name_query_mapping = {
            "is_active": "is_active",
            "key": "key__icontains",
            "id": "id__icontains",
        }
        search_filters = {
            "id": self.process_id,
            "created_at": process_timestamp,
            "modified_at": process_timestamp,
        }
        if columns.get("is_active") == "" or columns.get("is_active") is None:
            field_name_query_mapping.pop("is_active")
        records = SecretsModel.objects.all().order_by("-id")
        if search == "" and columns == {}:
            return records
        filters = Q()
        for field_name, query in field_name_query_mapping.items():
            if search:
                if search_filters.get(field_name, None):
                    value = search_filters[field_name](search)
                    if value is not None:
                        filters |= Q(**{query: value})
                else:
                    filters |= Q(**{query: search})
        records = records.filter(filters).distinct()
        if columns.get("created_at"):
            processed = process_timestamp(columns.get("created_at"), tenant.timezone)
            if processed is not None:
                records = records.filter(
                    created_at__gte=processed["start"], created_at__lte=processed["end"]
                )
        if columns.get("modified_at"):
            processed = process_timestamp(columns.get("modified_at"), tenant.timezone)
            if processed is not None:
                records = records.filter(
                    modified_at__gte=processed["start"],
                    modified_at__lte=processed["end"],
                )
        return records

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            action = request.GET.get("action", None)
            if action == "get_secret_value":
                secret_id = self.process_id(request.GET.get("secret_id", None))
                try:
                    secret = SecretsModel.objects.get(
                        id=secret_id
                    ).get_unencrypted_val()
                    if not secret:
                        return get_api_response(False, "Secret not found", 404)
                    return get_api_response(True, {"secret_value": secret}, 200)
                except Exception as e:
                    return get_api_response(False, {"message": str(e)}, 500)
            tenant = TenantModel.objects.get(uuid=app_uuid)
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            secrets = self.get_queryset(search, tenant, columns)
            paginated_secrets = self.paginate_queryset(secrets, request, view=self)
            serializer = SecretSerializer(
                paginated_secrets, many=True, context={"tenant": tenant}
            )
            paginated_secrets = self.get_paginated_response_data(serializer.data)
            success = True
            response = {
                "secrets": paginated_secrets,
                "message": "All secrets fetched successfully",
            }
            status = 200
        except Exception as e:
            import traceback

            traceback.print_exc()

            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)

    def post(self, request, *args, **kwargs):
        try:
            secret = SecretSerializer(data=request.data)
            if secret.is_valid():
                secret = secret.save()
                success = True
                response = {
                    "message": "Secret created successfully",
                    "secret_id": secret.id,
                }
                status = 200
            else:
                success = False
                if secret.errors:
                    error_messages = [
                        error[0] for field_name, error in secret.errors.items()
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
            secret_id = self.process_id(request.GET.get("secret_id", None))
            secret_obj = SecretsModel.objects.get(id=secret_id)
            secret = SecretSerializer(
                instance=secret_obj, data=request.data, partial=True
            )
            if secret.is_valid():
                secret = secret.save()
                success = True
                response = {
                    "message": "Secret updated successfully",
                    "secret_id": secret.id,
                }
                status = 200
            else:
                success = False
                if secret.errors:
                    error_messages = [
                        error[0] for field_name, error in secret.errors.items()
                    ]
                    error_message = ", ".join(error_messages)
                else:
                    error_message = "Invalid data"
                response = {"message": error_message}
                status = 400
        except Exception as e:
            import traceback

            traceback.print_exc()
            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)

    def delete(self, request, *args, **kwargs):
        try:
            secret_id = self.process_id(request.GET.get("secret_id", None))
            secret = SecretsModel.objects.get(id=secret_id)
            if secret.is_active:
                return get_api_response(
                    False,
                    {"message": "Secret is active, deactivate before deleting"},
                    400,
                )
            secret.delete()
            success = True
            response = {"message": "Secret deleted successfully"}
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)
