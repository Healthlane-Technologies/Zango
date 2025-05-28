from django.db.models import Q
from django.utils.decorators import method_decorator

from zango.apps.release.models import AppRelease
from zango.apps.shared.tenancy.models import TenantModel
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path
from zango.core.time_utils import process_timestamp
from zango.core.utils import get_search_columns

from .serializers import AppReleaseSerializer


@method_decorator(set_app_schema_path, name="dispatch")
class AppReleaseView(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    pagination_class = ZangoAPIPagination

    def process_id(self, id):
        try:
            return int(id)
        except ValueError:
            return None

    def get_queryset(self, search, tenant, columns={}):
        field_name_query_mapping = {
            "version": "version__icontains",
            "description": "description__icontains",
            "status": "status",
            "id": "id__icontains",
        }
        search_filters = {
            "id": self.process_id,
            "Release_date": process_timestamp,
        }
        if columns.get("status") == "" or columns.get("status") is None:
            field_name_query_mapping.pop("status")
        records = AppRelease.objects.all().order_by("-id")
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
        if columns.get("Release_date"):
            processed = process_timestamp(columns.get("Release_date"), tenant.timezone)
            if processed is not None:
                records = records.filter(
                    created_at__gte=processed["start"], created_at__lte=processed["end"]
                )
        if columns.get("status"):
            records = records.filter(status=columns["status"])
        if columns.get("version"):
            records = records.filter(version=columns["version"])
        return records

    def get_dropdown_options(self):
        options = {}
        options["version"] = [
            {
                "id": version,
                "label": version,
            }
            for version in AppRelease.objects.values_list(
                "version", flat=True
            ).distinct()
        ]
        options["status"] = [
            {
                "id": "initiated",
                "label": "Initiated",
            },
            {
                "id": "in_progress",
                "label": "In Progress",
            },
            {
                "id": "released",
                "label": "Released",
            },
            {
                "id": "failed",
                "label": "Failed",
            },
            {
                "id": "archived",
                "label": "Archived",
            },
        ]
        return options

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            tenant = TenantModel.objects.get(uuid=app_uuid)
            include_dropdown_options = request.GET.get("include_dropdown_options")
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            app_releases = self.get_queryset(search, tenant, columns)
            paginated_releases = self.paginate_queryset(
                app_releases, request, view=self
            )
            serializer = AppReleaseSerializer(
                paginated_releases, many=True, context={"tenant": tenant}
            )
            paginated_app_releases = self.get_paginated_response_data(serializer.data)
            success = True
            response = {
                "releases": paginated_app_releases,
                "message": "All app releases fetched successfully",
            }
            if include_dropdown_options:
                response["dropdown_options"] = self.get_dropdown_options()
            status = 200
        except Exception as e:
            import traceback

            traceback.print_exc()
            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)
