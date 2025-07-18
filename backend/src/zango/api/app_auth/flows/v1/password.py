import json

from allauth.account.stages import LoginStageController, SetPasswordStage
from allauth.headless.account.views import ChangePasswordView, RequestPasswordResetView
from allauth.headless.base import response
from allauth.headless.base.views import APIView

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from zango.api.app_auth.profile.v1.utils import PasswordValidationMixin
from zango.apps.appauth.models import OldPasswords
from zango.core.api import (
    ZangoSessionAppAPIView,
    get_api_response,
)

from .forms import PasswordSetForm


class PasswordChangeViewAPIV1(ChangePasswordView, PasswordValidationMixin):
    def clean_password(self, request, email, password):
        """
        Validates that the current password is correct
        """
        try:
            user = authenticate(request=request, username=email, password=password)
        except Exception:
            import traceback

            traceback.print_exc()
            raise ValidationError(
                "The current password you have entered is wrong. Please try again!"
            )

    def clean_password2(self, user, current_password, new_password):
        """method to validate password"""
        password2 = new_password
        validation = self.run_all_validations(
            user, new_password, password2, current_password
        )
        if not validation.get("validation"):
            raise ValidationError(validation.get("msg"))
        return True

    def put(self, request, *args, **kwargs):
        success = False

        if request.tenant.auth_config.get("password_policy", {}).get(
            "allow_change", True
        ):
            try:
                self.clean_password(
                    request,
                    request.user.email,
                    self.input.cleaned_data["current_password"],
                )
                self.clean_password2(
                    request.user,
                    self.input.cleaned_data["current_password"],
                    self.input.cleaned_data["new_password"],
                )

                user = request.user

                resp = super().post(request, *args, **kwargs)

                if resp.status_code != 401:
                    return get_api_response(
                        success=False,
                        response_content=resp.content.decode("utf-8"),
                        status=resp.status_code,
                    )

                user.refresh_from_db()
                obj = OldPasswords.objects.create(user=user)
                obj.setPasswords(user.password)
                obj.save()
                success = True
                status = 200
                return get_api_response(success, resp.content.decode("utf-8"), status)
            except ValidationError as e:
                response = {"message": e.message}
            if success:
                status = 200
            else:
                status = 400
            return get_api_response(success, response, status)
        else:
            response = {"message": "Password change is disabled"}
            success = False
            status = 400
            return get_api_response(success, response, status)


class SetPasswordViewAPIV1(APIView):
    input_class = PasswordSetForm
    stage_class = SetPasswordStage

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

    def get_input_kwargs(self):
        return {"user": self.stage.login.user}

    def post(self, request, *args, **kwargs):
        self.input.save()
        response = self.respond_next_stage()
        return get_api_response(
            success=True,
            response_content=json.loads(response.content.decode("utf-8")),
            status=response.status_code,
        )


class RequestResetPasswordViewAPIV1(ZangoSessionAppAPIView, RequestPasswordResetView):
    pass
