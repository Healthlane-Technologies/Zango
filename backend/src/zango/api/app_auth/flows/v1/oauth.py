import json

from allauth.headless.socialaccount.views import RedirectToProviderView

from zango.core.api import get_api_response
from zango.core.utils import get_auth_priority


class OAuthRedirectView(RedirectToProviderView):
    def post(self, request, *args, **kwargs):
        # Get provider from POST data or URL kwargs
        provider = request.POST.get("provider") or kwargs.get("provider")

        auth_config = get_auth_priority(request=request)

        print("auth config is", auth_config)

        # Ensure auth_config is a dictionary
        if not isinstance(auth_config, dict):
            return get_api_response(
                success=False,
                response_content={"message": "Invalid auth configuration"},
                status=400,
            )

        login_methods = auth_config.get("login_methods", {})
        if not isinstance(login_methods, dict):
            return get_api_response(
                success=False,
                response_content={"message": "OIDC login is not configured"},
                status=400,
            )

        oidc_config = login_methods.get("oidc", {})
        if not isinstance(oidc_config, dict):
            return get_api_response(
                success=False,
                response_content={"message": "OIDC login is not configured"},
                status=400,
            )

        if not oidc_config.get("enabled", False):
            return get_api_response(
                success=False,
                response_content={"message": "OIDC login is not enabled"},
                status=400,
            )
        if provider:
            providers = oidc_config.get("providers", [])
            if not isinstance(providers, list):
                return get_api_response(
                    success=False,
                    response_content={"message": "No OIDC providers configured"},
                    status=400,
                )

            # Find the provider and check if it's enabled
            provider_found = None
            for p in providers:
                if isinstance(p, dict) and p.get("provider") == provider:
                    provider_found = p
                    break

            if not provider_found:
                return get_api_response(
                    success=False,
                    response_content={
                        "message": f"Provider '{provider}' is not configured"
                    },
                    status=400,
                )

            if not provider_found.get("enabled", False):
                return get_api_response(
                    success=False,
                    response_content={
                        "message": f"Provider '{provider}' is not enabled"
                    },
                    status=400,
                )

        else:
            return get_api_response(
                success=False,
                response_content={"message": "No provider specified"},
                status=400,
            )

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
