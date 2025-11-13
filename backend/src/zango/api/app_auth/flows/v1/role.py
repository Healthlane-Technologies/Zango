import json

from allauth.account.stages import LoginStageController, RoleSelectionStage
from allauth.headless.base import response
from allauth.headless.base.views import APIView

from zango.apps.appauth.models import UserRoleModel
from zango.core.api import ZangoGenericAppAPIView, get_api_response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name='dispatch')
class UserRoleViewAPIV1(APIView):
    stage_class = RoleSelectionStage

    def handle(self, request, *args, **kwargs):
        self.stage = LoginStageController.enter(request, self.stage_class.key)
        if not self.stage:
            return response.UnauthorizedResponse(request)
        return super().handle(request, *args, **kwargs)

    def respond_stage_error(self):
        return response.UnauthorizedResponse(self.request)

    def respond_next_stage(self):
        self.stage.exit()
        return response.AuthenticationResponse(self.request)

    def post(self, request, *args, **kwargs):
        role = request.GET.get("role")
        if role is None:
            return get_api_response(
                success=False,
                response_content={"message": "user role not specified"},
                status=400,
            )
        try:
            UserRoleModel.objects.get(id=role)
        except UserRoleModel.DoesNotExist:
            return get_api_response(
                success=False,
                response_content={"message": "specified user role does not exist"},
                status=400,
            )
        request.session["role_id"] = role
        response = self.respond_next_stage()
        return get_api_response(
            success=True,
            response_content=json.loads(response.content.decode("utf-8")),
            status=response.status_code,
        )


class SwitchRoleAPIV1(ZangoGenericAppAPIView):
    def post(self, request, *args, **kwargs):
        role = request.GET.get("role")
        if role is None:
            return get_api_response(
                success=False,
                response_content={"message": "user role not specified"},
                status=400,
            )
        try:
            UserRoleModel.objects.get(id=role)
        except UserRoleModel.DoesNotExist:
            return get_api_response(
                success=False,
                response_content={"message": "specified user role does not exist"},
                status=400,
            )
        request.session["role_id"] = role
        return get_api_response(
            success=True,
            response_content={"message": "switched role"},
            status=200,
        )
