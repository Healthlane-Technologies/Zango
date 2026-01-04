import json

from allauth.headless.account.views import LoginView

from django.http import HttpResponse

from zango.core.api import get_api_response

from .auth_utils import (
    get_user_by_email_or_phone_with_query,
    validate_user_for_authentication,
)


class AppLoginViewAPIV1(LoginView):
    def handle(self, request, *args, **kwargs):
        auth_config = request.tenant.auth_config
        if (
            not auth_config.get("login_methods", {})
            .get("password", {})
            .get("enabled", False)
        ):
            response = {
                "status": 400,
                "errors": [
                    {
                        "message": "Password login is not enabled",
                    }
                ],
            }
            return HttpResponse(json.dumps(response), status=400)
        data = json.loads(request.body) if request.body else {}
        email = data.get("email")
        phone = data.get("phone")

        if email or phone:
            user = get_user_by_email_or_phone_with_query(email=email, phone=phone)
            if user:
                validation_error = validate_user_for_authentication(
                    user, "Password login"
                )
                if validation_error:
                    return validation_error
        return super().handle(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
