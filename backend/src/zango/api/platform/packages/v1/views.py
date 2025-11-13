from django.core import signing

from zango.apps.shared.tenancy.models import Domain, TenantModel
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response
from zango.core.api.utils import ZangoAPIPagination
from zango.core.package_utils import (
    get_all_packages,
    get_package_configuration_url,
    install_package,
)


class PackagesViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    pagination_class = ZangoAPIPagination

    def get_app_obj(self, app_uuid):
        obj = TenantModel.objects.get(uuid=app_uuid)
        return obj

    def get(self, request, app_uuid, *args, **kwargs):
        action = request.GET.get("action", None)
        tenant = self.get_app_obj(app_uuid)
        search = request.GET.get("search", None)
        if action == "config_url":
            domains = Domain.objects.filter(tenant=tenant)
            if len(domains) == 0:
                resp = {"message": "No domain configured for the tenant"}
                status = 400
                return get_api_response(False, resp, status)

            try:
                token = signing.dumps(
                    request.user.id,
                )
                url = get_package_configuration_url(
                    request, tenant, request.GET.get("package_name")
                )
                resp = {"url": f"{url}?token={token}"}
                status = 200
            except Exception as e:
                resp = {"message": str(e)}
                status = 500
            return get_api_response(True, resp, status)
        try:
            packages = get_all_packages(request, tenant)
            if search:
                packages = [
                    obj for obj in packages if search.lower() in obj["name"].lower()
                ]
            # Count installed packages before pagination
            installed_count = sum(
                1 for pkg in packages if pkg.get("status") == "Installed"
            )

            paginated_packages = self.paginate_queryset(packages, request, view=self)
            packages = self.get_paginated_response_data(paginated_packages)
            packages["installed_count"] = installed_count
            success = True
            response = {"packages": packages}
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def post(self, request, app_uuid, *args, **kwargs):
        try:
            data = request.data
            tenant = TenantModel.objects.get(uuid=app_uuid)
            result = install_package(data["name"], data["version"], tenant.name)
            success = True
            response = {"message": result}
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)
