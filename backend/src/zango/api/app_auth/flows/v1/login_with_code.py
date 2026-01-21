import json

from allauth.headless.account.views import ConfirmLoginCodeView, RequestLoginCodeView

from django.db.models import Q
from django.http import HttpResponse

from zango.apps.appauth.models import AppUserModel, OTPCode
from zango.core.api import get_api_response


class RequestLoginCodeViewAPIV1(RequestLoginCodeView):
    def handle(self, request, *args, **kwargs):
        auth_config = request.tenant.auth_config
        if (
            not auth_config.get("login_methods", {})
            .get("otp", {})
            .get("enabled", False)
        ):
            response = {
                "status": 400,
                "errors": [
                    {
                        "message": "OTP/Link login is not enabled",
                    }
                ],
            }
            return HttpResponse(json.dumps(response), status=400)
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
            response = {
                "status": 400,
                "errors": [
                    {
                        "message": "No account found with this email address.",
                    }
                ],
            }
            return HttpResponse(json.dumps(response), status=400)
        if not user.is_active:
            response = {
                "status": 400,
                "errors": [
                    {
                        "message": "Your account is currently inactive. Please reach out to support for assistance.",
                    }
                ],
            }
            return HttpResponse(json.dumps(response), status=400)
        if any(role.auth_config.get("enforce_sso", False) for role in user.roles.all()):
            response = {
                "status": 400,
                "errors": [
                    {"message": "OTP/Link login cannot be used when SSO is enforced"}
                ],
            }
            return HttpResponse(json.dumps(response), status=400)
        return super().handle(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        resp_data = json.loads(resp.content.decode("utf-8"))
        if resp.status_code == 401:
            resp_data["data"]["message"] = "Verification code sent."
        return get_api_response(
            success=True,
            response_content=resp_data,
            status=resp.status_code,
        )


class ConfirmLoginCodeViewAPIV1(ConfirmLoginCodeView):
    def dispatch(self, request, *args, **kwargs):
        data = json.loads(request.body)
        code = data.get("code")
        if code:
            try:
                otp_code = OTPCode.objects.get(code=code, otp_type="login_code")
                if not otp_code.is_valid():
                    response = {
                        "status": 400,
                        "errors": [
                            {
                                "message": "Login code has expired or has already been used",
                            }
                        ],
                    }
                    return HttpResponse(json.dumps(response), status=400)
            except OTPCode.DoesNotExist:
                return super().dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
