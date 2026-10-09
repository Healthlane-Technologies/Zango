import json

from allauth.headless.account.views import SessionView

from zango.apps.appauth.oidc.logout import get_idp_logout_url
from zango.apps.appauth.oidc.utils import SSO_SESSION_KEY
from zango.core.api import get_api_response


class AppLogoutViewAPIV1(SessionView):
    def delete(self, request, *args, **kwargs):
        # Read before logout flushes the session.
        sso = request.session.get(SSO_SESSION_KEY)
        resp = super().delete(request, *args, **kwargs)
        resp_data = json.loads(resp.content.decode("utf-8"))
        if resp.status_code == 401:
            resp_data["message"] = "Successfully logged out"
        idp_logout_url = get_idp_logout_url(request, sso)
        if idp_logout_url:
            resp_data["idp_logout_url"] = idp_logout_url
        return get_api_response(
            success=True,
            response_content=resp_data,
            status=resp.status_code,
        )
