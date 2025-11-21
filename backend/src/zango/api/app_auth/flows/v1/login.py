import json

from allauth.headless.account.views import LoginView

from zango.core.api import get_api_response


class AppLoginViewAPIV1(LoginView):
    def handle(self, request, *args, **kwargs):
        auth_config = request.tenant.auth_config
        if (
            not auth_config.get("login_methods", {})
            .get("password", {})
            .get("enabled", False)
        ):
            return get_api_response(
                success=False,
                response_content={"message": "Password login is not enabled"},
                status=400,
            )
        return super().handle(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
