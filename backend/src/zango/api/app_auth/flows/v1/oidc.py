import json

from allauth.headless.account.views import SessionView
from allauth.socialaccount.adapter import get_adapter as get_socialaccount_adapter
from allauth.socialaccount.providers.base.constants import AuthProcess
from requests import RequestException
from rest_framework.views import APIView

from django.views.decorators.csrf import csrf_exempt

from zango.apps.appauth.models import OIDCProviderModel
from zango.apps.appauth.oidc import errors
from zango.apps.appauth.oidc.utils import (
    DEFAULT_NEXT,
    NEXT_SESSION_KEY,
    SSO_SESSION_KEY,
    oidc_enabled,
    safe_next,
)
from zango.core.api import get_api_response


def _error(status, code, message):
    return get_api_response(False, {"code": code, "message": message}, status)


class OIDCLoginInitViewAPIV1(APIView):
    """Starts OIDC sign-in and returns the provider's authorize URL."""

    def post(self, request, *args, **kwargs):
        slug = request.data.get("provider")
        if not slug:
            return _error(400, "provider_required", "provider is required")
        if not oidc_enabled(request):
            return _error(
                400, errors.OIDC_DISABLED, "OpenID Connect sign-in is not enabled"
            )
        if request.user.is_authenticated:
            return _error(409, "already_authenticated", "Already signed in")
        cfg = OIDCProviderModel.objects.filter(slug=slug, is_active=True).first()
        if cfg is None:
            return _error(
                404, errors.PROVIDER_INACTIVE, f"Provider '{slug}' is not available"
            )

        request.session[NEXT_SESSION_KEY] = safe_next(request.data.get("next"))
        try:
            provider = get_socialaccount_adapter(request).get_provider(
                request, cfg.provider_id
            )
            resp = provider.redirect(
                request,
                AuthProcess.LOGIN,
                next_url=errors.login_url(),
                headless=True,
                oidc_provider=cfg.slug,
            )
        except RequestException:
            return _error(
                502,
                "discovery_unavailable",
                "The identity provider could not be reached",
            )
        location = resp.get("Location") if resp.status_code in (301, 302) else None
        if not location:
            return _error(
                502,
                "discovery_unavailable",
                "The identity provider could not be reached",
            )
        return get_api_response(True, {"redirect_url": location}, 200)


@csrf_exempt
def oidc_callback(request, *args, **kwargs):
    """Redirect URI registered at the provider. Always answers with a redirect."""
    from allauth.socialaccount.providers.openid_connect.views import callback

    slug = kwargs.get("slug")
    cfg = OIDCProviderModel.objects.filter(slug=slug, is_active=True).first()
    if cfg is None:
        return errors.error_response(request, errors.PROVIDER_INACTIVE, slug)
    if not oidc_enabled(request):
        return errors.error_response(request, errors.OIDC_DISABLED, slug)
    return callback(request, provider_id=cfg.provider_id)


class OIDCStatusViewAPIV1(SessionView):
    """What the login page should do after the provider redirected back."""

    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        data = json.loads(resp.content.decode("utf-8"))
        meta = data.setdefault("meta", {})
        sso = request.session.get(SSO_SESSION_KEY)
        if sso:
            meta["sso"] = {"method": sso.get("method"), "provider": sso.get("provider")}
        sso_error = request.session.pop(errors.SSO_ERROR_SESSION_KEY, None)
        if sso_error:
            meta["sso_error"] = sso_error
        if meta.get("is_authenticated"):
            data.setdefault("data", {})["redirect_url"] = request.session.pop(
                NEXT_SESSION_KEY, DEFAULT_NEXT
            )
        return get_api_response(
            success=resp.status_code == 200,
            response_content=data,
            status=resp.status_code,
        )
