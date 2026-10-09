import time
import traceback

from django.utils import timezone
from django.utils.decorators import method_decorator

from zango.apps.appauth.models import AppUserModel, OIDCProviderModel
from zango.apps.appauth.oidc.fetch import (
    FetchError,
    discovery_url,
    fetch_discovery,
    fetch_json,
    safe_request,
)
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response
from zango.core.api.mixin import TenantMixin
from zango.core.common_utils import set_app_schema_path
from zango.core.permissions import IsPlatformUserAllowedApp

from .serializers import OIDCProviderSerializer, get_sso_identities


def _errors(serializer):
    return {field: [str(e) for e in errs] for field, errs in serializer.errors.items()}


class _OIDCBase(ZangoGenericPlatformAPIView, TenantMixin):
    permission_classes = (IsPlatformUserAllowedApp,)

    def serializer(self, *args, **kwargs):
        context = {"tenant": self.get_tenant(**self.kwargs), "request": self.request}
        return OIDCProviderSerializer(*args, context=context, **kwargs)

    def get_obj(self):
        return OIDCProviderModel.objects.filter(
            id=self.kwargs.get("oidc_provider_id")
        ).first()

    def not_found(self):
        return get_api_response(
            False,
            {
                "message": f"OIDC provider '{self.kwargs.get('oidc_provider_id')}' not found"
            },
            404,
        )


@method_decorator(set_app_schema_path, name="dispatch")
class OIDCProvidersViewAPIV1(_OIDCBase):
    def get(self, request, *args, **kwargs):
        try:
            providers = OIDCProviderModel.objects.all().order_by("display_order", "id")
            data = self.serializer(providers, many=True).data
            return get_api_response(
                True,
                {
                    "oidc_providers": data,
                    "count": len(data),
                    "message": "OIDC providers fetched",
                },
                200,
            )
        except Exception as e:
            traceback.print_exc()
            return get_api_response(
                False, {"message": f"Error fetching OIDC providers: {e}"}, 500
            )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer(data=request.data)
        if not serializer.is_valid():
            return get_api_response(
                False,
                {
                    "message": "OIDC provider was not created",
                    "errors": _errors(serializer),
                },
                400,
            )
        obj = serializer.save()
        return get_api_response(
            True,
            {
                "message": "OIDC provider created",
                "oidc_provider_id": obj.id,
                "oidc_provider": self.serializer(obj).data,
                "warnings": serializer.get_warnings(obj),
            },
            201,
        )


@method_decorator(set_app_schema_path, name="dispatch")
class OIDCProviderDetailViewAPIV1(_OIDCBase):
    def get(self, request, *args, **kwargs):
        obj = self.get_obj()
        if obj is None:
            return self.not_found()
        data = self.serializer(obj).data
        data["discovery"] = obj.discovery
        return get_api_response(
            True, {"oidc_provider": data, "message": "OIDC provider fetched"}, 200
        )

    def put(self, request, *args, **kwargs):
        obj = self.get_obj()
        if obj is None:
            return self.not_found()
        serializer = self.serializer(instance=obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return get_api_response(
                False,
                {
                    "message": "OIDC provider was not updated",
                    "errors": _errors(serializer),
                },
                400,
            )
        obj = serializer.save()
        return get_api_response(
            True,
            {
                "message": "OIDC provider updated",
                "oidc_provider_id": obj.id,
                "oidc_provider": self.serializer(obj).data,
                "warnings": serializer.get_warnings(obj),
            },
            200,
        )

    def delete(self, request, *args, **kwargs):
        obj = self.get_obj()
        if obj is None:
            return self.not_found()
        linked = obj.linked_identities()
        force = str(request.GET.get("force", "")).lower() == "true"
        if linked.exists() and not force:
            return get_api_response(
                False,
                {
                    "code": "provider_in_use",
                    "message": f"{linked.count()} users are linked to this provider. Pass ?force=true to delete it and remove the links.",
                },
                409,
            )
        removed = linked.count()
        linked.delete()
        obj.delete()
        return get_api_response(
            True,
            {"message": "OIDC provider deleted", "removed_identities": removed},
            200,
        )


@method_decorator(set_app_schema_path, name="dispatch")
class OIDCDiscoverViewAPIV1(_OIDCBase):
    """Fetches a discovery document without saving anything."""

    def post(self, request, *args, **kwargs):
        issuer = (request.data.get("issuer") or "").strip()
        if not issuer:
            return get_api_response(False, {"message": "issuer is required"}, 400)
        try:
            config = fetch_discovery(issuer)
        except FetchError as e:
            return get_api_response(False, {"message": str(e)}, 400)
        keys = (
            "issuer",
            "authorization_endpoint",
            "token_endpoint",
            "userinfo_endpoint",
            "jwks_uri",
            "end_session_endpoint",
            "scopes_supported",
            "claims_supported",
            "token_endpoint_auth_methods_supported",
            "code_challenge_methods_supported",
            "id_token_signing_alg_values_supported",
        )
        result = {k: config.get(k) for k in keys if k in config}
        methods = config.get("token_endpoint_auth_methods_supported") or [
            "client_secret_basic"
        ]
        result["suggested"] = {
            "token_auth_method": "client_secret_basic"
            if "client_secret_basic" in methods
            else "client_secret_post",
            "use_pkce": "S256"
            in (config.get("code_challenge_methods_supported") or []),
        }
        return get_api_response(True, result, 200)


def _check(check_id, status, detail=None, started=None):
    out = {"id": check_id, "status": status}
    if detail:
        out["detail"] = detail
    if started is not None:
        out["ms"] = int((time.monotonic() - started) * 1000)
    return out


@method_decorator(set_app_schema_path, name="dispatch")
class OIDCProviderTestViewAPIV1(_OIDCBase):
    """Server-side connection checks. No real user is involved."""

    def post(self, request, *args, **kwargs):
        obj = self.get_obj()
        if obj is None:
            return self.not_found()
        checks = []

        started = time.monotonic()
        try:
            config = fetch_json(discovery_url(obj.issuer))
            checks.append(_check("discovery", "pass", "200", started))
        except FetchError as e:
            checks.append(_check("discovery", "fail", str(e), started))
            return get_api_response(True, {"ok": False, "checks": checks}, 200)

        if config.get("issuer") == obj.issuer:
            checks.append(_check("issuer_match", "pass"))
        else:
            checks.append(
                _check(
                    "issuer_match",
                    "fail",
                    f"Document issuer '{config.get('issuer')}' differs from '{obj.issuer}'",
                )
            )

        started = time.monotonic()
        try:
            jwks = fetch_json(config.get("jwks_uri") or "")
            keys = [k for k in jwks.get("keys", []) if k.get("use", "sig") == "sig"]
            algs = sorted({k.get("alg") or k.get("kty") for k in keys})
            status = "pass" if keys else "fail"
            checks.append(
                _check("jwks", status, f"{len(keys)} keys ({', '.join(algs)})", started)
            )
        except (FetchError, AttributeError) as e:
            checks.append(_check("jwks", "fail", str(e), started))

        checks.append(self._client_auth_check(obj, config))

        supported = config.get("code_challenge_methods_supported")
        if not obj.use_pkce:
            checks.append(_check("pkce", "warn", "PKCE is turned off"))
        elif supported is None:
            checks.append(
                _check("pkce", "warn", "Provider does not advertise PKCE methods")
            )
        elif "S256" in supported:
            checks.append(_check("pkce", "pass"))
        else:
            checks.append(_check("pkce", "fail", "S256 is not supported"))

        claims = config.get("claims_supported")
        if (
            not obj.trust_email
            and claims is not None
            and "email_verified" not in claims
        ):
            checks.append(
                _check(
                    "email_claim",
                    "warn",
                    "Provider may not send email_verified; first sign-in will not link users unless emails are trusted",
                )
            )
        else:
            checks.append(_check("email_claim", "pass"))

        ok = all(c["status"] != "fail" for c in checks)
        if ok:
            obj.discovery = config
            obj.discovery_fetched_at = timezone.now()
            obj.save(update_fields=["discovery", "discovery_fetched_at", "modified_at"])
        return get_api_response(True, {"ok": ok, "checks": checks}, 200)

    def _client_auth_check(self, obj, config):
        token_endpoint = config.get("token_endpoint")
        if not token_endpoint:
            return _check("client_auth", "fail", "No token_endpoint in discovery")
        serializer = self.serializer(obj)
        data = {
            "grant_type": "authorization_code",
            "code": "zango-connection-test",
            "redirect_uri": serializer.get_callback_url(obj),
        }
        auth = None
        if obj.token_auth_method == "client_secret_basic":
            auth = (obj.client_id, obj.get_client_secret())
        else:
            data["client_id"] = obj.client_id
            if obj.token_auth_method == "client_secret_post":
                data["client_secret"] = obj.get_client_secret()
        started = time.monotonic()
        try:
            resp, body = safe_request("POST", token_endpoint, data=data, auth=auth)
        except FetchError as e:
            return _check("client_auth", "fail", str(e), started)
        try:
            import json

            error = json.loads(body).get("error")
        except (ValueError, AttributeError):
            error = None
        if error == "invalid_grant":
            return _check("client_auth", "pass", "invalid_grant (expected)", started)
        if (
            error in ("invalid_client", "unauthorized_client")
            or resp.status_code == 401
        ):
            return _check(
                "client_auth", "fail", f"{error or resp.status_code}", started
            )
        return _check(
            "client_auth",
            "warn",
            f"Unexpected response: {error or resp.status_code}",
            started,
        )


@method_decorator(set_app_schema_path, name="dispatch")
class AppUserIdentitiesViewAPIV1(ZangoGenericPlatformAPIView, TenantMixin):
    """Linked SSO identities of an app user."""

    permission_classes = (IsPlatformUserAllowedApp,)

    def get(self, request, *args, **kwargs):
        user = AppUserModel.objects.filter(id=kwargs.get("user_id")).first()
        if user is None:
            return get_api_response(False, {"message": "User not found"}, 404)
        tenant = self.get_tenant(**kwargs)
        return get_api_response(
            True, {"identities": get_sso_identities(user, tenant)}, 200
        )

    def delete(self, request, *args, **kwargs):
        from allauth.socialaccount.models import SocialAccount

        account = SocialAccount.objects.filter(
            id=kwargs.get("identity_id"), user_id=kwargs.get("user_id")
        ).first()
        if account is None:
            return get_api_response(False, {"message": "Identity not found"}, 404)
        account.delete()
        return get_api_response(True, {"message": "Identity unlinked"}, 200)
