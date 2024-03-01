from django.db.models import Q
from django.conf import settings

from zelthy.core.api import (
    get_api_response,
    ZelthyGenericPlatformAPIView,
)
from zelthy.core.api.utils import ZelthyAPIPagination
from zelthy.apps.shared.platformauth.models import PlatformUserModel
from zelthy.apps.shared.tenancy.models import TenantModel
from zelthy.core.permissions import IsSuperAdminPlatformUser
from zelthy.core.utils import get_search_columns

from .serializers import PlatformUserSerializerModel


class PlatformUserViewAPIV1(ZelthyGenericPlatformAPIView, ZelthyAPIPagination):
    permission_classes = (IsSuperAdminPlatformUser,)
    pagination_class = ZelthyAPIPagination

    def get_dropdown_options(self):
        options = {}
        options["apps"] = [
            {"id": str(t.uuid), "label": t.name}
            for t in TenantModel.objects.all().exclude(schema_name="public")
        ]
        return options

    def get_queryset(self, search, columns={}):
        field_name_query_mappping = {
            "user_name": "name__icontains",
            "email": "email__icontains",
            "user_id": "id__icontains",
            "is_active": "is_active",
            "apps_access": "apps__name__icontains",
        }
        if columns.get("is_active") == "true":
            columns["is_active"] = True
        elif columns.get("is_active") == "false":
            columns["is_active"] = False
        elif columns.get("is_active") == "" or columns.get("is_active") is None:
            field_name_query_mappping.pop("is_active")
        records = PlatformUserModel.objects.all().order_by("-modified_at")
        if search == "" and columns == {}:
            return records
        filters = Q()
        for field_name, query in field_name_query_mappping.items():
            if field_name in columns:
                filters &= Q(**{query: columns[field_name]})
            else:
                if search:
                    filters |= Q(**{query: search})
        return records.filter(filters).distinct()

    def get(self, request, *args, **kwargs):
        try:
            include_dropdown_options = request.GET.get("include_dropdown_options")
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            platform_users = self.get_queryset(search, columns)
            paginated_platform_users = self.paginate_queryset(
                platform_users, request, view=self
            )
            serializer = PlatformUserSerializerModel(
                paginated_platform_users, many=True
            )
            platform_users_data = self.get_paginated_response_data(serializer.data)
            success = True
            response = {
                "platform_users": platform_users_data,
                "message": "Platform user fetched successfully",
            }
            if include_dropdown_options:
                response["dropdown_options"] = self.get_dropdown_options()
            status = 200

        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            app_uuids = data.getlist("apps")
            creation_result = PlatformUserModel.create_user(
                name=data["name"],
                email=data["email"],
                mobile="",
                password=data["password"],
                is_superadmin=False,
                require_verification=False,
                app_uuids=app_uuids,
            )
            success = creation_result["success"]
            result = {"message": creation_result["message"]}
            status = 200 if success else 400
        except Exception as e:
            result = {"message": str(e)}
            status = 500
            success = False
        return get_api_response(success, result, status)


class PlatformUserDetailViewAPIV1(ZelthyGenericPlatformAPIView):
    permission_classes = (IsSuperAdminPlatformUser,)

    def get_obj(self, **kwargs):
        obj = PlatformUserModel.objects.get(id=kwargs.get("user_id"))
        return obj

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            serializer = PlatformUserSerializerModel(obj)
            success = True
            response = {"platform_user": serializer.data}
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            update_result = PlatformUserModel.update_user(obj, request.data)
            success = update_result["success"]
            message = update_result["message"]
            status_code = 200 if success else 400
            result = {
                "message": message,
                "user_id": obj.id,
            }
        except Exception as e:
            success = False
            result = {"message": str(e)}
            status_code = 500

        return get_api_response(success, result, status_code)


class AppPanelDetailsView(ZelthyGenericPlatformAPIView):
    def get_obj(self, request, **kwargs):
        obj = PlatformUserModel.objects.get(id=request.user.id)
        return obj

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(request, **kwargs)
            serializer = PlatformUserSerializerModel(obj)
            success = True
            response = {
                "app_data": {"user_logged_in": serializer.data},
                "is_codeassist_enabled": getattr(settings, "CODEASSIST_ENABLED", False),
            }
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)
