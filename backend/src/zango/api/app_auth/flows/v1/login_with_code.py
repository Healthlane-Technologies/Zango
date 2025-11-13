import json

from allauth.headless.account.views import ConfirmLoginCodeView, RequestLoginCodeView

from zango.core.api import get_api_response


class RequestLoginCodeViewAPIV1(RequestLoginCodeView):
    def post(self, request, *args, **kwargs):
        auth_config = request.tenant.auth_config
        if (
            not auth_config.get("login_methods", {})
            .get("otp", {})
            .get("enabled", False)
        ):
            return get_api_response(
                success=False,
                response_content={"message": "OTP login is not enabled"},
                status=400,
            )
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
