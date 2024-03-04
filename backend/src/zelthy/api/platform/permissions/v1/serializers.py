import json

from rest_framework import serializers
from zelthy.apps.shared.tenancy.models import TenantModel, Domain
from zelthy.apps.permissions.models import PolicyModel
from zelthy.apps.appauth.models import UserRoleModel


class PolicySerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = PolicyModel
        fields = ["id", "name", "statement", "roles", "description", "type"]

    def get_roles(self, obj):
        return list(UserRoleModel.objects.filter(policies=obj).values("id", "name"))

    def create(self, validated_data):
        statement = json.loads(validated_data["statement"])
        validated_data["statement"] = statement
        validated_data["is_active"] = True

        return super(PolicySerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if instance.type == "system":
            # For System Policy Only role can be updated
            updated_allowed_fields = ["roles"]
            fields_list = list(validated_data.keys())
            for field in fields_list:
                if field not in updated_allowed_fields:
                    validated_data.pop(field)

        if validated_data.get("statement"):
            statement = json.loads(validated_data["statement"])
            validated_data["statement"] = statement
        existing_roles = list(
            UserRoleModel.objects.filter(policies=instance).values_list("id", flat=True)
        )
        roles = validated_data.pop("roles", [])
        for role in existing_roles:
            if role not in roles:
                role_obj = UserRoleModel.objects.get(id=role)
                role_obj.policies.remove(instance.id)

        for role in roles:
            role_obj = UserRoleModel.objects.get(id=role)
            role_obj.policies.add(instance.id)

        return super(PolicySerializer, self).update(instance, validated_data)
