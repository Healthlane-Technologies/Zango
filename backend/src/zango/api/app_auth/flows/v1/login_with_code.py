import json

from allauth.headless.account.views import ConfirmLoginCodeView, RequestLoginCodeView

from django.http import HttpResponse

from zango.apps.appauth.models import OTPCode
from zango.core.api import get_api_response

from .auth_utils import (
    get_user_by_email_or_phone_with_query,
    get_user_not_found_error_response,
    validate_user_for_authentication,
)


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
        data = json.loads(request.body)
        email = data.get("email")
        phone = data.get("phone")

        # Fetch user by email or phone
        user = get_user_by_email_or_phone_with_query(email=email, phone=phone)
        if not user:
            return get_user_not_found_error_response(
                "No account found with this email address/phone."
            )

        # Validate user status and permissions
        validation_error = validate_user_for_authentication(user, "OTP/Link login")
        if validation_error:
            return validation_error

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
