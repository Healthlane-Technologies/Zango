from rest_framework.views import APIView

from zango.core.api import get_api_response
from zango.core.utils import get_auth_priority


class AppAuthConfigViewAPIV1(APIView):
    def get(self, request, *args, **kwargs):
        response = {"auth_config": get_auth_priority(request=request)}
        status = 200
        success = True
        return get_api_response(success, response, status)
