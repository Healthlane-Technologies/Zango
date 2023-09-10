import json

from rest_framework import serializers
from zelthy.apps.shared.tenancy.models import TenantModel, Domain, ThemesModel
from zelthy.apps.appauth.models import UserRoleModel, AppUserModel


class DomainSerializerModel(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["domain", "is_primary"]


class TenantSerializerModel(serializers.ModelSerializer):
    domains = DomainSerializerModel(many=True, required=False)

    class Meta:
        model = TenantModel
        read_only_fields = ("name", "schema_name")
        fields = "__all__"

    def update(self, instance, validated_data):
        instance = super(TenantSerializerModel, self).update(instance, validated_data)
        request = self.context["request"]
        domains = request.data.getlist("domains")

        # Removing existing domains
        domains_to_be_removed = instance.domains.all().exclude(domain__in=domains)
        domains_to_be_removed.delete()

        # Creating new domains
        # TODO: Validare is_primary
        for domain in domains:
            domain_obj, created = Domain.objects.get_or_create(
                domain=domain, tenant=instance
            )
            if created:
                domain_obj.is_primary = False
                domain_obj.save()

        return instance


class UserRoleSerializerModel(serializers.ModelSerializer):
    class Meta:
        model = UserRoleModel
        fields = [
            "id",
            "name",
            "is_active",
            "is_default",
            "no_of_users",
            "policies",
            "policy_groups",
            "created_at",
            "created_by",
            "modified_at",
            "modified_by",
        ]

    def update(self, instance, validated_data):
        if not validated_data.get("policies"):
            validated_data["policies"] = []
        return super(UserRoleSerializerModel, self).update(instance, validated_data)


class AppUserModelSerializerModel(serializers.ModelSerializer):
    roles = UserRoleSerializerModel(many=True)

    class Meta:
        model = AppUserModel
        fields = [
            "id",
            "name",
            "email",
            "mobile",
            "roles",
            "is_active",
            "last_login",
            "created_at",
        ]


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