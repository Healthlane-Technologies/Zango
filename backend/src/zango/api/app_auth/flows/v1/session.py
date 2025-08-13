import json

from allauth.headless.usersessions.views import SessionsView

from zango.core.api import get_api_response


class AppSessionsViewAPIV1(SessionsView):
    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        resp_data = json.loads(resp.content.decode("utf-8"))
        return get_api_response(
            success=True,
            response_content=resp_data,
            status=resp.status_code,
        )

    def delete(self, request, *args, **kwargs):
        resp = super().delete(request, *args, **kwargs)
        resp_data = json.loads(resp.content.decode("utf-8"))
        return get_api_response(
            success=True,
            response_content=resp_data,
            status=resp.status_code,
        )
