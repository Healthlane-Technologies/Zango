import json
import re

from django_tenants.utils import schema_context
from rest_framework import serializers

from zango.api.platform.permissions.v1.serializers import PolicySerializer
from zango.apps.appauth.mixin import UserAuthConfigValidationMixin
from zango.apps.appauth.models import (
    AppUserModel,
    OIDCProviderModel,
    SAMLModel,
    UserRoleModel,
)
from zango.apps.appauth.schema import UserRoleAuthConfig
from zango.apps.shared.tenancy.models import Domain, TenantModel, ThemesModel
from zango.apps.shared.tenancy.schema import AuthConfigSchema as TenantAuthConfigSchema
from zango.core.utils import get_auth_priority, get_datetime_str_in_tenant_timezone


# Upper bound for a configurable token TTL: 1 year in seconds. Guards against an
# accidental huge value being mistaken for the explicit 0 ("never expires") sentinel.
MAX_TOKEN_TTL_SECONDS = 31536000

# Upper bound for the idle-session timeout: 24 hours in seconds. An idle window
# longer than a day is almost certainly a misconfiguration.
MAX_SESSION_TIMEOUT_SECONDS = 86400


def get_platform_session_timeout_seconds():
    """Platform-wide default idle-session timeout as ``(warn_after, expire_after)``.

    Mirrors the fallback used by ``get_app_session_timeout`` so the UI can show
    the effective value when an app/role inherits ("Platform default").
    """
    from django.conf import settings

    warn = int(getattr(settings, "SESSION_SECURITY_WARN_AFTER", 1700))
    expire = int(getattr(settings, "SESSION_SECURITY_EXPIRE_AFTER", 1800))
    return warn, expire


def get_platform_token_ttl_seconds():
    """Platform-wide default token TTL in seconds (0 means "never expires").

    Derived from the Knox setting so it matches the actual fallback used when an
    app/role does not configure its own ``token_ttl``.
    """
    from knox.settings import knox_settings

    ttl = knox_settings.TOKEN_TTL
    return 0 if ttl is None else int(ttl.total_seconds())


def sso_login_enabled(auth_config):
    """True when SAML or OpenID Connect sign-in is on in this auth config."""
    login_methods = (auth_config or {}).get("login_methods", {})
    return any(
        login_methods.get(method, {}).get("enabled", False)
        for method in ("sso", "oidc")
    )


def get_sso_identities(user, tenant=None):
    """OIDC identities linked to an app user (allauth SocialAccount rows)."""
    from allauth.socialaccount.models import SocialAccount

    from zango.apps.appauth.models import OIDCProviderModel

    identities = []
    for account in SocialAccount.objects.filter(user=user).order_by("id"):
        slug = OIDCProviderModel.slug_from_provider_id(account.provider)
        if slug is None:
            continue
        extra = account.extra_data or {}
        identities.append(
            {
                "id": account.id,
                "method": "oidc",
                "provider": slug,
                "uid": account.uid,
                "email": extra.get("email"),
                "linked_at": get_datetime_str_in_tenant_timezone(
                    account.date_joined, tenant
                )
                if tenant
                else account.date_joined.isoformat(),
                "last_login_at": get_datetime_str_in_tenant_timezone(
                    account.last_login, tenant
                )
                if tenant
                else account.last_login.isoformat(),
            }
        )
    return identities


def validate_session_policy_token_ttl(auth_config):
    """Validate ``session_policy.token_ttl`` if present in an auth_config dict.

    ``token_ttl`` is seconds (int). ``0`` means "never expires". Absence means
    "inherit" and is always valid. Raises ``serializers.ValidationError`` otherwise.
    """
    session_policy = (auth_config or {}).get("session_policy")
    if not session_policy or "token_ttl" not in session_policy:
        return
    ttl = session_policy["token_ttl"]
    # bool is a subclass of int -- reject it explicitly.
    if isinstance(ttl, bool) or not isinstance(ttl, int):
        raise serializers.ValidationError(
            "session_policy.token_ttl must be an integer number of seconds "
            "(0 means the token never expires)."
        )
    if ttl < 0:
        raise serializers.ValidationError(
            "session_policy.token_ttl cannot be negative."
        )
    if ttl > MAX_TOKEN_TTL_SECONDS:
        raise serializers.ValidationError(
            f"session_policy.token_ttl cannot exceed {MAX_TOKEN_TTL_SECONDS} "
            "seconds (1 year). Use 0 for a token that never expires."
        )


def _validate_positive_seconds(session_policy, key):
    """Validate an optional positive-int-seconds ``key`` in ``session_policy``.

    Absence = inherit = valid. bool is rejected explicitly (it subclasses int).
    Returns the value (or ``None`` if absent) for cross-field checks.
    """
    if key not in session_policy:
        return None
    val = session_policy[key]
    if isinstance(val, bool) or not isinstance(val, int):
        raise serializers.ValidationError(
            f"session_policy.{key} must be an integer number of seconds."
        )
    if val <= 0:
        raise serializers.ValidationError(
            f"session_policy.{key} must be a positive number of seconds."
        )
    if val > MAX_SESSION_TIMEOUT_SECONDS:
        raise serializers.ValidationError(
            f"session_policy.{key} cannot exceed {MAX_SESSION_TIMEOUT_SECONDS} "
            "seconds (24 hours)."
        )
    return val


def validate_session_policy_timeout(auth_config):
    """Validate ``session_policy.session_warn_after`` / ``session_expire_after``.

    Both are optional seconds (positive int); absence = inherit. When both are
    set, ``warn_after`` must be strictly less than ``expire_after``.
    """
    session_policy = (auth_config or {}).get("session_policy")
    if not session_policy:
        return
    warn = _validate_positive_seconds(session_policy, "session_warn_after")
    expire = _validate_positive_seconds(session_policy, "session_expire_after")
    if warn is not None and expire is not None and warn >= expire:
        raise serializers.ValidationError(
            "session_policy.session_warn_after must be less than "
            "session_expire_after."
        )


# Read-only, server-computed hint keys added on read and stripped on write.
_PLATFORM_HINT_KEYS = (
    "platform_token_ttl",
    "platform_session_warn_after",
    "platform_session_expire_after",
)


def inject_platform_session_hints(data):
    """Add read-only platform-default hints under ``auth_config.session_policy``.

    Lets the UI show the effective inherited value ("Platform default") for token
    TTL and idle timeout. Read-only: stripped again on write. Mutates and returns
    ``data`` (a serialized dict) for convenience.
    """
    auth_config = data.get("auth_config")
    if isinstance(auth_config, dict):
        session_policy = dict(auth_config.get("session_policy") or {})
        warn, expire = get_platform_session_timeout_seconds()
        session_policy["platform_token_ttl"] = get_platform_token_ttl_seconds()
        session_policy["platform_session_warn_after"] = warn
        session_policy["platform_session_expire_after"] = expire
        auth_config["session_policy"] = session_policy
    return data


def strip_platform_session_hints(value):
    """Remove read-only platform hint keys from an inbound auth_config dict."""
    if isinstance(value, dict) and isinstance(value.get("session_policy"), dict):
        for key in _PLATFORM_HINT_KEYS:
            value["session_policy"].pop(key, None)


class DomainSerializerModel(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["domain", "is_primary"]


class TenantSerializerModel(serializers.ModelSerializer):
    domains = DomainSerializerModel(many=True, required=False)
    domain_url = serializers.SerializerMethodField("get_domain_url")
    datetime_format_display = serializers.SerializerMethodField(
        "get_datetime_format_display"
    )
    date_format_display = serializers.SerializerMethodField("get_date_format_display")
    deployment_config = serializers.SerializerMethodField("get_deployment_config")
    last_released_version = serializers.SerializerMethodField(
        "get_last_released_version"
    )
    auth_config = serializers.JSONField(required=False)

    def get_last_released_version(self, obj):
        try:
            from django_tenants.utils import schema_context

            with schema_context(obj.schema_name):
                from zango.apps.release.models import AppRelease

                latest_release = (
                    AppRelease.objects.filter(
                        status="released",
                    )
                    .order_by("-created_at")
                    .first()
                    .version
                )
        except Exception:
            latest_release = None
        return latest_release

    def get_deployment_config(self, obj):
        try:
            with open(f"workspaces/{obj.name}/settings.json") as f:
                settings = json.load(f)
                depl_config = settings.get("deployment", {})
                return depl_config
        except Exception:
            return {}

    class Meta:
        model = TenantModel
        read_only_fields = ("name", "schema_name")
        fields = "__all__"

    def get_domain_url(self, obj):
        primary_domain = obj.get_primary_domain()
        if primary_domain:
            return primary_domain.domain
        return None

    def get_datetime_format_display(self, obj):
        return obj.get_datetime_format_display()

    def get_date_format_display(self, obj):
        return obj.get_date_format_display()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Surface platform-wide defaults (token TTL + idle timeout) alongside the
        # app's auth_config so the UI can show the effective value when an app/role
        # inherits ("Platform default"). Read-only, ignored on write.
        return inject_platform_session_hints(data)

    def validate_auth_config(self, value: TenantAuthConfigSchema):
        # platform_* hints are read-only, server-computed; never persist them.
        strip_platform_session_hints(value)
        validate_session_policy_token_ttl(value)
        validate_session_policy_timeout(value)
        return value

    def update(self, instance, validated_data):
        request = self.context["request"]
        extra_config_str = request.data.get("extra_config")
        # Convert extra_config from string to JSON if it exists
        if extra_config_str:
            try:
                extra_config_json = json.loads(extra_config_str)
                default_branch_config = {
                    "dev": "development",
                    "staging": "staging",
                    "prod": "main",
                }
                if extra_config_json.get("git_config", None):
                    if extra_config_json["git_config"].get("repo_url", None):
                        extra_config_json["git_config"]["branch"] = {
                            **extra_config_json["git_config"]["branch"],
                            **{
                                k: v
                                for k, v in default_branch_config.items()
                                if extra_config_json["git_config"]["branch"][k] is None
                            },
                        }
                validated_data["extra_config"] = extra_config_json
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    {"extra_config": "Invalid JSON format"}
                )

        # Handle domains from validated_data (nested serializer data) or request data
        domains_data = validated_data.pop("domains", None)
        instance = super(TenantSerializerModel, self).update(instance, validated_data)

        # Check if domains are passed as JSON string in request data
        domains_json_str = request.data.get("domains")
        if domains_json_str:
            try:
                domains_data = json.loads(domains_json_str)
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    {"domains": "Invalid JSON format for domains"}
                )

        if domains_data is not None:
            # Remove all existing domains for this tenant
            instance.domains.all().delete()

            # Create new domains with is_primary flags
            for domain_data in domains_data:
                Domain.objects.create(
                    domain=domain_data["domain"],
                    is_primary=domain_data.get("is_primary", False),
                    tenant=instance,
                )

        if "auth_config" in validated_data:
            auth_config = validated_data["auth_config"]
            if not sso_login_enabled(auth_config):
                with schema_context(instance.schema_name):
                    for role in UserRoleModel.objects.all():
                        if role.auth_config.get("enforce_sso", False):
                            role.auth_config["enforce_sso"] = False
                            role.save()
        return instance


class UserRoleSerializerModel(serializers.ModelSerializer):
    attached_policies = serializers.SerializerMethodField()
    policies_count = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    auth_config = serializers.JSONField(required=False)

    class Meta:
        model = UserRoleModel
        fields = "__all__"

    def get_attached_policies(self, obj):
        policies = obj.policies.all()
        policy_serializer = PolicySerializer(policies, many=True, context=self.context)
        return policy_serializer.data

    def get_policies_count(self, obj):
        return {
            "policies": obj.policies.count(),
            "policy_groups": obj.policy_groups.count(),
            "total": obj.policies.count() + obj.policy_groups.count(),
        }

    def get_users_count(self, obj):
        return obj.users.filter(is_active=True).count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tenant = self.context.get("tenant")
        if tenant.auth_config.get("two_factor_auth", {}).get("required", False):
            if data["auth_config"].get("two_factor_auth"):
                data["auth_config"]["two_factor_auth"]["required"] = True
            else:
                data["auth_config"]["two_factor_auth"] = {"required": True}
        # Surface platform-default token TTL + idle timeout so the role override
        # UI can show the inherited value. Read-only, stripped on write.
        inject_platform_session_hints(data)
        return data

    def validate_auth_config(self, value: UserRoleAuthConfig):
        strip_platform_session_hints(value)
        validate_session_policy_token_ttl(value)
        validate_session_policy_timeout(value)

        tenant = self.context.get("tenant")
        if not tenant:
            return value

        tenant_auth_config = tenant.auth_config

        # Validate two_factor_auth config not overridden by role
        if tenant_auth_config.get("two_factor_auth", {}).get("required", False):
            if value.get("two_factor_auth", {}).get("required", False) is False:
                raise serializers.ValidationError(
                    "Two-factor authentication is required for this user role as it is enabled for the tenant."
                )

        if not sso_login_enabled(tenant.auth_config) and value.get(
            "enforce_sso", False
        ):
            raise serializers.ValidationError(
                "Cannot enforce SSO for this user role as neither SAML nor OpenID Connect sign-in is enabled for the tenant."
            )
        return value

    def validate(self, attrs):
        return attrs


class AppUserModelSerializerModel(
    serializers.ModelSerializer, UserAuthConfigValidationMixin
):
    roles = UserRoleSerializerModel(many=True)
    pn_country_code = serializers.SerializerMethodField()
    auth_config = serializers.JSONField(required=False)
    date_joined = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()

    class Meta:
        model = AppUserModel
        fields = "__all__"

    def get_date_joined(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.date_joined, self.context["tenant"]
        )

    def get_last_login(self, obj):
        if not obj.last_login:
            return None
        return get_datetime_str_in_tenant_timezone(
            obj.last_login, self.context["tenant"]
        )

    def get_roles(self, obj):
        roles_serializer = UserRoleSerializerModel(
            obj.roles.all(), many=True, context=self.context
        )
        return roles_serializer.data

    def get_pn_country_code(self, obj):
        if obj.mobile:
            return f"+{obj.mobile.country_code}"
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tenant = self.context.get("tenant")
        auth_config = get_auth_priority(tenant=tenant, user=instance)
        twofa_enabled = auth_config.get("two_factor_auth", {}).get("required", False)
        for role in instance.roles.all():
            role_twofa_config = get_auth_priority(
                tenant=tenant, user_role=role, policy="two_factor_auth"
            )
            if role_twofa_config.get("required", False):
                twofa_enabled = True
                break
        auth_config["two_factor_auth"]["required"] = twofa_enabled
        auth_config["sso_identities"] = get_sso_identities(instance, tenant)
        data["auth_config"] = auth_config
        return data

    def validate(self, attrs):
        auth_config = attrs.get("auth_config", {})
        if auth_config:
            # For partial updates, if roles are not in attrs, use the instance's roles
            roles = attrs.get("roles")
            if roles is None and self.instance:
                roles = self.instance.roles.all()
            self.validate_user_role_two_factor_not_overridden(
                auth_config, self.instance, roles
            )
        return attrs

    def validate_auth_config(self, value):
        return value


class ThemeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThemesModel
        fields = "__all__"

    def validate(self, data):
        instance = self.instance

        name = data.get("name")
        tenant = data.get("tenant")

        if name:
            # Check if an instance with the same 'name' and 'tenant' combination exists
            if instance is None:
                # For create operation
                if ThemesModel.objects.filter(name=name, tenant=tenant).exists():
                    raise serializers.ValidationError(
                        "Theme with this name already exists."
                    )
            else:
                # For update operation
                if (
                    ThemesModel.objects.exclude(pk=instance.pk)
                    .filter(name=name, tenant=tenant)
                    .exists()
                ):
                    raise serializers.ValidationError(
                        "Theme with this name already exists."
                    )

        return data

    def create(self, validated_data):
        config = json.loads(validated_data["config"])
        validated_data["config"] = config
        return super(ThemeModelSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("config"):
            statement = json.loads(validated_data["config"])
            validated_data["config"] = statement

        return super(ThemeModelSerializer, self).update(instance, validated_data)


class SAMLProviderModelSerializer(serializers.ModelSerializer):
    """
    Serializer for SAMLModel with comprehensive validation and configuration support.

    Validates SAML configuration including:
    - Entity IDs and URLs format
    - X509 certificate format
    - Security settings consistency
    - Required fields based on configuration
    """

    class Meta:
        model = SAMLModel
        fields = "__all__"


class OIDCProviderSerializer(serializers.ModelSerializer):
    """
    OIDC provider config for the App Panel. ``client_secret`` is write-only;
    omit it on update to keep the stored value. Saving fetches the discovery
    document and fails on ``issuer`` when it cannot be loaded or does not match.
    """

    RESERVED_AUTH_PARAMS = {
        "state",
        "nonce",
        "code_challenge",
        "code_challenge_method",
        "redirect_uri",
        "client_id",
        "response_type",
        "scope",
    }
    DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$")

    client_secret = serializers.CharField(
        write_only=True, required=False, allow_blank=True, trim_whitespace=False
    )
    has_client_secret = serializers.SerializerMethodField()
    client_secret_last4 = serializers.SerializerMethodField()
    callback_url = serializers.SerializerMethodField()
    callback_urls = serializers.SerializerMethodField()
    slug_locked = serializers.SerializerMethodField()
    linked_users = serializers.SerializerMethodField()
    last_login_at = serializers.SerializerMethodField()

    class Meta:
        model = OIDCProviderModel
        fields = [
            "id",
            "slug",
            "label",
            "icon",
            "issuer",
            "client_id",
            "client_secret",
            "has_client_secret",
            "client_secret_last4",
            "token_auth_method",
            "scopes",
            "extra_auth_params",
            "email_claim",
            "name_claim",
            "trust_email",
            "allowed_email_domains",
            "use_pkce",
            "fetch_userinfo",
            "rp_logout",
            "display_order",
            "is_active",
            "callback_url",
            "callback_urls",
            "slug_locked",
            "linked_users",
            "last_login_at",
            "discovery_fetched_at",
            "created_at",
            "modified_at",
        ]
        read_only_fields = ["discovery_fetched_at", "created_at", "modified_at"]

    def get_has_client_secret(self, obj):
        return bool(obj.client_secret)

    def get_client_secret_last4(self, obj):
        secret = obj.get_client_secret()
        return secret[-4:] if len(secret) >= 8 else None

    def _domains(self):
        tenant = self.context.get("tenant")
        if tenant is None:
            return []
        domains = list(tenant.domains.all().order_by("-is_primary", "id"))
        return [d.domain for d in domains]

    def _scheme(self):
        from django.conf import settings

        request = self.context.get("request")
        if settings.DEBUG and request is not None:
            return request.scheme
        return "https"

    def get_callback_urls(self, obj):
        scheme = self._scheme()
        return [f"{scheme}://{d}{obj.callback_path}" for d in self._domains()]

    def get_callback_url(self, obj):
        urls = self.get_callback_urls(obj)
        return urls[0] if urls else obj.callback_path

    def get_slug_locked(self, obj):
        return obj.pk is not None and obj.linked_identities().exists()

    def get_linked_users(self, obj):
        return obj.linked_identities().count()

    def get_last_login_at(self, obj):
        last = obj.linked_identities().order_by("-last_login").first()
        if last is None:
            return None
        tenant = self.context.get("tenant")
        if tenant is not None:
            return get_datetime_str_in_tenant_timezone(last.last_login, tenant)
        return last.last_login.isoformat()

    def validate_slug(self, value):
        if (
            self.instance
            and self.instance.slug != value
            and self.get_slug_locked(self.instance)
        ):
            raise serializers.ValidationError(
                "The slug cannot change while users are linked to this provider."
            )
        return value

    def validate_issuer(self, value):
        from django.conf import settings

        if not value.startswith("https://") and not settings.DEBUG:
            raise serializers.ValidationError("Issuer must be an https URL.")
        return value

    def validate_scopes(self, value):
        if not isinstance(value, list) or not all(
            isinstance(s, str) and s.strip() and " " not in s for s in value
        ):
            raise serializers.ValidationError("Scopes must be a list of words.")
        if "openid" not in value:
            raise serializers.ValidationError("Scopes must include 'openid'.")
        return list(dict.fromkeys(value))

    def validate_extra_auth_params(self, value):
        if not isinstance(value, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in value.items()
        ):
            raise serializers.ValidationError(
                "Extra parameters must be a flat map of strings."
            )
        reserved = sorted(set(value) & self.RESERVED_AUTH_PARAMS)
        if reserved:
            raise serializers.ValidationError(
                f"These parameters are set by Zango and cannot be overridden: {', '.join(reserved)}."
            )
        return value

    def validate_allowed_email_domains(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of domains.")
        cleaned = []
        for domain in value:
            domain = str(domain).strip().lower()
            if not self.DOMAIN_RE.match(domain):
                raise serializers.ValidationError(f"'{domain}' is not a valid domain.")
            cleaned.append(domain)
        return list(dict.fromkeys(cleaned))

    def validate(self, attrs):
        from django.utils import timezone

        from zango.apps.appauth.oidc.fetch import FetchError, fetch_discovery

        def current(field):
            if field in attrs:
                return attrs[field]
            if self.instance is not None:
                return getattr(self.instance, field)
            return None

        method = current("token_auth_method") or "client_secret_basic"
        use_pkce = current("use_pkce")
        if use_pkce is None:
            use_pkce = True
        if "client_secret" in attrs:
            has_secret = bool(attrs["client_secret"])
        else:
            has_secret = bool(self.instance and self.instance.client_secret)
        if method == "none":
            if not use_pkce:
                raise serializers.ValidationError(
                    {"use_pkce": ["Public clients (no secret) must use PKCE."]}
                )
        elif not has_secret:
            raise serializers.ValidationError(
                {"client_secret": ["A client secret is required for this method."]}
            )

        issuer = attrs.get("issuer")
        if issuer is not None and (
            self.instance is None
            or issuer != self.instance.issuer
            or not self.instance.discovery
        ):
            try:
                attrs["discovery"] = fetch_discovery(issuer)
            except FetchError as e:
                raise serializers.ValidationError({"issuer": [str(e)]}) from e
            attrs["discovery_fetched_at"] = timezone.now()
        return attrs

    def get_warnings(self, obj):
        warnings = []
        if obj.trust_email and not obj.allowed_email_domains:
            warnings.append(
                "Emails are trusted without verification and no domain allowlist is set."
            )
        supported = (obj.discovery or {}).get("code_challenge_methods_supported")
        if obj.use_pkce and supported is not None and "S256" not in supported:
            warnings.append("The provider does not advertise PKCE S256 support.")
        return warnings
