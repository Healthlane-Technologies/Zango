import json

from allauth.socialaccount.models import SocialApp
from rest_framework import serializers

from zango.api.platform.permissions.v1.serializers import PolicySerializer
from zango.apps.appauth.mixin import UserAuthConfigValidationMixin
from zango.apps.appauth.models import AppUserModel, UserRoleModel
from zango.apps.appauth.schema import UserRoleAuthConfig
from zango.apps.shared.tenancy.models import Domain, TenantModel, ThemesModel
from zango.apps.shared.tenancy.schema import AuthConfigSchema as TenantAuthConfigSchema
from zango.core.utils import get_auth_priority


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

        instance = super(TenantSerializerModel, self).update(instance, validated_data)
        request = self.context["request"]
        domains = request.data.getlist("domains")

        if not domains:
            return instance

        # Removing existing domains
        domains_to_be_removed = instance.domains.all().exclude(domain__in=domains)
        domains_to_be_removed.delete()

        # Creating new domains
        for domain in domains:
            domain_obj, created = Domain.objects.get_or_create(
                domain=domain, tenant=instance
            )
            if created:
                domain_obj.is_primary = False
                domain_obj.save()

        return instance


class UserRoleSerializerModel(serializers.ModelSerializer):
    attached_policies = serializers.SerializerMethodField()
    auth_config = serializers.JSONField(required=False)

    class Meta:
        model = UserRoleModel
        fields = "__all__"

    def get_attached_policies(self, obj):
        policies = obj.policies.all()
        policy_serializer = PolicySerializer(policies, many=True)
        return policy_serializer.data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tenant = self.context.get("tenant")
        data["auth_config"] = get_auth_priority(tenant=tenant, user_role=instance)
        return data

    def validate_auth_config(self, value: UserRoleAuthConfig):
        tenant = self.context.get("tenant")
        tenant_auth_config = tenant.auth_config

        # Validate two_factor_auth config not overridden by role
        if tenant_auth_config.get("two_factor_auth", {}).get("required", False):
            if value.get("two_factor_auth", {}).get("required", False) is False:
                raise serializers.ValidationError(
                    "Two-factor authentication is required for this user role as it is enabled for the tenant."
                )
        return value

    def validate(self, attrs):
        return attrs

    def update(self, instance, validated_data):
        if not validated_data.get("policies"):
            validated_data["policies"] = []
        return super(UserRoleSerializerModel, self).update(instance, validated_data)


class AppUserModelSerializerModel(
    serializers.ModelSerializer, UserAuthConfigValidationMixin
):
    roles = UserRoleSerializerModel(many=True)
    pn_country_code = serializers.SerializerMethodField()
    auth_config = serializers.JSONField(required=False)

    class Meta:
        model = AppUserModel
        fields = "__all__"

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


class SocialAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialApp
        fields = [
            "provider",
            "name",
            "client_id",
            "secret",
            "key",
            "settings",
            "enabled",
            "redirect_url",
        ]
