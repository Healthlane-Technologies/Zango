import json

from allauth.account.stages import LoginStageController, SetPasswordStage
from allauth.headless.account.views import (
    ChangePasswordView,
    RequestPasswordResetView,
    ResetPasswordView,
)
from allauth.headless.base import response
from allauth.headless.base.views import APIView

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse

from zango.api.app_auth.profile.v1.utils import PasswordValidationMixin
from zango.apps.appauth.models import AppUserModel
from zango.core.api import (
    get_api_response,
)
from zango.core.utils import get_auth_priority

from .forms import PasswordSetForm


class PasswordChangeViewAPIV1(ChangePasswordView, PasswordValidationMixin):
    def handle(self, request, *args, **kwargs):
        if not request.tenant.auth_config.get("password_policy", {}).get(
            "allow_change", True
        ):
            response = {
                "status": 400,
                "errors": [
                    {
                        "message": "Password change is disabled",
                    }
                ],
            }
            return HttpResponse(json.dumps(response), status=400)
        try:
            # Load data from request body
            data = json.loads(request.body) if request.body else {}

            has_usable_password = request.user.has_usable_password()
            if has_usable_password:
                # Validate current password for users with usable passwords
                self.clean_password(
                    request,
                    request.user.email,
                    data.get("current_password"),
                )
                current_password = data.get("current_password")
        except ValidationError as e:
            # Handle ValidationError which may contain a list of messages
            if hasattr(e, "message"):
                message = e.message
            elif hasattr(e, "messages") and e.messages:
                message = "; ".join(str(msg) for msg in e.messages)
            else:
                message = str(e)
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": message,
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
        except Exception as e:
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": str(e),
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
        return super().handle(request, *args, **kwargs)

    def clean_password(self, request, email, password):
        """
        Validates that the current password is correct
        """
        try:
            user = authenticate(request=request, username=email, password=password)
            if user is None:
                raise ValidationError(
                    "The current password you have entered is wrong. Please try again!"
                )
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
        # Validate password policy

        success = False
        response = {}

        try:
            # Data is already validated in handle() method
            # Now validate new password against policies
            self.clean_password2(
                request.user,
                None,  # current_password already validated in handle()
                self.input.cleaned_data["new_password"],
            )
            resp = super().post(request, *args, **kwargs)
            resp_data = json.loads(resp.content.decode("utf-8"))
            if resp.status_code == 401:
                resp_data["message"] = "Successfully changed password"
            if resp.status_code != 401:
                return get_api_response(
                    success=False,
                    response_content=resp_data,
                    status=resp.status_code,
                )
            success = True
            status = 200
            return get_api_response(success, resp_data, status)
        except ValidationError as e:
            response = {"message": e.message}
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
        try:
            self.input.save()
            response = self.respond_next_stage()
            return get_api_response(
                success=True,
                response_content=json.loads(response.content.decode("utf-8")),
                status=response.status_code,
            )
        except ValidationError as e:
            message = str(e.message) if hasattr(e, "message") else str(e)
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": message,
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)


class RequestResetPasswordViewAPIV1(RequestPasswordResetView):
    def handle(self, request, *args, **kwargs):
        auth_config = request.tenant.auth_config
        if (
            not auth_config.get("password_policy", {})
            .get("reset", {})
            .get("enabled", False)
        ):
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "Password reset is not enabled, please contact support",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
        query = Q()
        data = json.loads(request.body)
        email = data.get("email")
        phone = data.get("phone")
        if email:
            query = query | Q(email__iexact=email)
        if phone:
            query = query | Q(mobile=phone)
        try:
            user = AppUserModel.objects.get(query)
        except AppUserModel.DoesNotExist:
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "User does not exist",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
        if any(role.auth_config.get("enforce_sso", False) for role in user.roles.all()):
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "Password cannot be reset when SSO is enforced",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
        return super().handle(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        data = json.loads(resp.content.decode("utf-8"))
        password_policy = get_auth_priority(policy="password_policy", request=request)
        password_reset_policy = password_policy.get("reset", {})
        if password_reset_policy.get("by_code", False):
            data["message"] = (
                "Password reset code has been sent to your email/phone number"
            )
        else:
            data["message"] = "Password reset link has been sent to your email address"
        return get_api_response(
            success=True if resp.status_code == 200 else False,
            response_content=data,
            status=resp.status_code,
        )


class ResetPasswordViewAPIV1(ResetPasswordView, PasswordValidationMixin):
    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        resp_data = json.loads(resp.content.decode("utf-8"))
        if not resp_data.get("data"):
            resp_data["data"] = {}
        password_policy = get_auth_priority(policy="password_policy")
        if resp.status_code == 200:
            resp_data["data"]["metadata"] = {"password_policy": password_policy}
        return get_api_response(
            success=True if resp.status_code == 200 else False,
            response_content=resp_data,
            status=resp.status_code,
        )

    def post(self, request, *args, **kwargs):
        auth_config = request.tenant.auth_config
        if (
            not auth_config.get("password_policy", {})
            .get("reset", {})
            .get("enabled", False)
        ):
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "Password reset is not enabled, please contact support",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
        resp = super().post(request, *args, **kwargs)
        resp_data = json.loads(resp.content.decode("utf-8"))
        if not resp_data.get("data"):
            resp_data["data"] = {}
        login_methods = get_auth_priority(policy="login_methods", request=request)
        if resp.status_code == 401 and not resp_data["data"].get("next_step"):
            resp_data["data"]["next_step"] = {
                "id": "login",
                "is_pending": True,
                "metadata": {"login_methods": login_methods},
            }
        return get_api_response(
            success=True
            if resp.status_code == 200 or resp.status_code == 401
            else False,
            response_content=resp_data,
            status=resp.status_code,
        )
