import json

from rest_framework import serializers
from zelthy.apps.shared.tenancy.models import TenantModel, Domain
from zelthy.apps.permissions.models import PolicyModel


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyModel
        fields = "__all__"

    def create(self, validated_data):
        statement = json.loads(validated_data["statement"])
        validated_data["statement"] = statement
        validated_data["is_active"] = True

        return super(PolicySerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if instance.type == "system":
            raise serializers.ValidationError
        if validated_data.get("statement"):
            statement = json.loads(validated_data["statement"])
            validated_data["statement"] = statement

        return super(PolicySerializer, self).update(instance, validated_data)
