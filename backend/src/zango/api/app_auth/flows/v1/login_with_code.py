import json

from allauth.headless.account.views import ConfirmLoginCodeView, RequestLoginCodeView

from django.db.models import Q

from zango.apps.appauth.models import AppUserModel
from zango.core.api import get_api_response


class RequestLoginCodeViewAPIV1(RequestLoginCodeView):
    def handle(self, request, *args, **kwargs):
        auth_config = request.tenant.auth_config
        if (
            not auth_config.get("login_methods", {})
            .get("otp", {})
            .get("enabled", False)
        ):
            return get_api_response(
                success=False,
                response_content={"message": "OTP/Link login is not enabled"},
                status=400,
            )
        query = Q()
        data = json.loads(request.body)
        email = data.get("email")
        phone = data.get("phone")
        if email:
            query = query | Q(email=email)
        if phone:
            query = query | Q(mobile=phone)
        try:
            user = AppUserModel.objects.get(query)
        except AppUserModel.DoesNotExist:
            return get_api_response(
                success=False,
                response_content={
                    "error": [{"message": "User not found with provided details"}]
                },
                status=400,
            )
        if any(role.auth_config.get("enforce_sso", False) for role in user.roles.all()):
            return get_api_response(
                success=False,
                response_content={
                    "error": [
                        {
                            "message": "OTP/Link login cannot be used when SSO is enforced"
                        }
                    ]
                },
                status=400,
            )
        return super().handle(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        resp_data = json.loads(resp.content.decode("utf-8"))
        if resp.status_code == 401:
            resp_data["data"]["message"] = "Login code sent successfully"
        return get_api_response(
            success=True,
            response_content=resp_data,
            status=resp.status_code,
        )


class ConfirmLoginCodeViewAPIV1(ConfirmLoginCodeView):
    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
