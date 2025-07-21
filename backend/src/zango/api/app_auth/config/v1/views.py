from rest_framework.views import APIView

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from zango.core.api import get_api_response
from zango.core.utils import get_auth_priority


@method_decorator(ensure_csrf_cookie, name="dispatch")
class AppAuthConfigViewAPIV1(APIView):
    def get(self, request):
        response = {"auth_config": get_auth_priority(request=request)}
        status = 200
        success = True
        return get_api_response(success, response, status)
