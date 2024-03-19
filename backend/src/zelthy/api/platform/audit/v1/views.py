import traceback
import csv
from datetime import datetime
import json
import pytz

from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.conf import settings

from zelthy.core.api import get_api_response, ZelthyGenericPlatformAPIView
from zelthy.core.api.utils import ZelthyAPIPagination
from zelthy.core.permissions import IsSuperAdminPlatformUser
from zelthy.core.utils import get_search_columns
from zelthy.apps.appauth.models import AppUserModel
from zelthy.apps.shared.tenancy.models import TenantModel
from zelthy.apps.auditlog.models import LogEntry

from .serializers import AuditLogSerializerModel


class AuditLogViewAPIV1(ZelthyGenericPlatformAPIView, ZelthyAPIPagination):
    permission_classes = (IsSuperAdminPlatformUser,)
    pagination_class = ZelthyAPIPagination

    def process_timestamp(self, timestamp):
        try:
            ts = json.loads(json.loads(timestamp))
            tz = pytz.timezone(connection.tenant.timezone)
            ts["start"] = tz.localize(
                datetime.strptime(ts["start"] + "-" + "00:00", "%Y-%m-%d-%H:%M"),
                is_dst=None,
            )
            ts["end"] = tz.localize(
                datetime.strptime(ts["end"] + "-" + "23:59", "%Y-%m-%d-%H:%M"),
                is_dst=None,
            )
            return ts
        except ValueError:
            return None

    def process_id(self, id):
        try:
            return int(id)
        except ValueError:
            return None

    def get_queryset(self, search, columns={}):

        field_name_query_mapping = {
            "tenant_actor": "tenant_actor__name__icontains",
            "platform_actor": "platform_actor__name__icontains",
            "object_id": "object_id",
            "log_id": "id",
            "object_repr": "object_repr__icontains",
        }
        search_filters = {
            "log_id": self.process_id,
            "object_id": self.process_id,
            "timestamp": self.process_timestamp,
        }
        records = LogEntry.objects.all().order_by("-id")
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
        if columns.get("timestamp"):
            processed = self.process_timestamp(columns.get("timestamp"))
            records = records.filter(
                timestamp__gte=processed["start"], timestamp__lte=processed["end"]
            )
        if columns.get("action"):
            records = records.filter(action=columns.get("action"))
        return records

    def get_dropdown_options(self):
        options = {}
        options["action"] = [
            {
                "id": "0",
                "label": "Create",
            },
            {
                "id": "1",
                "label": "Update",
            },
            {
                "id": "2",
                "label": "Delete",
            },
            {
                "id": "3",
                "label": "Access",
            },
        ]
        return options

    def get(self, request, *args, **kwargs):
        try:
            app_uuid = kwargs.get("app_uuid")
            tenant = TenantModel.objects.get(uuid=app_uuid)
            action = request.GET.get("action")
            if action == "generate_report":
                self.generate_report(request, tenant, *args, **kwargs)
                return get_api_response(True, {}, 200)
            include_dropdown_options = request.GET.get("include_dropdown_options")
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            connection.set_tenant(tenant)
            with connection.cursor() as c:
                audit_logs = self.get_queryset(search, columns)
                paginated_audit_logs = self.paginate_queryset(
                    audit_logs, request, view=self
                )
                serializer = AuditLogSerializerModel(
                    paginated_audit_logs, many=True, context={"tenant": tenant}
                )
                auditlogs = self.get_paginated_response_data(serializer.data)
                success = True
                response = {
                    "audit_logs": auditlogs,
                    "message": "Audit logs fetched successfully",
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

    def generate_report(self, request, tenant, *args, **kwargs):
        from_timestamp = self.process_timestamp(request.GET.get("from_timestamp"))
        to_timestamp = self.process_timestamp(request.GET.get("to_timestamp"))

        connection.set_tenant(tenant)
        with connection.cursor() as c:
            logs = LogEntry.objects.filter(
                timestamp__gte=from_timestamp, timestamp__lte=to_timestamp
            )
            serialized_logs = AuditLogSerializerModel(
                logs, many=True, context={"tenant": tenant}
            ).data
            field_names = [
                "id",
                "tenant_actor",
                "platform_actor",
                "action",
                "object_repr",
                "timestamp",
                "changes",
            ]
            with open("auditlogs.csv", "w") as f:
                writer = csv.DictWriter(f, fieldnames=field_names)
                writer.writeheader()
                for log in serialized_logs:
                    writer.writerow(log)
