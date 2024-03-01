import traceback

from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db import connection

from zelthy.core.api import (
    get_api_response,
    ZelthyGenericPlatformAPIView,
)
from zelthy.core.utils import get_search_columns
from zelthy.apps.shared.tenancy.models import TenantModel
from zelthy.apps.shared.tenancy.utils import TIMEZONES, DATETIMEFORMAT
from zelthy.apps.permissions.models import PolicyModel, PermissionsModel
from zelthy.core.common_utils import set_app_schema_path
from zelthy.core.api.utils import ZelthyAPIPagination
from zelthy.core.permissions import IsPlatformUserAllowedApp
from zelthy.apps.appauth.models import UserRoleModel
from zelthy.apps.dynamic_models.workspace.base import Workspace


from .serializers import PolicySerializer


@method_decorator(set_app_schema_path, name="dispatch")
class PolicyViewAPIV1(ZelthyGenericPlatformAPIView, ZelthyAPIPagination):
    pagination_class = ZelthyAPIPagination
    permission_classes = (IsPlatformUserAllowedApp,)

    def get_queryset(self, search, columns={}):
        field_name_query_mapping = {
            "policy_name": "name__icontains",
            "description": "description__icontains",
            "policy_id": "id__icontains",
        }
        records = PolicyModel.objects.all().order_by("-modified_at")
        if search == "" and columns == {}:
            return records
        filters = Q()
        for field_name, query in field_name_query_mapping.items():
            if field_name in columns:
                filters &= Q(**{query: columns.get(field_name)})
            else:
                if search:
                    filters |= Q(**{query: search})
        return records.filter(filters).distinct()

    def get_dropdown_options(self):
        options = {}
        options["roles"] = [
            {"id": t.id, "label": t.name} for t in UserRoleModel.objects.all()
        ]
        return options

    def get(self, request, *args, **kwargs):
        try:
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            policies = self.get_queryset(search, columns)
            paginated_roles = self.paginate_queryset(policies, request, view=self)
            serializer = PolicySerializer(paginated_roles, many=True)
            paginated_roles_data = self.get_paginated_response_data(serializer.data)

            success = True
            response = {
                "policies": paginated_roles_data,
                "message": "All policies fetched successfully",
            }
            if request.GET.get("include_dropdown_options"):
                response["dropdown_options"] = self.get_dropdown_options()
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def post(self, request, app_uuid, *args, **kwargs):
        data = request.data
        action = request.GET.get("action", None)
        if action == "sync_policies":
            try:
                tenant = TenantModel.objects.get(uuid=app_uuid)
                connection.set_tenant(tenant)
                with connection.cursor() as c:
                    ws = Workspace(connection.tenant, request=None, as_systemuser=True)
                    ws.ready()
                    ws.sync_policies()
                response = {"message": "Policies synced successfully"}
                status = 200
                success = True
            except Exception as e:
                response = {"message": str(e)}
                status = 500
                success = False
            return get_api_response(success, response, status)
        policy_serializer = PolicySerializer(data=data)
        if policy_serializer.is_valid():
            success = True
            status_code = 200
            policy = policy_serializer.save(
                **{"roles": request.data.getlist("roles", [])}
            )
            result = {"message": "Policy Created Successfully", "policy_id": policy.id}
        else:
            success = False
            status_code = 400
            if policy_serializer.errors:
                error_messages = [
                    error[0] for field_name, error in policy_serializer.errors.items()
                ]
                error_message = ", ".join(error_messages)
            else:
                error_message = "Invalid data"

            result = {"message": error_message}

        return get_api_response(success, result, status_code)


@method_decorator(set_app_schema_path, name="dispatch")
class PolicyDetailViewAPIV1(ZelthyGenericPlatformAPIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    def get_obj(self, **kwargs):
        obj = PolicyModel.objects.get(id=kwargs.get("policy_id"))
        return obj

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            serializer = PolicySerializer(obj)
            success = True
            response = {"policy": serializer.data}
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            serializer = PolicySerializer(instance=obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(**{"roles": request.data.getlist("roles", [])})
                success = True
                status_code = 200
                result = {
                    "message": "Policy Updated Successfully",
                    "policy_id": obj.id,
                }
            else:
                success = False
                status_code = 400
                if serializer.errors:
                    error_messages = [
                        error[0] for field_name, error in serializer.errors.items()
                    ]
                    error_message = ", ".join(error_messages)
                else:
                    error_message = "Invalid data"

                result = {"message": error_message}
        except Exception as e:
            success = False
            result = {"message": str(e)}
            status_code = 500

        return get_api_response(success, result, status_code)
