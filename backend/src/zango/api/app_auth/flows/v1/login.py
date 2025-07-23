import json

from allauth.headless.account.views import LoginView

from zango.core.api import get_api_response


class AppLoginViewAPIV1(LoginView):
    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
