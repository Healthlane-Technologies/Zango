from rest_framework.views import APIView

from zango.apps.shared.tenancy.models import TenantModel
from zango.core.api import get_api_response
from zango.core.utils import get_auth_priority


class AuthConfigViewAPIV1(APIView):
    def get_tenant(self, **kwargs):
        obj = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
        return obj

    def get(self, request, *args, **kwargs):
        try:
            tenant = self.get_tenant(**kwargs)

            response = {
                "auth_config": get_auth_priority(tenant=tenant, request=request)
            }
            status = 200
            success = True
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)
