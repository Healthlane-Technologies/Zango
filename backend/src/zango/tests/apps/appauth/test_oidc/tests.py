"""End-to-end tests for OIDC sign-in against a fake identity provider.

The fake provider signs real RS256 ID tokens, so these tests exercise the
zango_allauth verification code (signature, iss, aud, exp, nonce, userinfo
``sub``) as well as Zango's user resolution and login stages.
"""

import copy
import json
import time

from unittest import mock
from urllib.parse import parse_qs, urlparse

import jwt

from allauth.socialaccount.models import SocialAccount
from cryptography.hazmat.primitives.asymmetric import rsa

from django.core.cache import cache
from django.db import connection
from django.test import Client

from zango.apps.appauth.models import AppUserModel, OIDCProviderModel, UserRoleModel
from zango.apps.shared.tenancy.schema import DEFAULT_AUTH_CONFIG
from zango.test.cases import ZangoAppBaseTestCase


ISSUER = "https://idp.example.com"
CLIENT_ID = "zango-client"
CLIENT_SECRET = "s3cret-value-1234"
SLUG = "okta-corp"
CALLBACK = f"/api/v1/appauth/oidc/callback/{SLUG}/"

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_JWK = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(_KEY.public_key()))
_JWK.update({"kid": "k1", "use": "sig", "alg": "RS256"})

DISCOVERY = {
    "issuer": ISSUER,
    "authorization_endpoint": f"{ISSUER}/authorize",
    "token_endpoint": f"{ISSUER}/token",
    "userinfo_endpoint": f"{ISSUER}/userinfo",
    "jwks_uri": f"{ISSUER}/keys",
    "end_session_endpoint": f"{ISSUER}/logout",
    "id_token_signing_alg_values_supported": ["RS256"],
    "code_challenge_methods_supported": ["S256"],
    "token_endpoint_auth_methods_supported": ["client_secret_basic"],
}


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.headers = {"content-type": "application/json"}
        self.text = json.dumps(data)

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"{self.status_code}")


class FakeIdP:
    """Stands in for allauth's requests session."""

    def __init__(self):
        self.nonce = None
        self.claims = {}
        self.id_token_claims = {}
        self.userinfo = {}
        self.token_requests = []

    def base_claims(self):
        now = int(time.time())
        return {
            "iss": ISSUER,
            "aud": CLIENT_ID,
            "sub": "00u-priya",
            "email": "priya.raman@acme.com",
            "email_verified": True,
            "name": "Priya Raman",
            "iat": now,
            "exp": now + 300,
            "nonce": self.nonce,
        }

    def id_token(self):
        claims = {**self.base_claims(), **self.claims, **self.id_token_claims}
        claims = {k: v for k, v in claims.items() if v is not None}
        return jwt.encode(claims, _KEY, algorithm="RS256", headers={"kid": "k1"})

    def get(self, url, **kwargs):
        if url.endswith("/.well-known/openid-configuration"):
            return FakeResponse(DISCOVERY)
        if url == DISCOVERY["jwks_uri"]:
            return FakeResponse({"keys": [_JWK]})
        if url == DISCOVERY["userinfo_endpoint"]:
            claims = {**self.base_claims(), **self.claims, **self.userinfo}
            claims.pop("nonce", None)
            return FakeResponse({k: v for k, v in claims.items() if v is not None})
        return FakeResponse({"error": "not_found"}, 404)

    def request(self, method, url, **kwargs):
        if url == DISCOVERY["token_endpoint"]:
            self.token_requests.append(kwargs)
            return FakeResponse(
                {
                    "access_token": "at-123",
                    "token_type": "Bearer",
                    "expires_in": 300,
                    "id_token": self.id_token(),
                }
            )
        return self.get(url, **kwargs)


class OIDCTestBase(ZangoAppBaseTestCase):
    initialize_workspace = True

    @classmethod
    def get_test_module_path(cls):
        return "apps/appauth/test_oidc"

    def setUp(self):
        super().setUp()
        # The request middleware keeps the last request in a thread-local;
        # a previous test's request (and its session role) must not leak in.
        from zango.middleware.request import _request_local

        _request_local.__dict__.clear()
        connection.set_tenant(self.tenant)
        self.tenant.auth_config = copy.deepcopy(DEFAULT_AUTH_CONFIG)
        self.tenant.auth_config["login_methods"]["oidc"] = {"enabled": True}
        self.save_tenant()
        self.role = UserRoleModel.objects.create(name="qa_approver")
        result = AppUserModel.create_user(
            name="Priya Raman",
            email="priya.raman@acme.com",
            mobile="+919000000001",
            password="#Testpass123",
            role_ids=[self.role.id],
            require_verification=False,
            force_password_reset=False,
        )
        assert result["success"], result["message"]
        self.user = result["app_user"]
        self.provider = OIDCProviderModel.objects.create(
            slug=SLUG,
            label="Continue with Okta",
            icon="okta",
            issuer=ISSUER,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            discovery=DISCOVERY,
            rp_logout=True,
        )
        for key in (
            f"allauth:oidc:config:{ISSUER}/.well-known/openid-configuration",
            f"allauth:jwks:{DISCOVERY['jwks_uri']}",
        ):
            cache.delete(key)
        self.idp = FakeIdP()
        patcher = mock.patch(
            "allauth.socialaccount.adapter.DefaultSocialAccountAdapter.get_requests_session",
            return_value=self.idp,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = Client(HTTP_HOST=self.tenant.get_primary_domain().domain)

    # -- helpers ---------------------------------------------------------

    def save_tenant(self):
        # TenantModel.save() leaves the connection on the public schema.
        self.tenant.save()
        connection.set_tenant(self.tenant)

    def init(self, **body):
        body.setdefault("provider", SLUG)
        return self.client.post(
            "/api/v1/appauth/oidc/init/",
            data=json.dumps(body),
            content_type="application/json",
        )

    def start(self, next_url="/app/batches/"):
        resp = self.init(next=next_url)
        self.assertEqual(resp.status_code, 200, resp.content)
        url = json.loads(resp.content)["response"]["redirect_url"]
        params = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        self.idp.nonce = params.get("nonce")
        return url, params

    def callback(self, params, **query):
        query.setdefault("code", "auth-code-1")
        query.setdefault("state", params["state"])
        return self.client.get(CALLBACK, query)

    def sign_in(self):
        _, params = self.start()
        return self.callback(params)

    def status(self):
        resp = self.client.get("/api/v1/appauth/oidc/status/")
        return resp.status_code, json.loads(resp.content)["response"]

    def assertRejected(self, resp, code):
        self.assertEqual(resp.status_code, 302)
        query = parse_qs(urlparse(resp["Location"]).query)
        self.assertEqual(query.get("error"), [code], resp["Location"])
        self.assertEqual(query.get("sso"), ["oidc"])
        _, body = self.status()
        self.assertFalse(body["meta"]["is_authenticated"])
        self.assertEqual(body["meta"]["sso_error"]["code"], code)
        return body


class SignInTests:
    def test_init_returns_authorize_url_with_pkce_nonce_and_state(self):
        url, params = self.start()
        self.assertTrue(url.startswith(DISCOVERY["authorization_endpoint"]))
        self.assertEqual(params["client_id"], CLIENT_ID)
        self.assertEqual(params["response_type"], "code")
        self.assertEqual(params["code_challenge_method"], "S256")
        self.assertTrue(params["code_challenge"])
        self.assertTrue(params["nonce"])
        self.assertTrue(params["state"])
        self.assertTrue(params["redirect_uri"].endswith(CALLBACK))
        self.assertEqual(
            sorted(params["scope"].split()), ["email", "openid", "profile"]
        )

    def test_first_sign_in_links_by_verified_email(self):
        resp = self.sign_in()
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/app/login/?sso=oidc")
        account = SocialAccount.objects.get(provider=f"oidc-{SLUG}")
        self.assertEqual(account.uid, "00u-priya")
        self.assertEqual(account.user_id, self.user.id)
        # PKCE verifier went to the token endpoint, with client secret basic auth.
        token_request = self.idp.token_requests[0]
        self.assertTrue(token_request["data"]["code_verifier"])
        self.assertIsNotNone(token_request["auth"])

        status, body = self.status()
        self.assertEqual(status, 200)
        self.assertTrue(body["meta"]["is_authenticated"])
        self.assertEqual(body["meta"]["sso"], {"method": "oidc", "provider": SLUG})
        self.assertEqual(body["data"]["redirect_url"], "/app/batches/")
        self.assertEqual(body["data"]["user"]["id"], self.user.id)

    def test_later_sign_in_uses_subject_even_if_email_changed(self):
        self.sign_in()
        self.client.cookies.clear()
        self.idp.claims = {"email": "priya.r@new-domain.com"}
        resp = self.sign_in()
        self.assertEqual(resp["Location"], "/app/login/?sso=oidc")
        _, body = self.status()
        self.assertTrue(body["meta"]["is_authenticated"])
        self.assertEqual(SocialAccount.objects.filter(user=self.user).count(), 1)

    def test_unknown_email_is_rejected_without_creating_users(self):
        self.idp.claims = {"email": "r.mehta@acme.com", "sub": "00u-other"}
        users_before = AppUserModel.objects.count()
        body = self.assertRejected(self.sign_in(), "user_not_found")
        self.assertEqual(body["meta"]["sso_error"]["email"], "r.mehta@acme.com")
        self.assertEqual(AppUserModel.objects.count(), users_before)
        self.assertFalse(SocialAccount.objects.exists())

    def test_unverified_email_is_rejected(self):
        self.idp.claims = {"email_verified": False}
        self.assertRejected(self.sign_in(), "email_unverified")

    def test_missing_email_verified_needs_trust_email(self):
        self.idp.claims = {"email_verified": None}
        self.assertRejected(self.sign_in(), "email_unverified")
        self.client.cookies.clear()
        self.provider.trust_email = True
        self.provider.save()
        self.sign_in()
        _, body = self.status()
        self.assertTrue(body["meta"]["is_authenticated"])

    def test_explicit_unverified_email_is_rejected_even_when_trusted(self):
        self.provider.trust_email = True
        self.provider.save()
        self.idp.claims = {"email_verified": False}
        self.assertRejected(self.sign_in(), "email_unverified")

    def test_domain_allowlist(self):
        self.provider.allowed_email_domains = ["acme-pharma.in"]
        self.provider.save()
        self.assertRejected(self.sign_in(), "domain_not_allowed")

    def test_missing_email_claim(self):
        self.idp.claims = {"email": None}
        self.assertRejected(self.sign_in(), "email_missing")

    def test_custom_email_claim(self):
        self.provider.email_claim = "preferred_username"
        self.provider.save()
        self.idp.claims = {"email": None, "preferred_username": "priya.raman@acme.com"}
        self.sign_in()
        _, body = self.status()
        self.assertTrue(body["meta"]["is_authenticated"])

    def test_inactive_user_is_rejected(self):
        AppUserModel.objects.filter(id=self.user.id).update(is_active=False)
        self.assertRejected(self.sign_in(), "user_inactive")

    def test_user_without_active_role_is_rejected(self):
        UserRoleModel.objects.filter(id=self.role.id).update(is_active=False)
        self.assertRejected(self.sign_in(), "no_active_role")

    def test_identity_conflict(self):
        SocialAccount.objects.create(
            user=self.user, provider=f"oidc-{SLUG}", uid="00u-old", extra_data={}
        )
        self.assertRejected(self.sign_in(), "identity_conflict")

    def test_nonce_mismatch_is_rejected(self):
        _, params = self.start()
        self.idp.id_token_claims = {"nonce": "attacker-nonce"}
        self.assertRejected(self.callback(params), "id_token_invalid")

    def test_wrong_audience_is_rejected(self):
        self.idp.id_token_claims = {"aud": "another-client"}
        self.assertRejected(self.sign_in(), "id_token_invalid")

    def test_expired_id_token_is_rejected(self):
        now = int(time.time())
        self.idp.id_token_claims = {"iat": now - 3600, "exp": now - 1800}
        self.assertRejected(self.sign_in(), "id_token_invalid")

    def test_wrong_issuer_is_rejected(self):
        self.idp.id_token_claims = {"iss": "https://evil.example.com"}
        self.assertRejected(self.sign_in(), "id_token_invalid")

    def test_userinfo_subject_mismatch_is_rejected(self):
        self.idp.userinfo = {"sub": "00u-someone-else"}
        self.assertRejected(self.sign_in(), "id_token_invalid")

    def test_state_cannot_be_replayed(self):
        _, params = self.start()
        self.callback(params)
        self.client.post("/api/v1/appauth/logout/")
        resp = self.client.delete("/api/v1/appauth/logout/")
        self.assertIn(resp.status_code, (200, 401))
        self.assertRejected(self.callback(params), "state_mismatch")

    def test_cancel_at_provider(self):
        _, params = self.start()
        resp = self.client.get(
            CALLBACK, {"error": "access_denied", "state": params["state"]}
        )
        self.assertRejected(resp, "cancelled")

    def test_init_refused_when_oidc_disabled(self):
        self.tenant.auth_config["login_methods"]["oidc"]["enabled"] = False
        self.save_tenant()
        resp = self.init()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.content)["response"]["code"], "oidc_disabled")

    def test_init_refused_for_inactive_provider(self):
        self.provider.is_active = False
        self.provider.save()
        resp = self.init()
        self.assertEqual(resp.status_code, 404)

    def test_next_must_be_a_relative_path(self):
        _, params = self.start(next_url="https://evil.example.com/")
        self.callback(params)
        _, body = self.status()
        self.assertEqual(body["data"]["redirect_url"], "/app")

    def test_logout_returns_provider_end_session_url(self):
        self.sign_in()
        self.status()
        resp = self.client.delete("/api/v1/appauth/logout/")
        body = json.loads(resp.content)["response"]
        url = urlparse(body["idp_logout_url"])
        query = parse_qs(url.query)
        self.assertEqual(f"{url.scheme}://{url.netloc}{url.path}", f"{ISSUER}/logout")
        self.assertEqual(query["client_id"], [CLIENT_ID])
        self.assertTrue(query["id_token_hint"][0])
        self.assertTrue(query["post_logout_redirect_uri"][0].endswith("/app/login/"))


class TwoFactorTests:
    def set_two_factor(self, **policy):
        self.tenant.auth_config["two_factor_auth"] = {
            "required": True,
            "allowed_methods": ["email"],
            **policy,
        }
        self.save_tenant()

    def test_two_factor_still_applies_after_sso_by_default(self):
        self.set_two_factor()
        self.sign_in()
        status, body = self.status()
        self.assertEqual(status, 401)
        self.assertFalse(body["meta"]["is_authenticated"])
        next_step = body["data"]["next_step"]
        self.assertEqual(next_step["id"], "mfa_authenticate")
        # SSO identities are email based, so the second factor goes by SMS.
        self.assertEqual(next_step["metadata"]["type"], "sms")

    def test_skip_for_sso_skips_two_factor(self):
        self.set_two_factor(skip_for_sso=True)
        self.sign_in()
        status, body = self.status()
        self.assertEqual(status, 200)
        self.assertTrue(body["meta"]["is_authenticated"])

    def test_is_sso_login_follows_latest_primary_authentication(self):
        from types import SimpleNamespace

        from allauth.account.utils import is_sso_login

        def req(*methods, **session):
            records = [{"method": m} for m in methods]
            return SimpleNamespace(
                session={"account_authentication_methods": records, **session}
            )

        self.assertTrue(is_sso_login(req("socialaccount")))
        self.assertTrue(is_sso_login(req("socialaccount", "mfa")))
        # Password after an abandoned SSO attempt is not SSO.
        self.assertFalse(is_sso_login(req("socialaccount", "password")))
        self.assertFalse(is_sso_login(req()))
        self.assertTrue(is_sso_login(req(saml=True)))


class AuthConfigTests:
    def test_providers_injected_without_mutating_tenant_config(self):
        from zango.core.utils import get_auth_priority

        stored = copy.deepcopy(self.tenant.auth_config)
        for _ in range(3):
            config = get_auth_priority(tenant=self.tenant)
        self.assertEqual(
            config["login_methods"]["oidc"]["providers"],
            [{"slug": SLUG, "label": "Continue with Okta", "icon": "okta"}],
        )
        self.assertEqual(self.tenant.auth_config, stored)
        self.assertEqual(DEFAULT_AUTH_CONFIG["login_methods"]["oidc"]["providers"], [])

    def test_config_endpoint_lists_providers_without_secrets(self):
        resp = self.client.get("/api/v1/appauth/config/")
        body = resp.content.decode()
        self.assertIn(SLUG, body)
        self.assertNotIn(CLIENT_SECRET, body)
        self.assertNotIn(CLIENT_ID, body)

    def test_client_secret_is_encrypted_at_rest(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT client_secret FROM appauth_oidcprovidermodel WHERE id = %s",
                [self.provider.id],
            )
            stored = cursor.fetchone()[0]
        self.assertNotIn(CLIENT_SECRET, stored)
        fresh = OIDCProviderModel.objects.get(id=self.provider.id)
        self.assertEqual(fresh.get_client_secret(), CLIENT_SECRET)


class ProviderSerializerTests:
    def serializer(self, data, instance=None):
        from zango.api.platform.tenancy.v1.serializers import OIDCProviderSerializer

        return OIDCProviderSerializer(
            instance=instance,
            data=data,
            partial=instance is not None,
            context={"tenant": self.tenant},
        )

    def valid_data(self, **overrides):
        data = {
            "slug": "entra-partners",
            "label": "Continue with Microsoft",
            "issuer": ISSUER,
            "client_id": "entra-client",
            "client_secret": "another-secret",
        }
        data.update(overrides)
        return data

    def fetch(self):
        return mock.patch(
            "zango.apps.appauth.oidc.fetch.fetch_json", return_value=DISCOVERY
        )

    def test_create_fetches_discovery_and_hides_secret(self):
        with self.fetch():
            s = self.serializer(self.valid_data())
            self.assertTrue(s.is_valid(), s.errors)
            obj = s.save()
        self.assertEqual(obj.discovery["issuer"], ISSUER)
        data = self.serializer(None, instance=obj).to_representation(obj)
        self.assertNotIn("client_secret", data)
        self.assertTrue(data["has_client_secret"])
        self.assertEqual(data["client_secret_last4"], "cret")
        self.assertEqual(
            data["callback_url"],
            f"https://{self.tenant.get_primary_domain().domain}/api/v1/appauth/oidc/callback/entra-partners/",
        )

    def test_issuer_must_match_discovery(self):
        with self.fetch():
            s = self.serializer(self.valid_data(issuer="https://idp.example.com/v2"))
            self.assertFalse(s.is_valid())
        self.assertIn("issuer", s.errors)

    def test_scopes_must_include_openid(self):
        with self.fetch():
            s = self.serializer(self.valid_data(scopes=["email", "profile"]))
            self.assertFalse(s.is_valid())
        self.assertIn("scopes", s.errors)

    def test_reserved_auth_params_rejected(self):
        with self.fetch():
            s = self.serializer(self.valid_data(extra_auth_params={"nonce": "x"}))
            self.assertFalse(s.is_valid())
        self.assertIn("extra_auth_params", s.errors)

    def test_secret_required_unless_public_client_with_pkce(self):
        with self.fetch():
            s = self.serializer(self.valid_data(client_secret=""))
            self.assertFalse(s.is_valid())
            self.assertIn("client_secret", s.errors)
            s = self.serializer(
                self.valid_data(
                    client_secret="", token_auth_method="none", use_pkce=False
                )
            )
            self.assertFalse(s.is_valid())
            self.assertIn("use_pkce", s.errors)
            s = self.serializer(
                self.valid_data(client_secret="", token_auth_method="none")
            )
            self.assertTrue(s.is_valid(), s.errors)

    def test_update_without_secret_keeps_it(self):
        s = self.serializer({"label": "Okta"}, instance=self.provider)
        self.assertTrue(s.is_valid(), s.errors)
        obj = s.save()
        obj.refresh_from_db()
        self.assertEqual(obj.get_client_secret(), CLIENT_SECRET)

    def test_slug_locked_once_users_are_linked(self):
        SocialAccount.objects.create(
            user=self.user, provider=f"oidc-{SLUG}", uid="00u-priya", extra_data={}
        )
        s = self.serializer({"slug": "okta-new"}, instance=self.provider)
        self.assertFalse(s.is_valid())
        self.assertIn("slug", s.errors)

    def test_enforce_sso_allowed_with_oidc_only(self):
        from zango.api.platform.tenancy.v1.serializers import sso_login_enabled

        self.assertTrue(sso_login_enabled(self.tenant.auth_config))
        self.tenant.auth_config["login_methods"]["oidc"]["enabled"] = False
        self.assertFalse(sso_login_enabled(self.tenant.auth_config))


class OIDCTests(
    SignInTests,
    TwoFactorTests,
    AuthConfigTests,
    ProviderSerializerTests,
    OIDCTestBase,
):
    """One TestCase: Zango's teardown deletes the shared test tenant per class."""
