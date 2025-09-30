import json

from allauth.headless.account.views import LoginView

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from zango.core.api import get_api_response


@method_decorator(csrf_exempt, name="dispatch")
class AppLoginViewAPIV1(LoginView):
    def post(self, request, *args, **kwargs):
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

        resp = super().post(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
