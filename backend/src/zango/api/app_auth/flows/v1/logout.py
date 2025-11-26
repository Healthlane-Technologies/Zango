import json

from allauth.headless.account.views import SessionView

from zango.core.api import get_api_response


class AppLogoutViewAPIV1(SessionView):
    def delete(self, request, *args, **kwargs):
        resp = super().delete(request, *args, **kwargs)
        resp_data = json.loads(resp.content.decode("utf-8"))
        if resp.status_code == 401:
            resp_data["message"] = "Successfully logged out"
        return get_api_response(
            success=True,
            response_content=resp_data,
            status=resp.status_code,
        )
