from rest_framework import serializers
from .models import SkuModel, SkuTypes, OrderItemsModel


class SkuModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkuModel
        fields = '__all__'
    

    # def validate_program_name(self, value):
    #     if len(value) < 5:
    #         raise serializers.ValidationError("Program name is to short.")
    #     return value


class SkuTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkuTypes
        fields = '__all__'


class OrderItemsModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItemsModel
        fields = '__all__'