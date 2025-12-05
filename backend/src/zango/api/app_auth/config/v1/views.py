from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from zango.api.platform.tenancy.v1.serializers import AppUserModelSerializerModel
from zango.apps.appauth.auth_backend import KnoxTokenAuthBackend
from zango.core.api import get_api_response
from zango.core.utils import get_auth_priority


@method_decorator(ensure_csrf_cookie, name="dispatch")
class AppAuthConfigViewAPIV1(APIView):
    def get_authenticators(self):
        if self.request.method == "PUT":
            return [KnoxTokenAuthBackend(), SessionAuthentication()]
        return super().get_authenticators()

    def get_permissions(self):
        if self.request.method == "PUT":
            return [IsAuthenticated()]
        return []

    def get(self, request):
        response = {"auth_config": get_auth_priority(request=request)}
        status = 200
        success = True
        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        serializer = AppUserModelSerializerModel(
            request.user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return get_api_response(False, serializer.errors, 400)
        serializer.save()
        response = {"auth_config": get_auth_priority(request=request)}
        status = 200
        success = True
        return get_api_response(success, response, status)
