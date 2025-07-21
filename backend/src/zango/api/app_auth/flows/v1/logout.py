import json

from allauth.headless.account.views import SessionView

from zango.core.api import get_api_response


class AppLogoutViewAPIV1(SessionView):
    def delete(self, request, *args, **kwargs):
        resp = super().delete(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
