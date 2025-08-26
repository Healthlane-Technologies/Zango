import json

from allauth.headless.socialaccount.views import RedirectToProviderView

from zango.core.api import get_api_response


class OAuthRedirectView(RedirectToProviderView):
    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        if resp.status_code in [301, 302, 303, 307, 308]:
            redirect_url = resp.get("Location", "")
            return get_api_response(
                success=True,
                response_content={"redirect_url": redirect_url},
                status=200,
            )

        try:
            response_content = json.loads(resp.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            response_content = {"message": "Unable to parse response content"}

        return get_api_response(
            success=resp.status_code < 400,
            response_content=response_content,
            status=resp.status_code,
        )
