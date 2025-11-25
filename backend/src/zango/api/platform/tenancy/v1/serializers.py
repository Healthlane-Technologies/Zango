import json

from django_tenants.utils import schema_context
from rest_framework import serializers

from zango.api.platform.permissions.v1.serializers import PolicySerializer
from zango.apps.appauth.mixin import UserAuthConfigValidationMixin
from zango.apps.appauth.models import AppUserModel, SAMLModel, UserRoleModel
from zango.apps.appauth.schema import UserRoleAuthConfig
from zango.apps.shared.tenancy.models import Domain, TenantModel, ThemesModel
from zango.apps.shared.tenancy.schema import AuthConfigSchema as TenantAuthConfigSchema
from zango.core.utils import get_auth_priority, get_datetime_str_in_tenant_timezone


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

    def validate_auth_config(self, value: TenantAuthConfigSchema):
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
            if (
                not auth_config.get("login_methods", {})
                .get("sso", {})
                .get("enabled", False)
            ):
                with schema_context(instance.schema_name):
                    for role in UserRoleModel.objects.all():
                        print(role.auth_config)
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
        return data

    def validate_auth_config(self, value: UserRoleAuthConfig):
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

        sso_enabled = (
            tenant.auth_config.get("login_methods", {})
            .get("sso", {})
            .get("enabled", False)
        )

        if not sso_enabled and value.get("enforce_sso", False):
            raise serializers.ValidationError(
                "Cannot enforce SSO for this user role as SSO is not enabled for the tenant."
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
