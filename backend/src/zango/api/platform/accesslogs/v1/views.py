import traceback

from django.db.models import Q
from django.utils.decorators import method_decorator

from zango.api.platform.accesslogs.v1.serializers import AccessLogSerializerModel
from zango.apps.accesslogs.models import AppAccessLog
from zango.apps.shared.tenancy.models import TenantModel
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path
from zango.core.time_utils import process_timestamp
from zango.core.utils import get_search_columns


@method_decorator(set_app_schema_path, name="dispatch")
class AccessLogViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    pagination_class = ZangoAPIPagination

    def process_id(self, id):
        try:
            return int(id)
        except ValueError:
            return None

    def get_queryset(self, search, tenant, columns={}):
        # Text-only free-text search targets. Numeric fields (id, user_id)
        # move to an explicit exact-match branch below so we don't OR
        # int-typed columns into a text search chain.
        text_field_query_mapping = {
            "username": "username__icontains",
            "user_agent": "user_agent__icontains",
            "ip_address": "ip_address__icontains",
            "attempt_type": "attempt_type__icontains",
        }
        # FK-name searches use a subquery instead of a joined icontains so
        # we don't need distinct() to dedupe join rows and the DB can use
        # the FK index.
        fk_name_search_mapping = {
            "user__in": ("user", "name__icontains"),
            "role__in": ("role", "name__icontains"),
        }

        records = AppAccessLog.objects.all().order_by("-id")

        if search == "" and columns == {}:
            return records

        filters = Q()
        if search:
            for field_name, query in text_field_query_mapping.items():
                filters |= Q(**{query: search})
            for query_key, (field, subq_filter) in fk_name_search_mapping.items():
                related_model = AppAccessLog._meta.get_field(field).related_model
                filters |= Q(
                    **{query_key: related_model.objects.filter(**{subq_filter: search})}
                )
            # Exact-match numeric branch — only fires when the user typed
            # a plain integer.
            if search.isdigit():
                filters |= Q(id=int(search)) | Q(user_id=int(search))
        records = records.filter(filters)

        if columns.get("attempt_time"):
            processed = process_timestamp(columns.get("attempt_time"), tenant.timezone)
            if processed is not None:
                records = records.filter(
                    attempt_time__gte=processed["start"],
                    attempt_time__lte=processed["end"],
                )

        if columns.get("session_expired_at"):
            processed = process_timestamp(
                columns.get("session_expired_at"), tenant.timezone
            )
            if processed is not None:
                records = records.filter(
                    session_expired_at__gte=processed["start"],
                    session_expired_at__lte=processed["end"],
                )
        if columns.get("attempt_type"):
            records = records.filter(attempt_type=columns.get("attempt_type"))

        if columns.get("is_login_successful") is not None:
            if columns.get("is_login_successful") == "successful":
                records = records.filter(is_login_successful=True)
            elif columns.get("is_login_successful") == "failed":
                records = records.filter(is_login_successful=False)

        if columns.get("role"):
            records = records.filter(role=columns.get("role"))

        return records

    def get_dropdown_options(self):
        options = {"role": []}
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
                "id": "successful",
                "label": "Successful",
            },
            {
                "id": "failed",
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

            # Calculate total failed attempts before pagination
            total_failed_attempts = access_logs.filter(
                is_login_successful=False
            ).count()

            paginated_access_logs = self.paginate_queryset(
                access_logs, request, view=self
            )
            serializer = AccessLogSerializerModel(
                paginated_access_logs, many=True, context={"tenant": tenant}
            )
            accesslogs = self.get_paginated_response_data(serializer.data)
            success = True
            response = {
                "access_logs": accesslogs,
                "total_failed_attempts": total_failed_attempts,
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
