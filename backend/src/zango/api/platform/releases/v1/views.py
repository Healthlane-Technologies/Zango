from django.utils.decorators import method_decorator
from django.db.models import Q

from zango.core.common_utils import set_app_schema_path
from zango.core.utils import get_search_columns
from zango.apps.release.models import AppRelease
from zango.core.api import get_api_response, ZangoGenericPlatformAPIView
from zango.core.api.utils import ZangoAPIPagination

from .serializers import AppReleaseSerializer


@method_decorator(set_app_schema_path, name="dispatch")
class AppReleaseView(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    pagination_class = ZangoAPIPagination

    def get_queryset(self, search, columns={}):
        name_field_query_mappping = {
            "version": "version__icontains",
            "description": "description__icontains",
            "status": "status",
            "id": "id__icontains",
        }
        if columns.get("status") == "" or columns.get("status") is None:
            name_field_query_mappping.pop("status")
        records = AppRelease.objects.all().order_by("-id")
        if search == "" and columns == {}:
            return records
        filters = Q()
        for field_name, query in name_field_query_mappping.items():
            if field_name in columns:
                filters &= Q(**{query: columns[field_name]})
            else:
                if search:
                    filters |= Q(**{query: search})
        return records.filter(filters).distinct()

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            app_releases = self.get_queryset(search, columns)
            paginated_releases = self.paginate_queryset(
                app_releases, request, view=self
            )
            serializer = AppReleaseSerializer(paginated_releases, many=True)
            paginated_app_releases = self.get_paginated_response_data(serializer.data)
            success = True
            response = {
                "releases": paginated_app_releases,
                "message": "All app releases fetched successfully",
            }
            status = 200
        except Exception as e:
            import traceback

            traceback.print_exc()
            success = False
            response = {"message": str(e)}
            status = 500
        return get_api_response(success, response, status)
