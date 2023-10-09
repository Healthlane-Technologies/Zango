from zelthy.apps.shared.tenancy.models import TenantModel
from zelthy.apps.dynamic_models.workspace.base import Workspace
from zelthy.core.api import (
    get_api_response,
    ZelthyGenericPlatformAPIView,
)
from .helpers import get_packages

class ListAvailablePackagesAPIV1(ZelthyGenericPlatformAPIView):

    def get_obj(self, **kwargs):
        obj = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
        return obj
    
    def get_installed_packages(self, **kwargs):
        app_obj = self.get_obj(**kwargs)

        pass

    def get(self, request, *args, **kwargs):
        try:
            available_packages = get_packages()
            installed_packages = {}
            success = True
            response = {
                "packages": get_packages(),
                "message": "Packages list fetched successfully",
            }
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)