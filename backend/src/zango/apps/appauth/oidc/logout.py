from django.utils.http import urlencode

from allauth.utils import build_absolute_uri

from zango.apps.appauth.models import OIDCProviderModel

from .errors import LOGIN_PATH


def get_idp_logout_url(request, sso):
    """
    URL of the provider's end-session page for an OIDC session whose provider
    has ``rp_logout`` on, else ``None``.
    """
    if not sso or sso.get("method") != "oidc":
        return None
    cfg = OIDCProviderModel.objects.filter(
        slug=sso.get("provider"), rp_logout=True
    ).first()
    if cfg is None:
        return None
    endpoint = (cfg.discovery or {}).get("end_session_endpoint")
    if not endpoint:
        return None
    params = {
        "client_id": cfg.client_id,
        "post_logout_redirect_uri": build_absolute_uri(request, LOGIN_PATH),
    }
    if sso.get("id_token"):
        params["id_token_hint"] = sso["id_token"]
    sep = "&" if "?" in endpoint else "?"
    return f"{endpoint}{sep}{urlencode(params)}"
