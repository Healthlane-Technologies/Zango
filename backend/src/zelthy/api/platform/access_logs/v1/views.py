import csv
import json
import pytz
import traceback
from datetime import datetime

from django.db.models import Q
from django.utils.decorators import method_decorator

from zelthy.core.utils import get_search_columns
from zelthy.core.api.utils import ZelthyAPIPagination
from zelthy.apps.access_logs.models import AppAccessLog
from zelthy.core.common_utils import set_app_schema_path
from zelthy.apps.shared.tenancy.models import TenantModel
from zelthy.core.api import get_api_response, ZelthyGenericPlatformAPIView

from .serializers import AccessLogSerializerModel


@method_decorator(set_app_schema_path, name="dispatch")
class AccessLogViewAPIV1(ZelthyGenericPlatformAPIView, ZelthyAPIPagination):
    pagination_class = ZelthyAPIPagination

    def process_timestamp(self, timestamp, timezone):
        try:
            ts = json.loads(timestamp)
            tz = pytz.timezone(timezone)
            ts["start"] = tz.localize(
                datetime.strptime(ts["start"] + "-" + "00:00", "%Y-%m-%d-%H:%M"),
                is_dst=None,
            )
            ts["end"] = tz.localize(
                datetime.strptime(ts["end"] + "-" + "23:59", "%Y-%m-%d-%H:%M"),
                is_dst=None,
            )
            return ts
        except Exception:
            return None

    def process_id(self, id):
        try:
            return int(id)
        except ValueError:
            return None

    def get_queryset(self, search, tenant, columns={}):

        field_name_query_mapping = {
            "id": "id",
            "user": "user__name__icontains",
            "user_agent": "user_agent__icontains",
        }
        search_filters = {
            "id": self.process_id,
            "attempt_time": self.process_timestamp,
        }

        records = AppAccessLog.objects.all().order_by("-id")

        if search == "" and columns == {}:
            return records

        filters = Q()
        for field_name, query in field_name_query_mapping.items():
            if search:
                if search_filters.get(field_name, None):
                    filters |= Q(**{query: search_filters[field_name](search)})
                else:
                    filters |= Q(**{query: search})
        records = records.filter(filters).distinct()

        if columns.get("attempt_time"):
            processed = self.process_timestamp(
                columns.get("attempt_time"), tenant.timezone
            )
            if processed is not None:
                records = records.filter(
                    attempt_time__gte=processed["start"],
                    attempt_time__lte=processed["end"],
                )
        if columns.get("attempt_type"):
            records = records.filter(attempt_type=columns.get("attempt_type"))

        if columns.get("is_login_successful") != None:
            records = records.filter(
                is_login_successful=columns.get("is_login_successful")
            )

        if columns.get("role"):
            records = records.filter(role=columns.get("role"))

        return records

    def get_dropdown_options(self):
        options = {}
        options["attempt_type"] = [
            {
                "id": "login",
                "label": "Login",
            },
            {
                "id": "switch_role",
                "label": "Switch Role",
            },
        ]
        options["is_login_successful"] = [
            {
                "id": True,
                "label": "Successful",
            },
            {
                "id": False,
                "label": "Failed",
            },
        ]
        role_list = list(
            AppAccessLog.objects.all()
            .values_list("role__id", "role__name")
            .order_by("role__name")
            .distinct()
        )
        for user_role in role_list:
            options["role"].append(
                {
                    "id": user_role[0],
                    "label": user_role[1],
                }
            )
        return options

    def get(self, request, *args, **kwargs):
        try:
            app_uuid = kwargs.get("app_uuid")
            tenant = TenantModel.objects.get(uuid=app_uuid)
            include_dropdown_options = request.GET.get("include_dropdown_options")
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            access_logs = self.get_queryset(search, tenant, columns)
            paginated_access_logs = self.paginate_queryset(
                access_logs, request, view=self
            )
            serializer = AccessLogSerializerModel(
                paginated_access_logs, many=True, context={"tenant": tenant}
            )
            accesslogs = self.get_paginated_response_data(serializer.data)
            success = True
            response = {
                "audit_logs": accesslogs,
                "message": "Access logs fetched successfully",
            }
            if include_dropdown_options:
                response["dropdown_options"] = self.get_dropdown_options()

            status = 200

        except Exception as e:
            traceback.print_exc()
            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)
