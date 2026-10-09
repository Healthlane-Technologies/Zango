"""allauth social account adapter for Zango OIDC sign-in.

Providers come from ``OIDCProviderModel`` (never ``SocialApp`` rows). Users are
never created here: the first sign-in links an existing app user by verified
email, later sign-ins resolve through the ``(provider, sub)`` link.
"""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.base.constants import AuthError
from allauth.socialaccount.providers.oauth2.client import OAuth2Error

from django.db import connection

from zango.apps.appauth.models import AppUserModel, OIDCProviderModel

from . import errors
from .utils import SSO_SESSION_KEY, oidc_enabled


class ZangoSocialAccountAdapter(DefaultSocialAccountAdapter):
    def list_apps(self, request, provider=None, client_id=None):
        if getattr(connection, "tenant", None) is None or (
            getattr(connection.tenant, "tenant_type", None) != "app"
        ):
            return []
        apps = [
            row.as_social_app()
            for row in OIDCProviderModel.objects.filter(is_active=True)
        ]
        if provider:
            apps = [a for a in apps if provider in (a.provider, a.provider_id)]
        if client_id:
            apps = [a for a in apps if a.client_id == client_id]
        return apps

    # A pending login stage (MFA, role selection) stashes the SocialLogin in
    # the session. AppUserModel has fields allauth cannot auto-serialize
    # (PhoneNumberField), and the user always exists here, so stash its pk.
    _USER_PK_KEY = "__zango_app_user_pk__"

    def serialize_instance(self, instance):
        if isinstance(instance, AppUserModel) and instance.pk:
            return {self._USER_PK_KEY: instance.pk}
        return super().serialize_instance(instance)

    def deserialize_instance(self, model, data):
        if isinstance(data, dict) and self._USER_PK_KEY in data:
            return AppUserModel.objects.get(pk=data[self._USER_PK_KEY])
        return super().deserialize_instance(model, data)

    def is_open_for_signup(self, request, sociallogin):
        return False

    def is_auto_signup_allowed(self, request, sociallogin):
        return False

    def pre_social_login(self, request, sociallogin):
        provider_id = sociallogin.account.provider
        slug = OIDCProviderModel.slug_from_provider_id(provider_id)
        if slug is None:
            return
        claims = sociallogin.account.extra_data or {}
        cfg = OIDCProviderModel.objects.filter(slug=slug).first()

        if not oidc_enabled(request):
            raise errors.sso_error(request, errors.OIDC_DISABLED, slug)
        if cfg is None or not cfg.is_active:
            raise errors.sso_error(request, errors.PROVIDER_INACTIVE, slug)
        if (sociallogin.state or {}).get("oidc_provider") != slug:
            # The state was issued for another provider (mix-up) or not by us.
            raise errors.sso_error(
                request,
                errors.STATE_MISMATCH,
                slug,
                detail=f"state provider {sociallogin.state.get('oidc_provider')!r}",
            )

        email = _claim_str(claims, cfg.email_claim)
        if email and not _domain_allowed(cfg, email):
            raise errors.sso_error(request, errors.DOMAIN_NOT_ALLOWED, slug, email)

        if sociallogin.is_existing:
            user = sociallogin.user
        else:
            user = self._resolve_by_email(request, cfg, claims, email)
            sociallogin.connect(request, user)

        if not user.is_active:
            raise errors.sso_error(request, errors.USER_INACTIVE, slug, user.email)
        if not user.roles.filter(is_active=True).exists():
            raise errors.sso_error(request, errors.NO_ACTIVE_ROLE, slug, user.email)

        request.session[SSO_SESSION_KEY] = {
            "method": "oidc",
            "provider": slug,
            "id_token": getattr(sociallogin, "id_token", None),
        }
        request.session.pop(errors.SSO_ERROR_SESSION_KEY, None)

    def _resolve_by_email(self, request, cfg, claims, email):
        slug = cfg.slug
        if not email:
            raise errors.sso_error(request, errors.EMAIL_MISSING, slug)
        verified = claims.get("email_verified")
        if isinstance(verified, str):
            verified = verified.lower() == "true"
        if verified is False or (verified is None and not cfg.trust_email):
            raise errors.sso_error(request, errors.EMAIL_UNVERIFIED, slug, email)
        user = AppUserModel.objects.filter(email__iexact=email).first()
        if user is None:
            raise errors.sso_error(request, errors.USER_NOT_FOUND, slug, email)
        if cfg.linked_identities().filter(user=user).exists():
            # Already linked to another subject at this provider.
            raise errors.sso_error(request, errors.IDENTITY_CONFLICT, slug, email)
        return user

    def on_authentication_error(
        self, request, provider, error=None, exception=None, extra_context=None
    ):
        app = getattr(provider, "app", None)
        slug = OIDCProviderModel.slug_from_provider_id(
            getattr(app, "provider_id", None)
        )
        if slug is None:
            return super().on_authentication_error(
                request,
                provider,
                error=error,
                exception=exception,
                extra_context=extra_context,
            )
        extra_context = extra_context or {}
        if error == AuthError.CANCELLED:
            code = errors.CANCELLED
        elif "callback_view" in extra_context and extra_context.get("state") is None:
            code = errors.STATE_MISMATCH
        elif isinstance(exception, OAuth2Error) and _is_token_check(exception):
            code = errors.ID_TOKEN_INVALID
        else:
            code = errors.IDP_ERROR
        detail = repr(exception) if exception else request.GET.get("error_description")
        raise errors.sso_error(request, code, slug, detail=detail)


def _claim_str(claims, name):
    value = claims.get(name)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _domain_allowed(cfg, email):
    domains = [d.lower() for d in (cfg.allowed_email_domains or [])]
    if not domains:
        return True
    return email.rsplit("@", 1)[-1].lower() in domains


def _is_token_check(exception):
    text = str(exception).lower()
    if exception.__cause__ is not None:
        text += " " + str(exception.__cause__).lower()
    return any(
        marker in text
        for marker in ("id_token", "nonce", "azp", "kid", "'sub'", "algorithm")
    )
