from rest_framework import serializers
from .models import SupplyChainNodes


class SupplyChainNodesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplyChainNodes
        fields = '__all__'