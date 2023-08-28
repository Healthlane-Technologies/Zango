import json
import traceback

from django.conf import settings

from zelthy.core.api import (
    ZelthySessionPlatformAPIView,
    get_api_response,
    ZelthyGenericPlatformAPIView,
)

from zelthy.apps.shared.tenancy.models import TenantModel
from .serializers import TenantSerializerModel


# import logging

# logger = logging.getLogger("zelthy")


class AppaunchAppAPIV1(ZelthyGenericPlatformAPIView):
    def validate_data(self, data):
        if TenantModel.objects.filter(name=data["name"]).exists():
            success, message = False, "App name already taken"
        elif len(data["name"]) < 5:
            success, message = False, "App name must have at least 5 charecters"
        else:
            success, message = True, ""
        return success, message

    def post(self, request, *args, **kwargs):
        data = json.loads(request.data["data"])
        try:
            success, message = self.validate_data(data)
            if success:
                app = TenantModel.objects.create(
                    name=data["name"],
                    schema_name=data["name"],
                    description=data["description"],
                    tenant_type="app",
                    status="staged",
                )
                app = TenantModel.objects.get(name=data["name"])
                app.initialize_workspace()
                # task = launch_new_app.delay(str(app.uuid), countdown=30)
                # result = {"app_uuid": str(app.uuid), "task_uuid": str(task)}
                result = {
                    "message": "App Launch Initiated Successfully",
                    "app_id": str(app.uuid),
                }
                status = 200
            else:
                result = {"message": message}
                status = 200
        except Exception as e:
            # logger.error(traceback.format_exc())
            result = {"message": str(e)}
            status = 500
            success = False
        return get_api_response(success, result, status)


class AppListViewV1(ZelthyGenericPlatformAPIView):
    def get(self, request, *args, **kwargs):
        try:
            apps = TenantModel.objects.all()
            serializer = TenantSerializerModel(apps, many=True)
            success = True
            response_content = serializer.data
            status = 200
        except Exception as e:
            success = False
            response_content = {"message": str(e)}
            status = 500

        return get_api_response(success, response_content, status)


class AppDetailViewAPIV1(ZelthyGenericPlatformAPIView):
    def get_obj(self, **kwargs):
        obj = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
        return obj

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            serializer = TenantSerializerModel(obj)
            success = True
            response_content = serializer.data
            status = 200
        except Exception as e:
            success = False
            response_content = {"message": str(e)}
            status = 500

        return get_api_response(success, response_content, status)
